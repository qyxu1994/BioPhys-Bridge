"""License metadata normalization and checks."""

from __future__ import annotations

from biophysevo.schemas.case_schema import Case


_KNOWN_BAD = {"", "unknown", "none", "null"}
_LICENSE_ALIASES = {
    "cc by": "CC-BY-4.0",
    "cc-by": "CC-BY-4.0",
    "cc-by-4.0": "CC-BY-4.0",
    "cc by 4.0": "CC-BY-4.0",
    "cc_by_4.0": "CC-BY-4.0",
    "cc0": "CC0-1.0",
    "cc-0": "CC0-1.0",
    "cc0-1.0": "CC0-1.0",
    "cc0 1.0": "CC0-1.0",
}


def normalize_license(value: str | None) -> str:
    """Return canonical SPDX-ish strings for release-compatible data licenses."""
    raw = (value or "").strip()
    return _LICENSE_ALIASES.get(raw.lower(), raw)


def has_license(case: Case) -> bool:
    lic = normalize_license(case.source.license).lower()
    return lic not in _KNOWN_BAD
