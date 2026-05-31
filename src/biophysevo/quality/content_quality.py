"""Semantic content-quality gates for releasable Biophys-Bridge cases.

These checks intentionally sit above JSON Schema validation. They catch
release-polish failures that are syntactically valid JSON but unsuitable for a
contest-facing dataset: unresolved template markers, malformed task vocabularies,
empty task prompts, and incomplete Sci-Evo trajectories.
"""

from __future__ import annotations

import re
from typing import Any

from biophysevo.schemas.case_schema import Case


TEMPLATE_MARKERS = (
    "[template - needs expert review]",
    "expert review pending",
)

_EVIDENCE_LIST_RE = re.compile(
    r"^\s*\[\s*(['\"]ev_[^'\"]+['\"]\s*,?\s*)+\]\s*$"
)


def _as_dict(case: Case | dict[str, Any]) -> dict[str, Any]:
    if isinstance(case, Case):
        return case.model_dump(mode="json")
    return case


def _walk_strings(value: Any, path: str = "$") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            found.extend(_walk_strings(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            found.extend(_walk_strings(item, f"{path}[{i}]"))
    elif isinstance(value, str):
        found.append((path, value))
    return found


def _is_character_split_list(values: Any) -> bool:
    if not isinstance(values, list) or len(values) < 8:
        return False
    strings = [v for v in values if isinstance(v, str)]
    if len(strings) != len(values):
        return False
    return sum(len(v) <= 1 for v in strings) / len(strings) >= 0.8


def _vocabulary_issues(values: Any, path: str, *, require_nonempty: bool) -> list[str]:
    issues: list[str] = []
    if not isinstance(values, list):
        return [f"{path} must be a list"]
    if require_nonempty and not values:
        return [f"{path} must contain at least one entry"]
    if _is_character_split_list(values):
        issues.append(f"{path} appears to be a character-split string")
    for i, value in enumerate(values):
        item_path = f"{path}[{i}]"
        if not isinstance(value, str):
            issues.append(f"{item_path} must be a string")
            continue
        stripped = value.strip()
        if not stripped:
            issues.append(f"{item_path} is blank")
        elif len(stripped) <= 1:
            issues.append(f"{item_path} is too short to be a useful vocabulary item")
        elif len(stripped) > 100:
            issues.append(f"{item_path} is too long to be a controlled vocabulary item")
    return issues


def content_quality_issues(case: Case | dict[str, Any]) -> list[str]:
    """Return release-blocking semantic issues for a validated case."""

    record = _as_dict(case)
    issues: list[str] = []

    for path, text in _walk_strings(record):
        lowered = text.lower()
        for marker in TEMPLATE_MARKERS:
            if marker.lower() in lowered:
                issues.append(f"{path} contains unresolved template/review marker")
                break

    stages = {
        step.get("stage")
        for step in record.get("sci_evo_trajectory", [])
        if isinstance(step, dict)
    }
    if "next_step" not in stages:
        issues.append("sci_evo_trajectory is missing a next_step stage")

    tasks = record.get("agent_tasks") or []
    if not tasks:
        issues.append("agent_tasks must contain at least one task")
        return issues

    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            issues.append(f"agent_tasks[{i}] must be an object")
            continue
        prefix = f"agent_tasks[{i}]"
        task_input = str(task.get("input") or "").strip()
        gold_answer = str(task.get("gold_answer") or "").strip()
        if len(task_input) < 20:
            issues.append(f"{prefix}.input is empty or too weak")
        if _EVIDENCE_LIST_RE.match(task_input):
            issues.append(f"{prefix}.input is only an evidence-id list, not a task prompt")
        if len(gold_answer) < 30:
            issues.append(f"{prefix}.gold_answer is empty or too weak")
        issues.extend(
            _vocabulary_issues(
                task.get("required_reasoning_skills"),
                f"{prefix}.required_reasoning_skills",
                require_nonempty=True,
            )
        )
        issues.extend(
            _vocabulary_issues(
                task.get("allowed_tools", []),
                f"{prefix}.allowed_tools",
                require_nonempty=False,
            )
        )

    return issues


def passes_content_quality(case: Case | dict[str, Any]) -> bool:
    """Convenience predicate for release filtering."""

    return not content_quality_issues(case)
