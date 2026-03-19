"""T1: PythonExecute — Run Python code in a sandbox.

Supports three modes:
  1. OpenSandbox (self-hosted) — default
  2. E2B (cloud) — alternative
  3. Local subprocess with persistent namespace — fallback for development

PRD §2.7: Input: `code: str` → Output: `stdout + stderr + figures`

Persistent namespace:
  In local mode, each project session shares a Python namespace so that
  variables (DataFrames, models, etc.) survive across tool calls within a
  single agent session. The namespace is keyed by project_id from the
  ContextVar and is reset when a new project is selected.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import os
import resource
import sys
import tempfile
from typing import Any

from loguru import logger

from app.config import config

# ---------------------------------------------------------------------------
# Persistent local namespaces (project_id → dict)
# ---------------------------------------------------------------------------
_local_namespaces: dict[str, dict[str, Any]] = {}


def _get_namespace(project_id: str) -> dict[str, Any]:
    """Return (creating if needed) the persistent namespace for a project."""
    if project_id not in _local_namespaces:
        _local_namespaces[project_id] = {"__builtins__": __builtins__}
    return _local_namespaces[project_id]


def reset_namespace(project_id: str) -> None:
    """Clear the persistent namespace for a project (call on new session)."""
    _local_namespaces.pop(project_id, None)



async def python_execute(
    code: str,
    timeout: int = 30,
) -> str:
    """Execute Python code in a sandboxed environment.

    Runs the given Python code safely and returns the output.
    Used for data analysis, model building, visualization, and
    numerical computation in math modeling tasks.

    In local mode the execution shares a **persistent namespace** across
    calls within the same project session, so variables set in one call
    (e.g. a DataFrame) are available in subsequent calls.

    Supported libraries: numpy, scipy, pandas, matplotlib,
    scikit-learn, networkx, sympy, pytorch.

    Args:
        code: The Python source code to execute.
        timeout: Maximum execution time in seconds (default: 30).

    Returns:
        A string containing stdout, stderr, and any generated figure paths.
    """
    provider = config.sandbox.provider

    if provider == "opensandbox":
        return await _execute_opensandbox(code, timeout)
    elif provider == "e2b" and config.sandbox.e2b_api_key:
        return await _execute_e2b(code, timeout)
    else:
        return await _execute_local_persistent(code, timeout)


async def _execute_opensandbox(code: str, timeout: int) -> str:
    """Execute code using OpenSandbox self-hosted sandbox.

    Uses opensandbox 0.1.5 + opensandbox-code-interpreter 0.1.1 APIs:
    - Sandbox.create() — async, returns running sandbox container
    - CodeInterpreter.create(sandbox) — async factory method
    - interpreter.codes.run(code, language=...) — async execution
    - ExecutionLogs.stdout/stderr are list[OutputMessage] with .text attr
    - Execution.result is list[ExecutionResult] with .text attr
    """
    try:
        from datetime import timedelta

        from opensandbox import ConnectionConfig, Sandbox
        from code_interpreter import CodeInterpreter, SupportedLanguage

        cfg = ConnectionConfig(
            domain=config.sandbox.opensandbox_domain,
            api_key=config.sandbox.opensandbox_api_key,
            protocol="http",
        )

        sandbox = await Sandbox.create(
            image=config.sandbox.opensandbox_image,
            connection_config=cfg,
            timeout=timedelta(seconds=max(timeout * 3, 300)),
        )
        try:
            # CodeInterpreter.create() is an async factory method
            interpreter = await CodeInterpreter.create(sandbox)
            result = await interpreter.codes.run(code, language=SupportedLanguage.PYTHON)

            parts = []
            # logs.stdout / logs.stderr are list[OutputMessage]; each has .text
            if result.logs.stdout:
                parts.append(f"[stdout]\n{''.join(m.text for m in result.logs.stdout)}")
            if result.logs.stderr:
                parts.append(f"[stderr]\n{''.join(m.text for m in result.logs.stderr)}")
            if result.error:
                parts.append(f"[error]\n{result.error.name}: {result.error.value}")
            # result.result is list[ExecutionResult]; each has .text
            for i, r in enumerate(result.result):
                if r.text:
                    parts.append(f"[result_{i}]\n{r.text}")

            return "\n\n".join(parts) if parts else "Code executed successfully (no output)"
        finally:
            await sandbox.kill()

    except ImportError:
        logger.warning("opensandbox packages not installed, falling back to local execution")
        return await _execute_local(code, timeout)
    except Exception as e:
        logger.error(f"OpenSandbox execution error: {e}")
        return f"[error] OpenSandbox error: {e}"


async def _execute_e2b(code: str, timeout: int) -> str:
    """Execute code using E2B cloud sandbox.

    Uses e2b-code-interpreter 2.4.1 API:
    - Sandbox (not CodeInterpreter) from e2b_code_interpreter
    - Sandbox.create() and run_code() are synchronous — run in executor
    - Execution.logs.stdout / .stderr are List[str]
    - Execution.results is List[Result]; each has .text / .png
    - Use sandbox.kill() (not .close()) for cleanup
    """
    try:
        from e2b_code_interpreter import Sandbox

        def _run_sync() -> str:
            sandbox = Sandbox.create(
                timeout=timeout,
                api_key=config.sandbox.e2b_api_key,
            )
            try:
                execution = sandbox.run_code(code)

                parts = []
                if execution.logs.stdout:
                    parts.append(f"[stdout]\n{''.join(execution.logs.stdout)}")
                if execution.logs.stderr:
                    parts.append(f"[stderr]\n{''.join(execution.logs.stderr)}")
                if execution.error:
                    parts.append(f"[error]\n{execution.error.name}: {execution.error.value}")
                if execution.results:
                    for i, result in enumerate(execution.results):
                        if hasattr(result, "png") and result.png:
                            parts.append(f"[figure_{i}] PNG image generated")
                        elif hasattr(result, "text") and result.text:
                            parts.append(f"[result_{i}]\n{result.text}")

                return "\n\n".join(parts) if parts else "Code executed successfully (no output)"
            finally:
                try:
                    sandbox.kill()
                except Exception:
                    pass

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run_sync)

    except ImportError:
        logger.warning("e2b_code_interpreter not available, falling back to local")
        return await _execute_local(code, timeout)
    except Exception as e:
        logger.error(f"E2B execution error: {e}")
        return f"[error] E2B sandbox error: {e}"


async def _execute_local(code: str, timeout: int) -> str:
    """Execute code locally via subprocess (development fallback).

    Applies basic resource limits: 512 MB RAM, no new processes beyond the
    interpreter itself (via RLIMIT_NPROC on Linux/macOS).
    """
    workspace = config.workspace_root
    os.makedirs(workspace, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        dir=workspace,
        delete=False,
    ) as f:
        f.write(code)
        script_path = f.name

    def _set_limits():
        mem = 512 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        except (AttributeError, ValueError):
            pass

    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace,
            preexec_fn=_set_limits,
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )

        parts = []
        if stdout:
            parts.append(f"[stdout]\n{stdout.decode('utf-8', errors='replace')}")
        if stderr:
            parts.append(f"[stderr]\n{stderr.decode('utf-8', errors='replace')}")
        if proc.returncode != 0:
            parts.append(f"[exit_code] {proc.returncode}")

        return "\n\n".join(parts) if parts else "Code executed successfully (no output)"

    except asyncio.TimeoutError:
        return f"[error] Execution timed out after {timeout} seconds"
    except Exception as e:
        return f"[error] Local execution error: {e}"
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


async def _execute_local_persistent(code: str, timeout: int) -> str:
    """Execute code in a persistent in-process namespace (dev mode).

    Variables defined in one call persist across subsequent calls within
    the same project session. The namespace is isolated per project_id.
    """
    try:
        from app.context import project_id_var
        project_id = str(project_id_var.get() or "default")
    except Exception:
        project_id = "default"

    namespace = _get_namespace(project_id)

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    def _run():
        with contextlib.redirect_stdout(stdout_buf), \
             contextlib.redirect_stderr(stderr_buf):
            try:
                exec(compile(code, "<sandbox>", "exec"), namespace)  # noqa: S102
            except Exception as exc:
                print(f"{type(exc).__name__}: {exc}", file=sys.stderr)

    loop = asyncio.get_running_loop()
    try:
        await asyncio.wait_for(
            loop.run_in_executor(None, _run),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        return f"[error] Execution timed out after {timeout} seconds"
    except Exception as e:
        return f"[error] Persistent sandbox error: {e}"

    parts = []
    out = stdout_buf.getvalue()
    err = stderr_buf.getvalue()
    if out:
        parts.append(f"[stdout]\n{out}")
    if err:
        parts.append(f"[stderr]\n{err}")

    # Report variables that changed (new names added this call)
    new_vars = [
        k for k in namespace
        if not k.startswith("_") and k != "__builtins__"
    ]
    if new_vars:
        parts.append(f"[namespace] {len(new_vars)} vars: {', '.join(new_vars[:10])}")

    return "\n\n".join(parts) if parts else "Code executed successfully (no output)"
