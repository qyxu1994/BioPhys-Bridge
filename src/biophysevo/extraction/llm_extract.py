"""Optional LLM-based structuring of evidence blocks.

Disabled by default (regex-first per plan-v1 section 10). Callers must pass
``enabled=True`` and the function is a thin shim around an OpenAI-compatible
chat API. Returns ``None`` if the LLM is disabled or unavailable.

The prompt enforces the evidence-only contract from plan-v1 Stage 5:
"Only use the provided evidence blocks. If evidence is missing, return null."
"""

from __future__ import annotations

import json
import os
from typing import Any


EVIDENCE_ONLY_SYSTEM = (
    "You are structuring evidence from a scientific paper. Only use the "
    "provided evidence blocks. Do not invent experimental results. If the "
    "evidence does not support a field, return null. Every claim must cite "
    "evidence_id."
)


def structure_with_llm(
    evidence_blocks: list[dict],
    question: str,
    *,
    enabled: bool = False,
    provider: str = "openai",
    model: str = "gpt-4o-mini",
) -> dict[str, Any] | None:
    """Return a structured dict or ``None`` if disabled / unavailable."""
    if not enabled:
        return None
    if provider != "openai":
        return None
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI(api_key=api_key)
    user = json.dumps(
        {"evidence_blocks": evidence_blocks, "question": question},
        ensure_ascii=False,
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": EVIDENCE_ONLY_SYSTEM},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None
