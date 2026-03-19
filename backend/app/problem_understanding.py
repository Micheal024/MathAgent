"""ProblemUnderstanding — Structured analysis of competition math problems.

Runs once at the start of each project execution.
Extracts problem type, decision variables, constraints, and candidate tools.
Emits a `problem_understanding` WS event so the frontend can render the panel.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from loguru import logger


@dataclass
class ProblemUnderstanding:
    """Structured understanding extracted from a math modeling problem."""

    type: str = "优化问题"          # 优化问题 | 预测问题 | 模拟问题 | 评价问题
    variables: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    confidence: float = 0.5
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "variables": self.variables,
            "constraints": self.constraints,
            "tools": self.tools,
            "confidence": round(self.confidence, 2),
            "summary": self.summary,
        }

    def to_context_str(self) -> str:
        """Compact string for injection into phase planning prompts."""
        lines = [
            f"问题类型: {self.type}",
            f"决策变量: {', '.join(self.variables) or '待确认'}",
            f"约束条件: {', '.join(self.constraints) or '待确认'}",
            f"候选数学工具: {', '.join(self.tools) or '待选择'}",
        ]
        if self.summary:
            lines.append(f"核心摘要: {self.summary}")
        return "\n".join(lines)


_ANALYSIS_PROMPT = """\
你是数学建模竞赛专家。请深入分析以下竞赛题目，提取结构化信息。

## 题目内容
{problem_text}

## 任务
请以 JSON 格式返回，字段说明如下：
{{
  "type": "优化问题" 或 "预测问题" 或 "模拟问题" 或 "评价问题",
  "variables": ["变量1简短描述", "变量2简短描述", ...],
  "constraints": ["约束1", "约束2", ...],
  "tools": ["线性规划"|"整数规划"|"非线性规划"|"微分方程"|"蒙特卡洛"|"神经网络"|"灰色预测"|"层次分析法"|"模糊评价"|"图论"|"统计回归"|"动态规划"|"博弈论"|"元启发算法"|...],
  "confidence": 置信度0.0~1.0（反映你对分析结果的把握程度）,
  "summary": "一句话概括题目核心目标（15字以内）"
}}

只返回 JSON，不要其他任何文字。\
"""


async def analyze_problem(
    problem_text: str,
    agent: ChatAgent,
    on_emit: Optional[Callable] = None,
) -> ProblemUnderstanding:
    """Analyze a competition problem and return structured understanding.

    Args:
        problem_text: Raw competition problem statement.
        agent: ChatAgent to use for LLM analysis.
        on_emit: Async callback(event_type: str, content: str) for WS events.

    Returns:
        ProblemUnderstanding with extracted fields.
    """
    prompt = BaseMessage.make_user_message(
        role_name="User",
        content=_ANALYSIS_PROMPT.format(problem_text=problem_text[:3000]),
    )

    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, lambda: agent.step(prompt)
        )
        raw = response.msgs[0].content if response.msgs else ""
    except Exception as e:
        logger.warning(f"[ProblemUnderstanding] LLM call failed: {e}")
        raw = ""

    pu = _parse_response(raw)

    logger.info(
        f"[ProblemUnderstanding] type={pu.type} "
        f"vars={len(pu.variables)} conf={pu.confidence:.2f}"
    )

    if on_emit:
        try:
            await on_emit(
                "problem_understanding",
                json.dumps(pu.to_dict(), ensure_ascii=False),
            )
        except Exception as e:
            logger.warning(f"[ProblemUnderstanding] emit failed: {e}")

    return pu


def _parse_response(raw: str) -> ProblemUnderstanding:
    """Parse LLM JSON response into a ProblemUnderstanding."""
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return ProblemUnderstanding(confidence=0.3)
    try:
        data = json.loads(m.group())
        return ProblemUnderstanding(
            type=data.get("type", "优化问题"),
            variables=list(data.get("variables", []))[:8],
            constraints=list(data.get("constraints", []))[:8],
            tools=list(data.get("tools", []))[:6],
            confidence=float(data.get("confidence", 0.5)),
            summary=str(data.get("summary", "")),
        )
    except Exception as e:
        logger.warning(f"[ProblemUnderstanding] JSON parse failed: {e}")
        return ProblemUnderstanding(confidence=0.3)
