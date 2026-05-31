"""Normalize MinerU outputs into the canonical parsed_docs layout.

Target:
    data/intermediate/parsed_docs/<doc_id>/
        document.md
        document.json
        tables.jsonl
        formulas.jsonl
        figures.jsonl
        evidence_blocks.jsonl
        parse_metadata.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from biophysevo.utils.io import atomic_write_jsonl


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_mineru_payload(
    doc_id: str,
    payload: dict[str, Any],
    out_root: str | Path,
    *,
    parse_metadata: dict[str, Any] | None = None,
    include_text_blocks: bool = False,
) -> Path:
    """Write the canonical layout. Returns the per-document folder.

    When ``include_text_blocks`` is True, numeric-bearing prose paragraphs from
    the markdown body are emitted as ``text`` evidence blocks (``ev_pNNNN``) so
    quantitative values stated in prose can be grounded to an evidence_id.
    """
    out_dir = Path(out_root) / doc_id
    out_dir.mkdir(parents=True, exist_ok=True)

    _atomic_write_text(out_dir / "document.md", payload.get("markdown", "") or "")
    _atomic_write_text(
        out_dir / "document.json",
        json.dumps(payload.get("json", {}) or {}, indent=2, sort_keys=True),
    )

    atomic_write_jsonl(out_dir / "tables.jsonl", payload.get("tables", []) or [])
    atomic_write_jsonl(out_dir / "formulas.jsonl", payload.get("formulas", []) or [])
    atomic_write_jsonl(out_dir / "figures.jsonl", payload.get("figures", []) or [])

    evidence_blocks = _build_evidence_blocks(
        payload, include_text=include_text_blocks
    )
    atomic_write_jsonl(out_dir / "evidence_blocks.jsonl", evidence_blocks)

    meta = dict(parse_metadata or {})
    meta.setdefault("doc_id", doc_id)
    meta.setdefault("tables", len(payload.get("tables", []) or []))
    meta.setdefault("formulas", len(payload.get("formulas", []) or []))
    meta.setdefault("figures", len(payload.get("figures", []) or []))
    meta.setdefault("evidence_blocks", len(evidence_blocks))
    _atomic_write_text(
        out_dir / "parse_metadata.json",
        json.dumps(meta, indent=2, sort_keys=True),
    )
    return out_dir


_DIGIT_RE = re.compile(r"\d")


def _text_evidence_blocks(markdown: str, *, max_chars: int = 2000) -> list[dict]:
    """Numeric-bearing prose paragraphs as ``text`` evidence blocks.

    Paragraphs (split on blank lines) are kept only if they contain a digit, so
    measurement-bearing prose is captured while non-numeric narrative (and the
    token cost of sending it to an LLM) is skipped.
    """
    blocks: list[dict] = []
    pidx = 0
    for para in re.split(r"\n\s*\n", markdown or ""):
        text = para.strip()
        if not text or not _DIGIT_RE.search(text):
            continue
        pidx += 1
        blocks.append(
            {
                "evidence_id": f"ev_p{pidx:04d}",
                "modality": "text",
                "text": text[:max_chars],
                "source_location": {},
            }
        )
    return blocks


def _build_evidence_blocks(
    payload: dict[str, Any], *, include_text: bool = False
) -> list[dict]:
    """Flatten tables/formulas/figures into evidence blocks with stable IDs.

    Each block:
        {"evidence_id": "...", "modality": "table|formula|figure|text",
         "text": "...", "source_location": {...}}

    When ``include_text`` is True, numeric-bearing prose paragraphs are appended
    as ``text`` blocks (``ev_pNNNN``).
    """
    blocks: list[dict] = []
    idx = 0
    for table in payload.get("tables", []) or []:
        idx += 1
        blocks.append(
            {
                "evidence_id": f"ev_t{idx:04d}",
                "modality": "table",
                "text": table.get("text") or table.get("caption") or "",
                "source_location": {
                    "page": table.get("page"),
                    "table_id": table.get("id"),
                    "section": table.get("section"),
                },
            }
        )
    fidx = 0
    for formula in payload.get("formulas", []) or []:
        fidx += 1
        blocks.append(
            {
                "evidence_id": f"ev_f{fidx:04d}",
                "modality": "formula",
                "text": formula.get("latex") or formula.get("text") or "",
                "source_location": {
                    "page": formula.get("page"),
                    "section": formula.get("section"),
                },
            }
        )
    gidx = 0
    for figure in payload.get("figures", []) or []:
        gidx += 1
        blocks.append(
            {
                "evidence_id": f"ev_g{gidx:04d}",
                "modality": "figure",
                "text": figure.get("caption") or "",
                "source_location": {
                    "page": figure.get("page"),
                    "figure_id": figure.get("id"),
                    "section": figure.get("section"),
                },
            }
        )
    if include_text:
        blocks.extend(_text_evidence_blocks(payload.get("markdown", "") or ""))
    return blocks


def _join_caption(value: Any) -> str:
    """MinerU captions are lists of strings; join into one string."""
    if isinstance(value, list):
        return " ".join(str(v) for v in value if v)
    return str(value) if value else ""


def mineru_content_list_to_payload(
    content_list: list[dict], *, markdown: str = ""
) -> dict[str, Any]:
    """Adapt a real MinerU ``*_content_list.json`` array into the payload shape
    that :func:`normalize_mineru_payload` expects.

    MinerU 2.x emits a flat, page-ordered list of blocks keyed by ``type``:
    ``text``/``title`` (free text, flows through ``document.md`` only),
    ``table`` (``table_body`` HTML + ``table_caption`` list), ``equation``
    (LaTeX in ``text`` wrapped in ``$$``), and ``image`` (``img_caption`` list).
    ``page_idx`` is 0-based; we expose 1-based ``page``. ``section`` is left
    ``None`` (content_list carries no reliable per-block section).
    """
    tables: list[dict] = []
    formulas: list[dict] = []
    figures: list[dict] = []

    n_tab = n_fig = 0
    for block in content_list:
        btype = block.get("type")
        page_idx = block.get("page_idx")
        page = page_idx + 1 if isinstance(page_idx, int) else None

        if btype == "table":
            n_tab += 1
            tables.append(
                {
                    "id": f"Table {n_tab}",
                    "page": page,
                    "section": None,
                    "text": block.get("table_body") or "",
                    "caption": _join_caption(block.get("table_caption")),
                }
            )
        elif btype == "equation":
            latex = (block.get("text") or "").strip().strip("$").strip()
            formulas.append({"page": page, "section": None, "latex": latex})
        elif btype == "image":
            n_fig += 1
            figures.append(
                {
                    "id": f"Figure {n_fig}",
                    "page": page,
                    "section": None,
                    "caption": _join_caption(block.get("img_caption")),
                }
            )

    return {
        "markdown": markdown or "",
        "json": {"content_list": content_list},
        "tables": tables,
        "formulas": formulas,
        "figures": figures,
        "metadata": {"source": "mineru_content_list"},
    }


def dry_run_payload(doc_id: str) -> dict[str, Any]:
    """Return a deterministic stub payload for ``--dry-run`` mode."""
    return {
        "markdown": f"# Dry-run document {doc_id}\n\nKd = 120 nM at pH 7.4.\n",
        "json": {"doc_id": doc_id, "stub": True},
        "tables": [
            {
                "id": "Table 1",
                "page": 1,
                "section": "Results",
                "text": "Kd = 120 nM at pH 7.4, 298 K (ITC).",
                "caption": "Binding affinities",
            }
        ],
        "formulas": [
            {
                "page": 1,
                "section": "Methods",
                "latex": r"\Delta G = R T \ln K_d",
            }
        ],
        "figures": [
            {
                "id": "Figure 1",
                "page": 2,
                "section": "Results",
                "caption": "ITC isotherm for kinase + inhibitor.",
            }
        ],
        "metadata": {"dry_run": True},
    }
