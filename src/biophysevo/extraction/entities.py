"""Regex extractors for entities (UniProt, PDB, EC numbers, mutations)."""

from __future__ import annotations

import re
from typing import Iterable

UNIPROT_RE = re.compile(
    r"\b[OPQ][0-9][A-Z0-9]{3}[0-9]\b|\b[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2}\b"
)

PDB_RE = re.compile(r"\b[1-9][A-Z0-9]{3}\b")

EC_RE = re.compile(r"\bEC\s?(\d+\.\d+\.\d+\.\d+)\b", re.IGNORECASE)

MUTATION_RE = re.compile(r"\b[ARNDCEQGHILKMFPSTWYV]\d{1,4}[ARNDCEQGHILKMFPSTWYV]\b")


def find_uniprot_ids(text: str) -> list[str]:
    return list(dict.fromkeys(UNIPROT_RE.findall(text)))


def find_pdb_ids(text: str) -> list[str]:
    """Return PDB-like 4-char codes (digit + 3 alphanumerics, e.g. 1ABC, 7BRO)."""
    return list(dict.fromkeys(PDB_RE.findall(text)))


def find_ec_numbers(text: str) -> list[str]:
    return list(dict.fromkeys(EC_RE.findall(text)))


def find_mutations(text: str) -> list[str]:
    return list(dict.fromkeys(MUTATION_RE.findall(text)))


def extract_entities(text: str) -> dict[str, list[str]]:
    return {
        "uniprot_ids": find_uniprot_ids(text),
        "pdb_ids": find_pdb_ids(text),
        "ec_numbers": find_ec_numbers(text),
        "mutations": find_mutations(text),
    }
