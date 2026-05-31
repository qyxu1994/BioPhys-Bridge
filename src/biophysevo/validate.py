"""CLI: validate a JSONL of Biophys-Bridge Sci-Evo cases against the schema.

    python -m biophysevo.validate --input data/samples/sample_cases.jsonl
    biophysevo-validate --input data/samples/sample_cases.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from biophysevo.schemas.case_schema import validate_cases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Biophys-Bridge Sci-Evo cases.")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2

    raw: list[dict] = []
    with args.input.open() as fh:
        for i, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"line {i}: invalid JSON: {exc}", file=sys.stderr)
                return 2

    try:
        cases = validate_cases(raw)
    except (ValidationError, ValueError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"ok: {len(cases)} case(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
