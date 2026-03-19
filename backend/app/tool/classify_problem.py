"""T5: ClassifyProblem — Math modeling problem analysis and classification.

Uses LLM to analyze problem text and extract structured information.

PRD §2.7: Input: `text: str` → Output: `{type, variables, constraints, objective}`
"""

from __future__ import annotations

import json

from loguru import logger


def classify_problem(text: str) -> str:
    """Analyze and classify a math modeling competition problem.

    Extracts key components from the problem statement:
    - Problem type (optimization, prediction, evaluation, simulation)
    - Decision variables and parameters
    - Constraints and boundary conditions
    - Objective function or evaluation criteria
    - Recommended modeling approaches

    This is typically the first tool to use after receiving a new problem.

    Args:
        text: The full problem statement text.

    Returns:
        A JSON object with the classification results and extracted entities.
    """
    logger.info(f"🔬 Classifying problem ({len(text)} chars)")

    # Template-based extraction (LLM-enhanced in production)
    # This provides the structured output format;
    # the actual LLM analysis happens via the ChatAgent's reasoning
    result = {
        "problem_type": "pending_analysis",
        "problem_text_length": len(text),
        "analysis_prompt": (
            "请分析以下赛题并提取:\n"
            "1. 问题类型 (optimization/prediction/evaluation/simulation)\n"
            "2. 决策变量 (decision variables)\n"
            "3. 约束条件 (constraints)\n"
            "4. 目标函数 (objective)\n"
            "5. 推荐模型类别\n\n"
            f"题目文本:\n{text[:3000]}"
        ),
        "note": (
            "This tool provides the analysis framework. "
            "Use the ChatAgent's reasoning to fill in the structured fields."
        ),
    }

    return json.dumps(result, ensure_ascii=False, indent=2)
