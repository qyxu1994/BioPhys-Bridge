"""Shared test fixtures."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CASES = REPO_ROOT / "data" / "samples" / "sample_cases.jsonl"


@pytest.fixture
def sample_case_dict() -> dict:
    with SAMPLE_CASES.open() as fh:
        line = next(fh)
    return json.loads(line)


@pytest.fixture
def make_case(sample_case_dict):
    """Return a factory producing fresh deep copies of the sample case."""

    def _factory(**overrides):
        case = copy.deepcopy(sample_case_dict)
        case.update(overrides)
        return case

    return _factory
