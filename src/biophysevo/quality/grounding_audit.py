"""Programmatic grounding audit: gate cases for release.

Promotes ``manual_review_status`` from ``needs_fix`` -> ``reviewed`` ONLY when
every ``quantitative_evidence`` value can be matched (whitespace-robust) in the
text of the evidence block it cites. Failed cases stay ``needs_fix`` with a
per-case failure reason appended to ``quality.reviewer_notes``.

Conservative by design: this is the only programmatic gate that lets cases
reach a release, so a value the LLM invented (or mis-cited) blocks the case.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from biophysevo.utils.logging import get_logger
from biophysevo.utils.io import read_jsonl

LOG = get_logger("biophysevo.quality.grounding_audit")


_WS = re.compile(r"\s+")
_DIGITS = re.compile(r"[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?")
# scientific in prose: "10^6", "10^{6}", "1.5 × 10^4"
_POW10 = re.compile(r"(\d+\.?\d*)\s*[×x*]?\s*10\s*[\^]\s*\{?\s*([-+]?\d+)\s*\}?")
# superscript digits (Unicode) used in OCR output
_SUPER = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


def _strip_ws(s: str) -> str:
    """Collapse whitespace + commas (handles LaTeX '3 4 . 9' and '1,000,000')."""
    return _WS.sub("", (s or "").replace(",", ""))


def _candidate_numbers(text: str) -> list[float]:
    """Pull every plausible numeric value out of a haystack, incl. 10^N forms."""
    if not text:
        return []
    t = text.translate(_SUPER).replace(",", "")
    nums: list[float] = []
    for m in _DIGITS.findall(t):
        try:
            nums.append(float(m))
        except ValueError:
            continue
    for mantissa, exp in _POW10.findall(t):
        try:
            nums.append(float(mantissa) * (10 ** int(exp)))
        except ValueError:
            continue
    return nums


def _value_repr(v: float) -> list[str]:
    """Render a numeric value into the forms the LLM is likely to find verbatim."""
    out: list[str] = []
    if v == int(v):
        out.append(str(int(v)))
    s = f"{v}"
    if s not in out:
        out.append(s)
    # also a non-scientific representation for small/large numbers
    s2 = f"{v:.6f}".rstrip("0").rstrip(".")
    if s2 and s2 not in out:
        out.append(s2)
    return out


def _value_in_text(value: float, text: str) -> bool:
    haystack = _strip_ws(text)
    for rep in _value_repr(value):
        if _strip_ws(rep) in haystack:
            return True
    # numeric match against every plausible number in the text. Allow 1% relative
    # tolerance to absorb LLM precision normalization (233.17 ↔ 233.2) and unit
    # rounding, while still rejecting wholly fabricated values.
    target = float(value)
    if target == 0.0:
        return any(n == 0.0 for n in _candidate_numbers(text))
    for n in _candidate_numbers(text):
        if abs(n - target) / abs(target) < 0.01:
            return True
    return False


def audit_case(case: dict) -> tuple[bool, list[str]]:
    """Return (passes, reasons). passes=True ⇒ ok to promote to reviewed."""
    reasons: list[str] = []
    ev_by_id = {
        e.get("evidence_id"): e.get("text") or ""
        for e in (case.get("evidence") or [])
        if e.get("evidence_id")
    }
    qe = case.get("quantitative_evidence") or []
    if not qe:
        reasons.append("no quantitative_evidence")
        return False, reasons

    for q in qe:
        eid = q.get("evidence_id")
        if eid not in ev_by_id:
            reasons.append(f"qe cites missing evidence_id={eid}")
            continue
        v = q.get("value")
        if not isinstance(v, (int, float)):
            reasons.append(f"qe value not numeric (metric={q.get('metric')})")
            continue
        if not _value_in_text(float(v), ev_by_id[eid]):
            reasons.append(
                f"qe value={v} {q.get('unit')} not found in {eid} (metric={q.get('metric')})"
            )
    return (not reasons), reasons


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Grounding audit; promote passing cases to reviewed.")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument(
        "--keep-reviewed",
        action="store_true",
        default=True,
        help="If a case is already 'reviewed', do not re-audit (default).",
    )
    args = p.parse_args(argv)

    cases = list(read_jsonl(args.input))
    n_pass = 0
    n_fail = 0
    n_skip = 0
    for c in cases:
        q = c.setdefault("quality", {})
        if args.keep_reviewed and q.get("manual_review_status") == "reviewed":
            n_skip += 1
            continue
        ok, reasons = audit_case(c)
        if ok:
            q["manual_review_status"] = "reviewed"
            notes = q.get("reviewer_notes") or ""
            q["reviewer_notes"] = (notes + " " if notes else "") + "auto: grounding audit passed"
            n_pass += 1
        else:
            q["manual_review_status"] = "needs_fix"
            notes = q.get("reviewer_notes") or ""
            q["reviewer_notes"] = (notes + " " if notes else "") + "; ".join(reasons)
            n_fail += 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")

    LOG.info(
        "grounding audit: skipped(already reviewed)=%d auto-passed=%d failed=%d total=%d",
        n_skip, n_pass, n_fail, len(cases),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
