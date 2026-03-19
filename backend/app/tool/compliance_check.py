"""T8: ComplianceCheck — Math modeling paper compliance scanner.

Checks papers against competition formatting rules (MCM/ICM/CUMCM).

PRD §2.7: Input: `document, rules` → Output: `{passed: bool, violations[]}`
"""

from __future__ import annotations

import json
import os
import re

from loguru import logger

# Competition rule sets
_RULES = {
    "MCM": {
        "max_pages": 25,
        "required_sections": ["Summary", "Introduction", "Model", "Results", "Conclusion", "References"],
        "forbidden_words": [],
        "requires_ai_statement": True,
        "max_summary_words": 250,
    },
    "ICM": {
        "max_pages": 25,
        "required_sections": ["Summary", "Introduction", "Model", "Results", "Conclusion", "References"],
        "forbidden_words": [],
        "requires_ai_statement": True,
        "max_summary_words": 250,
    },
    "CUMCM": {
        "max_pages": 20,
        "required_sections": ["摘要", "问题重述", "模型建立", "模型求解", "结果分析", "参考文献"],
        "forbidden_words": ["学校", "姓名", "学号"],
        "requires_ai_statement": False,
        "max_summary_words": 400,
    },
    "APMCM": {
        "max_pages": 25,
        "required_sections": ["Summary", "Introduction", "Model", "Results", "Conclusion"],
        "forbidden_words": [],
        "requires_ai_statement": True,
        "max_summary_words": 300,
    },
}


def compliance_check(
    document_path: str,
    competition: str = "MCM",
) -> str:
    """Check a math modeling paper for competition compliance.

    Scans the document for formatting violations, forbidden words,
    required sections, and page limits based on competition rules.

    Args:
        document_path: Path to the document file (LaTeX or text).
        competition: Competition type ("MCM", "ICM", "CUMCM", "APMCM").

    Returns:
        A JSON report with pass/fail status and detailed violations.
    """
    logger.info(f"📋 Compliance check: {document_path} ({competition})")

    competition = competition.upper()
    if competition not in _RULES:
        return json.dumps({
            "passed": False,
            "error": f"Unknown competition: {competition}. Supported: {list(_RULES.keys())}",
        }, ensure_ascii=False)

    rules = _RULES[competition]

    # Read document
    from app.config import config
    full_path = os.path.join(config.workspace_root, document_path)

    if not os.path.exists(full_path):
        return json.dumps({
            "passed": False,
            "error": f"Document not found: {full_path}",
        }, ensure_ascii=False)

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    violations = []

    # Check forbidden words
    for word in rules["forbidden_words"]:
        if word in content:
            violations.append({
                "type": "forbidden_word",
                "severity": "critical",
                "detail": f"Forbidden word found: '{word}'",
            })

    # Check required sections
    for section in rules["required_sections"]:
        # Check both LaTeX section commands and plain text headers
        if (
            f"\\section{{{section}}}" not in content
            and f"\\section*{{{section}}}" not in content
            and section not in content
        ):
            violations.append({
                "type": "missing_section",
                "severity": "warning",
                "detail": f"Required section not found: '{section}'",
            })

    # Check AI statement requirement
    if rules["requires_ai_statement"]:
        ai_keywords = ["AI", "artificial intelligence", "ChatGPT", "LLM", "GPT", "machine learning tool"]
        has_ai_statement = any(kw.lower() in content.lower() for kw in ai_keywords)
        if not has_ai_statement:
            violations.append({
                "type": "missing_ai_statement",
                "severity": "warning",
                "detail": "AI usage statement may be missing (required by competition rules)",
            })

    # Estimate page count (rough: ~3000 chars per page for LaTeX)
    estimated_pages = len(content) / 3000
    if estimated_pages > rules["max_pages"]:
        violations.append({
            "type": "page_limit",
            "severity": "critical",
            "detail": f"Estimated {estimated_pages:.0f} pages exceeds limit of {rules['max_pages']}",
        })

    # Result
    passed = all(v["severity"] != "critical" for v in violations)

    report = {
        "passed": passed,
        "competition": competition,
        "estimated_pages": round(estimated_pages, 1),
        "max_pages": rules["max_pages"],
        "total_violations": len(violations),
        "critical_violations": sum(1 for v in violations if v["severity"] == "critical"),
        "violations": violations,
    }

    return json.dumps(report, ensure_ascii=False, indent=2)
