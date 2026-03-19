"""T7: LaTeXCompile — Compile LaTeX documents to PDF.

Compiles LaTeX source using xelatex in the sandbox.

PRD §2.7: Input: `tex_source: str` → Output: `pdf_url + compile_log`
"""

from __future__ import annotations

import os
import subprocess
import tempfile

from loguru import logger

from app.config import config


def latex_compile(
    tex_source: str,
    output_filename: str = "paper",
) -> str:
    """Compile LaTeX source code into a PDF document.

    Writes the LaTeX source to a .tex file and compiles it
    using xelatex. Returns the compilation log and path to
    the generated PDF.

    Args:
        tex_source: The complete LaTeX source code.
        output_filename: Base name for the output file (default: "paper").

    Returns:
        A string with the compilation result, including
        the PDF path on success or error details on failure.
    """
    workspace = config.workspace_root
    os.makedirs(workspace, exist_ok=True)

    tex_path = os.path.join(workspace, f"{output_filename}.tex")
    pdf_path = os.path.join(workspace, f"{output_filename}.pdf")

    # Write LaTeX source
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_source)

    logger.info(f"📄 Compiling LaTeX: {tex_path}")

    try:
        # Run xelatex twice (for references/table of contents)
        for pass_num in range(2):
            result = subprocess.run(
                [
                    "xelatex",
                    "-interaction=nonstopmode",
                    "-output-directory", workspace,
                    tex_path,
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=workspace,
            )

        # Check if PDF was generated
        if os.path.exists(pdf_path):
            # Extract key log info
            log_lines = result.stdout.split("\n") if result.stdout else []
            warnings = [l for l in log_lines if "Warning" in l][:5]
            errors = [l for l in log_lines if "Error" in l or "!" in l][:5]

            parts = [f"[success] PDF generated: {pdf_path}"]
            if warnings:
                parts.append(f"Warnings:\n" + "\n".join(warnings))
            if errors:
                parts.append(f"Non-fatal errors:\n" + "\n".join(errors))

            return "\n\n".join(parts)
        else:
            # Compilation failed
            stderr = result.stderr[:2000] if result.stderr else ""
            stdout_tail = "\n".join(
                (result.stdout or "").split("\n")[-20:]
            )
            return (
                f"[error] LaTeX compilation failed\n"
                f"[stderr]\n{stderr}\n"
                f"[log tail]\n{stdout_tail}"
            )

    except FileNotFoundError:
        return (
            "[error] xelatex not found. "
            "Install TeX Live: brew install --cask mactex (macOS) "
            "or apt install texlive-xetex (Ubuntu)"
        )
    except subprocess.TimeoutExpired:
        return "[error] LaTeX compilation timed out (>60s)"
    except Exception as e:
        return f"[error] Compilation error: {e}"
