"""Pull LaTeX / inline math blocks from MinerU normalized output."""

from __future__ import annotations

import re
from pathlib import Path

from biophysevo.utils.io import read_jsonl

_INLINE_RE = re.compile(r"\$(.+?)\$", re.DOTALL)
_BLOCK_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)


def extract_formulas_from_markdown(text: str) -> list[dict]:
    out: list[dict] = []
    for m in _BLOCK_RE.finditer(text):
        out.append({"latex": m.group(1).strip(), "kind": "block", "span": m.span()})
    for m in _INLINE_RE.finditer(text):
        out.append({"latex": m.group(1).strip(), "kind": "inline", "span": m.span()})
    return out


def load_formulas_from_parsed_doc(doc_dir: str | Path) -> list[dict]:
    doc_dir = Path(doc_dir)
    formulas = list(read_jsonl(doc_dir / "formulas.jsonl"))
    md = doc_dir / "document.md"
    if md.exists():
        formulas.extend(extract_formulas_from_markdown(md.read_text()))
    return formulas
