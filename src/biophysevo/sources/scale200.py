"""Scale-to-200 source scoring and manual MinerU parse handoff utilities.

This module deliberately stops before PDF parsing. MinerU parsing is launched
from generated handoff instructions; this code prepares deterministic batch
manifests and audits completed parse folders afterward.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import requests

from biophysevo.schemas.case_schema import (
    DOMAIN_DEFAULT_MODEL_FAMILY,
    MODEL_FAMILY_VALUES,
)
from biophysevo.utils.io import atomic_write_jsonl, read_jsonl
from biophysevo.utils.run_manager import timestamp


EUROPE_PMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
HTTP_HEADERS = {
    "User-Agent": (
        "Biophys-Bridge/0.1 "
        "(research data curation; contact: https://github.com/)"
    ),
    "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.1",
}


DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "protein_ligand_binding": (
        "binding affinity",
        "ligand",
        "Kd",
        "Ki",
        "IC50",
        "ITC",
        "SPR",
    ),
    "enzyme_kinetics": (
        "enzyme",
        "protease",
        "kinase",
        "catalysis",
        "catalytic",
        "enzyme kinetics",
        "kcat",
        "Km",
        "Michaelis-Menten",
        "catalytic efficiency",
    ),
    "protein_stability_thermodynamics": (
        "protein stability",
        "folding",
        "Tm",
        "ΔΔG",
        "ddG",
        "thermal stability",
    ),
    "conformational_dynamics_allostery": (
        "allostery",
        "conformational",
        "FRET",
        "HDX",
        "NMR relaxation",
    ),
    "biomolecular_phase_separation": (
        "phase separation",
        "LLPS",
        "condensate",
        "coacervation",
        "saturation concentration",
    ),
    "systems_biology_dynamics": (
        "bistability",
        "feedback",
        "ODE",
        "switch",
        "pathway dynamics",
        "gene regulatory",
    ),
}


MODEL_FAMILY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "binding_thermodynamics": ("Kd", "Ki", "binding free energy", "ITC", "SPR"),
    "enzyme_reaction_kinetics": (
        "enzyme",
        "protease",
        "kinase",
        "catalysis",
        "catalytic",
        "kcat",
        "Km",
        "Vmax",
        "Michaelis-Menten",
        "IC50",
    ),
    "folding_stability_thermodynamics": ("Tm", "ΔG", "ΔΔG", "folding stability"),
    "conformational_allostery_energy_landscape": (
        "allosteric",
        "conformational",
        "energy landscape",
        "Markov state",
    ),
    "polymer_phase_separation_statistical_mechanics": (
        "LLPS",
        "phase separation",
        "Flory",
        "polymer",
        "critical concentration",
    ),
    "systems_stochastic_dynamics": (
        "ODE",
        "stochastic",
        "Gillespie",
        "bistability",
        "feedback",
    ),
    "mechanical_force_response": ("force", "optical tweezers", "AFM", "mechanical"),
    "spatial_transport_electrostatics": (
        "diffusion",
        "reaction-diffusion",
        "Debye",
        "Poisson-Boltzmann",
        "transport",
    ),
    "evolutionary_fitness_landscape": (
        "fitness landscape",
        "directed evolution",
        "selection",
        "mutational landscape",
    ),
}


QUANT_KEYWORDS = (
    "Kd",
    "Ki",
    "IC50",
    "EC50",
    "kcat",
    "Km",
    "Tm",
    "ΔG",
    "ddG",
    "rate constant",
    "diffusion coefficient",
    "half-life",
)


DEFAULT_SOURCE_QUERIES: tuple[str, ...] = (
    '"binding affinity" protein ligand Kd OR Ki',
    '"isothermal titration calorimetry" protein ligand thermodynamics',
    '"surface plasmon resonance" protein ligand binding free energy',
    '"enzyme kinetics" kcat Km Michaelis-Menten',
    '"catalytic efficiency" enzyme kcat/Km',
    '"directed evolution" enzyme kinetics fitness landscape',
    '"protein stability" Tm folding ΔG',
    '"protein folding" stability ΔΔG mutation',
    '"thermal stability" protein engineering thermodynamics',
    'allostery conformational dynamics "energy landscape"',
    '"Markov state" protein conformational dynamics allostery',
    'FRET allostery conformational equilibrium protein',
    '"phase separation" protein condensate saturation concentration',
    'LLPS polymer statistical mechanics protein RNA',
    'coacervation biomolecular condensate phase diagram',
    'bistability feedback ODE signaling pathway dynamics',
    '"gene regulatory" circuit dynamics model ODE',
    'reaction-diffusion biological patterning quantitative model',
    '"optical tweezers" protein unfolding force',
    'diffusion electrostatics protein transport quantitative',
)


def _text(record: dict[str, Any]) -> str:
    return " ".join(
        str(record.get(k) or "")
        for k in ("title", "paper_title", "abstract", "journal", "keywords")
    )


def _keyword_score(text: str, keywords: Iterable[str]) -> int:
    lowered = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lowered)


def is_release_compatible_license(value: Any) -> bool:
    """Return True for CC0 or CC-BY style licenses accepted by the release."""

    text = str(value or "").lower().replace("_", "-")
    if "cc0" in text or "public domain" in text:
        return True
    if "cc-by" in text or "cc by" in text or "/by/" in text:
        blocked = ("noncommercial", "nc", "no derivatives", "nd", "sharealike", "sa")
        return not any(token in text for token in blocked)
    return False


def guess_domain(record: dict[str, Any]) -> str:
    text = _text(record)
    scores = {
        domain: _keyword_score(text, keywords)
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    best, score = max(scores.items(), key=lambda kv: (kv[1], kv[0]))
    return best if score else "protein_ligand_binding"


def guess_model_family(record: dict[str, Any], *, domain: str | None = None) -> str:
    text = _text(record)
    scores = {
        family: _keyword_score(text, keywords)
        for family, keywords in MODEL_FAMILY_KEYWORDS.items()
    }
    best, score = max(scores.items(), key=lambda kv: (kv[1], kv[0]))
    if score:
        return best
    if domain is None:
        domain = guess_domain(record)
    return DOMAIN_DEFAULT_MODEL_FAMILY[domain]


def score_candidate(record: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized candidate with triage fields."""

    out = dict(record)
    title = out.get("paper_title") or out.get("title") or ""
    out["paper_title"] = title
    domain = out.get("domain_guess") or guess_domain(out)
    model_family = out.get("model_family_guess") or guess_model_family(out, domain=domain)
    if model_family not in MODEL_FAMILY_VALUES:
        model_family = DOMAIN_DEFAULT_MODEL_FAMILY.get(domain, "binding_thermodynamics")
    text = _text(out)
    quant_score = _keyword_score(text, QUANT_KEYWORDS)
    has_license = is_release_compatible_license(out.get("license"))
    has_id = bool(out.get("doi") or out.get("pmcid"))
    open_access = bool(out.get("is_open_access", True))
    out["domain_guess"] = domain
    out["model_family_guess"] = model_family
    out["quantitative_keyword_count"] = quant_score
    out["triage_score"] = (
        quant_score * 4
        + int(has_license) * 10
        + int(has_id) * 8
        + int(open_access) * 6
        + int(bool(out.get("pdf_path") or out.get("source_url"))) * 4
    )
    return out


def score_candidates(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (score_candidate(r) for r in records),
        key=lambda r: (-r["triage_score"], r.get("domain_guess", ""), r.get("paper_title", "")),
    )


def _paper_key(record: dict[str, Any]) -> str:
    doi = str(record.get("doi") or "").lower().strip()
    pmcid = str(record.get("pmcid") or "").lower().strip()
    title = str(record.get("paper_title") or record.get("title") or "").lower().strip()
    return doi or pmcid or title


def _choose_full_text_url(item: dict[str, Any]) -> str | None:
    urls = ((item.get("fullTextUrlList") or {}).get("fullTextUrl") or [])
    if isinstance(urls, dict):
        urls = [urls]
    for entry in urls:
        if not isinstance(entry, dict):
            continue
        url = entry.get("url")
        style = str(entry.get("documentStyle") or "").lower()
        if url and "pdf" in style:
            return url
    for entry in urls:
        if isinstance(entry, dict) and entry.get("url"):
            return entry["url"]
    return None


def candidate_from_europepmc_result(item: dict[str, Any], *, query: str) -> dict[str, Any]:
    """Normalize one Europe PMC search result into the source-candidate shape."""

    doi = item.get("doi")
    pmcid = item.get("pmcid")
    full_text_url = _choose_full_text_url(item)
    license_value = item.get("license") or item.get("licenseType")
    return {
        "candidate_id": item.get("id") or doi or pmcid,
        "paper_title": item.get("title"),
        "abstract": item.get("abstractText"),
        "doi": doi,
        "pmcid": pmcid,
        "journal": item.get("journalTitle"),
        "pub_year": item.get("pubYear"),
        "license": license_value,
        "is_open_access": str(item.get("isOpenAccess", "")).upper() == "Y",
        "source_url": full_text_url,
        "europepmc_id": item.get("id"),
        "europepmc_source": item.get("source"),
        "cited_by_count": int(item.get("citedByCount") or 0),
        "source_query": query,
    }


def fetch_europepmc_candidates(
    queries: Iterable[str],
    *,
    target_size: int = 1000,
    page_size: int = 100,
    timeout_seconds: int = 30,
) -> list[dict[str, Any]]:
    """Fetch and score an OA-compatible candidate pool from Europe PMC.

    The API call is intentionally narrow: open-access records with a DOI or
    PMCID and enough abstract/title text to support later triage. Raw PDFs are
    not downloaded here.
    """

    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for query in queries:
        cursor = "*"
        while len(candidates) < target_size:
            full_query = f"({query}) AND OPEN_ACCESS:Y"
            params = {
                "query": full_query,
                "format": "json",
                "pageSize": str(page_size),
                "cursorMark": cursor,
                "sort": "CITED desc",
                "resultType": "core",
            }
            response = requests.get(
                EUROPE_PMC_SEARCH_URL,
                params=params,
                timeout=timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            results = (payload.get("resultList") or {}).get("result") or []
            if not results:
                break
            for item in results:
                candidate = candidate_from_europepmc_result(item, query=query)
                key = _paper_key(candidate)
                if not key or key in seen:
                    continue
                if not (candidate.get("doi") or candidate.get("pmcid")):
                    continue
                if not is_release_compatible_license(candidate.get("license")):
                    continue
                seen.add(key)
                candidates.append(candidate)
                if len(candidates) >= target_size:
                    break
            next_cursor = payload.get("nextCursorMark")
            if not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor
        if len(candidates) >= target_size:
            break
    return score_candidates(candidates)


def _candidate_key(record: dict[str, Any]) -> str:
    return str(
        record.get("candidate_id")
        or record.get("doc_id")
        or record.get("pmcid")
        or record.get("doi")
        or record.get("paper_title")
    )


def select_parse_batch(
    candidates: list[dict[str, Any]],
    *,
    batch_size: int = 100,
    exclude_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Select a deterministic balanced parse batch from scored candidates."""

    exclude_ids = exclude_ids or set()
    selected: list[dict[str, Any]] = []
    domain_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    pool = [
        c
        for c in score_candidates(candidates)
        if _candidate_key(c) not in exclude_ids
        and (c.get("doi") or c.get("pmcid"))
        and is_release_compatible_license(c.get("license"))
    ]
    while pool and len(selected) < batch_size:
        best_index = 0
        best_rank: tuple[int, int, int, str] | None = None
        for i, candidate in enumerate(pool):
            domain = candidate.get("domain_guess") or guess_domain(candidate)
            family = candidate.get("model_family_guess") or guess_model_family(candidate, domain=domain)
            rank = (
                domain_counts[domain],
                family_counts[family],
                -int(candidate.get("triage_score", 0)),
                str(candidate.get("paper_title", "")),
            )
            if best_rank is None or rank < best_rank:
                best_rank = rank
                best_index = i
        chosen = pool.pop(best_index)
        domain_counts[chosen["domain_guess"]] += 1
        family_counts[chosen["model_family_guess"]] += 1
        selected.append(chosen)
    return selected


def to_parse_manifest_row(record: dict[str, Any], *, index: int, batch_id: str) -> dict[str, Any]:
    doc_id = record.get("doc_id") or f"{batch_id}_{index:04d}"
    return {
        "doc_id": doc_id,
        "candidate_id": record.get("candidate_id"),
        "paper_title": record.get("paper_title"),
        "doi": record.get("doi"),
        "pmcid": record.get("pmcid"),
        "license": record.get("license"),
        "source_url": record.get("source_url"),
        "pdf_path": record.get("pdf_path"),
        "domain_guess": record.get("domain_guess"),
        "model_family_guess": record.get("model_family_guess"),
        "triage_score": record.get("triage_score"),
    }


def pdf_candidate_urls(row: dict[str, Any]) -> list[str]:
    """Return ordered PDF URL attempts for a manifest row."""

    urls: list[str] = []
    source_url = row.get("source_url")
    if source_url:
        urls.append(str(source_url))
    pmcid = str(row.get("pmcid") or "").strip()
    if pmcid:
        urls.extend(
            [
                f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/",
                f"https://europepmc.org/articles/{pmcid}?pdf=render",
            ]
        )
    out = []
    for url in urls:
        if url and url not in out:
            out.append(url)
    return out


def _looks_like_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return fh.read(5) == b"%PDF-"
    except OSError:
        return False


def download_pdf_for_row(
    row: dict[str, Any],
    *,
    pdf_dir: Path,
    timeout_seconds: int = 90,
    resume: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Download one PDF without overwriting existing files.

    Returns ``(manifest_row, report_row)``. ``manifest_row`` is None when all
    URL attempts fail.
    """

    doc_id = row.get("doc_id")
    if not doc_id:
        return None, {"status": "failed", "error": "missing doc_id", "row": row}
    pdf_path = pdf_dir / f"{doc_id}.pdf"
    if pdf_path.exists():
        if resume and _looks_like_pdf(pdf_path):
            out = dict(row)
            out["pdf_path"] = str(pdf_path)
            return out, {
                "doc_id": doc_id,
                "status": "already_downloaded",
                "pdf_path": str(pdf_path),
                "bytes": pdf_path.stat().st_size,
            }
        return None, {
            "doc_id": doc_id,
            "status": "failed",
            "error": f"refusing to overwrite existing file: {pdf_path}",
        }

    errors = []
    for url in pdf_candidate_urls(row):
        tmp_path = pdf_path.with_suffix(".pdf.tmp")
        if tmp_path.exists():
            tmp_path.unlink()
        try:
            with requests.get(
                url,
                headers=HTTP_HEADERS,
                stream=True,
                timeout=timeout_seconds,
                allow_redirects=True,
            ) as response:
                response.raise_for_status()
                tmp_path.parent.mkdir(parents=True, exist_ok=True)
                with tmp_path.open("wb") as fh:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            fh.write(chunk)
            if not _looks_like_pdf(tmp_path):
                size = tmp_path.stat().st_size if tmp_path.exists() else 0
                tmp_path.unlink(missing_ok=True)
                raise ValueError(f"downloaded content is not a PDF ({size} bytes)")
            tmp_path.rename(pdf_path)
            out = dict(row)
            out["pdf_path"] = str(pdf_path)
            out["download_source_url"] = url
            return out, {
                "doc_id": doc_id,
                "status": "downloaded",
                "pdf_path": str(pdf_path),
                "source_url": url,
                "bytes": pdf_path.stat().st_size,
            }
        except Exception as exc:  # noqa: BLE001 - try alternate PDF mirrors.
            tmp_path.unlink(missing_ok=True)
            errors.append({"url": url, "error": str(exc)[:500]})

    return None, {"doc_id": doc_id, "status": "failed", "errors": errors}


def download_batch_pdfs(
    rows: list[dict[str, Any]],
    *,
    out_dir: Path,
    timeout_seconds: int = 90,
    resume: bool = False,
) -> dict[str, Any]:
    if out_dir.exists() and any(out_dir.iterdir()) and not resume:
        raise FileExistsError(f"refusing to write into non-empty directory: {out_dir}")
    pdf_dir = out_dir / "pdfs"
    reports = []
    local_rows = []
    provenance: dict[str, dict[str, Any]] = {}
    for row in rows:
        local_row, report = download_pdf_for_row(
            row,
            pdf_dir=pdf_dir,
            timeout_seconds=timeout_seconds,
            resume=resume,
        )
        reports.append(report)
        if local_row:
            local_rows.append(local_row)
            doc_id = local_row["doc_id"]
            provenance[doc_id] = {
                k: local_row.get(k)
                for k in (
                    "paper_title",
                    "doi",
                    "pmcid",
                    "license",
                    "source_url",
                    "candidate_id",
                    "domain_guess",
                    "model_family_guess",
                )
                if local_row.get(k) is not None
            }

    out_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_jsonl(out_dir / "local_manifest.jsonl", local_rows)
    atomic_write_jsonl(out_dir / "download_report.jsonl", reports)
    (out_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True)
    )
    counts = Counter(r["status"] for r in reports)
    summary = {
        "n_manifest": len(rows),
        "n_downloaded": counts.get("downloaded", 0),
        "n_already_downloaded": counts.get("already_downloaded", 0),
        "n_failed": counts.get("failed", 0),
        "out_dir": str(out_dir),
        "local_manifest": str(out_dir / "local_manifest.jsonl"),
        "provenance": str(out_dir / "provenance.json"),
        "download_report": str(out_dir / "download_report.jsonl"),
    }
    (out_dir / "download_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True)
    )
    return summary


def render_manual_parse_instructions(
    *,
    manifest_path: Path,
    parsed_dir: Path,
    run_dir: Path,
) -> str:
    return f"""# Manual MinerU Parse Handoff

Run this parse step in an environment with access to the MinerU API. This
repository step is intentionally manual so source PDF handling and API
credentials stay outside the public repository.

```bash
python -m biophysevo.mineru.parse \\
  --manifest {manifest_path} \\
  --config configs/mineru.yaml \\
  --parsed-dir {parsed_dir} \\
  --run-dir {run_dir} \\
  --resume
```

Expected normalized outputs should land under:

```text
{parsed_dir}/<doc_id>/
  document.md
  document.json
  evidence_blocks.jsonl
  parse_metadata.json
```

After the command finishes, run the parse audit:

```bash
python -m biophysevo.sources.scale200 audit-parse \\
  --manifest {manifest_path} \\
  --parsed-dir {parsed_dir} \\
  --out {run_dir / "parse_audit.json"}
```
"""


def audit_parsed_outputs(manifest_rows: list[dict[str, Any]], parsed_dir: Path) -> dict[str, Any]:
    required = ["document.md", "document.json", "evidence_blocks.jsonl", "parse_metadata.json"]
    records = []
    for row in manifest_rows:
        doc_id = row["doc_id"]
        doc_dir = parsed_dir / doc_id
        missing = [name for name in required if not (doc_dir / name).exists()]
        status = "parsed" if doc_dir.exists() and not missing else "missing_or_incomplete"
        records.append({"doc_id": doc_id, "status": status, "missing": missing})
    counts = Counter(r["status"] for r in records)
    return {
        "n_manifest": len(manifest_rows),
        "n_parsed": counts.get("parsed", 0),
        "n_missing_or_incomplete": counts.get("missing_or_incomplete", 0),
        "records": records,
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return list(read_jsonl(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scale-to-200 source utilities.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_score = sub.add_parser("score-candidates")
    p_score.add_argument("--input", type=Path, required=True)
    p_score.add_argument("--out", type=Path, required=True)

    p_pool = sub.add_parser("build-pool")
    p_pool.add_argument("--out", type=Path, required=True)
    p_pool.add_argument("--queries", type=Path, default=None)
    p_pool.add_argument("--target-size", type=int, default=1000)
    p_pool.add_argument("--page-size", type=int, default=100)
    p_pool.add_argument("--summary-out", type=Path, default=None)

    p_batch = sub.add_parser("prepare-batch")
    p_batch.add_argument("--candidates", type=Path, required=True)
    p_batch.add_argument("--out-manifest", type=Path, required=True)
    p_batch.add_argument("--instructions", type=Path, required=True)
    p_batch.add_argument("--batch-id", default=None)
    p_batch.add_argument("--batch-size", type=int, default=100)
    p_batch.add_argument("--parsed-dir", type=Path, default=Path("data/intermediate/parsed_docs_real"))
    p_batch.add_argument("--run-dir", type=Path, default=None)
    p_batch.add_argument("--exclude-manifest", action="append", type=Path, default=[])

    p_download = sub.add_parser("download-pdfs")
    p_download.add_argument("--manifest", type=Path, required=True)
    p_download.add_argument("--out-dir", type=Path, required=True)
    p_download.add_argument("--timeout-seconds", type=int, default=90)
    p_download.add_argument(
        "--resume",
        action="store_true",
        help="Reuse existing PDFs in out-dir without overwriting them.",
    )

    p_audit = sub.add_parser("audit-parse")
    p_audit.add_argument("--manifest", type=Path, required=True)
    p_audit.add_argument("--parsed-dir", type=Path, required=True)
    p_audit.add_argument("--out", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.cmd == "score-candidates":
        scored = score_candidates(_read_jsonl(args.input))
        atomic_write_jsonl(args.out, scored)
        return 0

    if args.cmd == "build-pool":
        if args.queries:
            queries = [
                line.strip()
                for line in args.queries.read_text().splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        else:
            queries = list(DEFAULT_SOURCE_QUERIES)
        candidates = fetch_europepmc_candidates(
            queries,
            target_size=args.target_size,
            page_size=args.page_size,
        )
        atomic_write_jsonl(args.out, candidates)
        summary = {
            "n_candidates": len(candidates),
            "domain_counts": dict(Counter(c.get("domain_guess") for c in candidates)),
            "model_family_counts": dict(
                Counter(c.get("model_family_guess") for c in candidates)
            ),
        }
        if args.summary_out:
            args.summary_out.parent.mkdir(parents=True, exist_ok=True)
            args.summary_out.write_text(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    if args.cmd == "prepare-batch":
        exclude_ids: set[str] = set()
        for manifest in args.exclude_manifest:
            exclude_ids.update(_candidate_key(r) for r in _read_jsonl(manifest))
        candidates = _read_jsonl(args.candidates)
        selected = select_parse_batch(
            candidates,
            batch_size=args.batch_size,
            exclude_ids=exclude_ids,
        )
        batch_id = args.batch_id or f"batch_{timestamp()}"
        rows = [
            to_parse_manifest_row(r, index=i, batch_id=batch_id)
            for i, r in enumerate(selected, start=1)
        ]
        atomic_write_jsonl(args.out_manifest, rows)
        run_dir = args.run_dir or Path("runs") / f"{timestamp()}_parse_{batch_id}"
        args.instructions.parent.mkdir(parents=True, exist_ok=True)
        args.instructions.write_text(
            render_manual_parse_instructions(
                manifest_path=args.out_manifest,
                parsed_dir=args.parsed_dir,
                run_dir=run_dir,
            )
        )
        return 0

    if args.cmd == "download-pdfs":
        rows = _read_jsonl(args.manifest)
        summary = download_batch_pdfs(
            rows,
            out_dir=args.out_dir,
            timeout_seconds=args.timeout_seconds,
            resume=args.resume,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if summary["n_downloaded"] or summary["n_already_downloaded"] else 1

    if args.cmd == "audit-parse":
        manifest_rows = _read_jsonl(args.manifest)
        report = audit_parsed_outputs(manifest_rows, args.parsed_dir)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True))
        if report["n_missing_or_incomplete"]:
            print(
                f"parse audit found {report['n_missing_or_incomplete']} incomplete docs",
                file=sys.stderr,
            )
            return 1
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
