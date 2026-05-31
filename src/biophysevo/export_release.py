"""CLI: build the Biophys-Bridge release bundle in data/release/.

    python -m biophysevo.export_release \
        --input data/intermediate/cases_validated.jsonl \
        --out-dir data/release \
        --min-quality-score 0.8

Produces:
    data/release/biophys_bridge_evo_cases.jsonl
    data/release/biophys_bridge_10_gold_samples.jsonl
    data/release/biophys_bridge_30_gold_samples.jsonl
    data/release/biophys_bridge_metadata.json
    data/release/data_card.md
    data/release/biophys_bridge_schema.json
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import sys
from pathlib import Path

from biophysevo.extraction.sci_evo_view import to_three_block
from biophysevo.physics.consistency import check_case
from biophysevo.quality.content_quality import content_quality_issues
from biophysevo.quality.deduplicate import find_duplicate_case_ids
from biophysevo.quality.scoring import aggregate_metrics, per_case_score
from biophysevo.quality.validate_schema import validate_each
from biophysevo.schemas.case_schema import emit_json_schema
from biophysevo.utils.io import atomic_write_jsonl, read_jsonl
from biophysevo.utils.logging import get_logger


LOG = get_logger("biophysevo.export_release")


_ALL_DOMAINS = 6  # DOMAIN_BRIDGE_COMPATIBILITY in case_schema has 6 v1 domains
_CONSISTENCY_AUDIT_MARKER = "Deterministic physics audit:"


def _md_escape(text: str) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ").strip()


def _consistency_summary(check: dict | None) -> str:
    if not check:
        return (
            f"{_CONSISTENCY_AUDIT_MARKER} not_checked; no supported deterministic "
            "relation fired for the reported quantitative-evidence set."
        )
    status = check.get("status", "not_checked")
    checks = check.get("checks") or [check]
    relation_bits = []
    for item in checks:
        relation = item.get("relation", "unknown relation")
        item_status = item.get("status", status)
        detail = relation
        if "residual_kcal_per_mol" in item:
            detail += f" residual={item['residual_kcal_per_mol']} kcal/mol"
        elif "residual_K" in item:
            detail += f" residual={item['residual_K']} K"
        elif "derived_dG_act_kcal_per_mol" in item:
            detail += f" dG_act={item['derived_dG_act_kcal_per_mol']} kcal/mol"
        relation_bits.append(f"{detail} [{item_status}]")
    return f"{_CONSISTENCY_AUDIT_MARKER} {status}; " + "; ".join(relation_bits)


def _strip_existing_audit(text: str) -> str:
    if _CONSISTENCY_AUDIT_MARKER not in text:
        return text.strip()
    return text.split(_CONSISTENCY_AUDIT_MARKER, 1)[0].rstrip(" |;")


def _with_physics_audit(record: dict) -> tuple[dict, dict | None]:
    """Return a release record with a per-case deterministic audit note."""
    rec = json.loads(json.dumps(record))
    check = check_case(rec)
    interp = rec.setdefault("physical_interpretation", {})
    existing = _strip_existing_audit(interp.get("consistency_check") or "")
    summary = _consistency_summary(check)
    interp["consistency_check"] = f"{existing} | {summary}" if existing else summary
    return rec, check


def _write_splits(out_dir: Path, records: list[dict]) -> dict:
    """Write deterministic stratified train/validation/test JSONL splits."""
    split_dir = out_dir / "splits"
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        by_domain[str(rec.get("domain"))].append(rec)

    splits: dict[str, list[dict]] = {"train": [], "validation": [], "test": []}
    for _, group in sorted(by_domain.items()):
        ordered = sorted(group, key=lambda r: str(r.get("case_id")))
        n = len(ordered)
        if n >= 3:
            n_test = max(1, round(n * 0.10))
            n_val = max(1, round(n * 0.10))
        else:
            n_test = 0
            n_val = 0
        n_train = max(0, n - n_val - n_test)
        splits["train"].extend(ordered[:n_train])
        splits["validation"].extend(ordered[n_train:n_train + n_val])
        splits["test"].extend(ordered[n_train + n_val:])

    for name, rows in splits.items():
        rows.sort(key=lambda r: str(r.get("case_id")))
        atomic_write_jsonl(split_dir / f"{name}.jsonl", rows)

    manifest = {
        "strategy": "deterministic stratified by domain; case_id-sorted within each domain",
        "split_counts": {name: len(rows) for name, rows in splits.items()},
        "domain_counts_by_split": {
            name: dict(Counter(r.get("domain") for r in rows))
            for name, rows in splits.items()
        },
    }
    (split_dir / "split_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True)
    )
    return manifest


def render_data_card(records: list[dict], metrics: dict) -> str:
    """Build a dataset card that accurately describes the shipped cases.

    Domains, counts, provenance, and quality numbers are derived from the actual
    released records so the card never drifts from the data it ships with.
    """
    n = len(records)
    domain_counts = Counter(r.get("domain") for r in records)
    n_domains = len(domain_counts)

    domain_lines = "\n".join(
        f"- `{dom}`: {cnt} case(s)"
        for dom, cnt in sorted(domain_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    )
    model_family_counts = metrics.get("physics_model_family_counts") or {}
    model_family_lines = "\n".join(
        f"- `{family}`: {cnt} case(s)"
        for family, cnt in sorted(
            model_family_counts.items(), key=lambda kv: (-kv[1], kv[0])
        )
    )

    prov_rows = "\n".join(
        "| {cid} | {title} | {doi} | {lic} | {nqe} |".format(
            cid=_md_escape(r.get("case_id")),
            title=_md_escape(r.get("source", {}).get("paper_title")) or "—",
            doi=_md_escape(r.get("source", {}).get("doi")) or "—",
            lic=_md_escape(r.get("source", {}).get("license")) or "—",
            nqe=len(r.get("quantitative_evidence") or []),
        )
        for r in records
    )

    def m(key: str) -> str:
        v = metrics.get(key)
        return f"{v:.3f}" if isinstance(v, (int, float)) else "n/a"

    sample_note = (
        ""
        if n >= 10
        else f"\n- This release ships **{n} cases**, below the 10-complete-sample "
        "target; additional CC-licensed papers can be added to reach 10.\n"
    )
    citation = """```bibtex
@dataset{xu2026biophysbridge,
  author    = {Xu, Qingyang},
  title     = {Biophys-Bridge: A Physics-Grounded Sci-Evo Dataset for Biological Mechanism Reasoning},
  year      = {2026},
  url       = {https://github.com/qyxu1994/Biophys-Bridge},
  license   = {CC-BY-4.0}
}
```"""

    return f"""# Biophys-Bridge Dataset Card

## Name
Biophys-Bridge (Sci-Evo dataset type: Sci-Evo) — {n} cases.

## Intended use
Training and evaluating AI research agents on physics-grounded scientific
reasoning: each case is a physics-grounded Scientific Evolution Case linking a
physical model -> quantitative evidence -> biological mechanism -> agent
decision (research question -> physical model -> quantitative observation ->
biophysical interpretation -> mechanism -> next-step decision). Suitable for
AGI4S evaluation, scientific-reasoning benchmarks, and AI research agents.

## Domains in this release
This release covers {n_domains} of the {_ALL_DOMAINS} schema-supported v1 domains
(domain is assigned per paper from its actual content):

{domain_lines}

## Physics model families
The primary `biophysical_model.model_family` records the physics model family
used by the main equation and agent decision; supporting families, when
present, are listed in `secondary_model_families`.

{model_family_lines}

## Construction method
1. **MinerU v4** parses each source PDF into markdown + tables + formulas +
   figures.
2. Outputs are normalized into per-document evidence blocks: tables, formulas,
   figure captions, and numeric-bearing prose paragraphs, each with a stable
   `evidence_id`.
3. An **evidence-only LLM pass (OpenAI gpt-4o)** extracts `quantitative_evidence`
   and fills the physical-interpretation / biological-mechanism / agent-task
   fields. Every value and claim must cite an `evidence_id` present in the
   document's blocks; unsupported fields are `null` and any fabricated
   `evidence_id` is dropped (no invented data).
4. Each extracted value was checked to appear verbatim in its cited evidence
   block during review; cases reach `manual_review_status = reviewed` only after
   that grounding check passes.
5. Release export applies a semantic content-quality gate: unresolved template
   markers, character-split tool/skill vocabularies, evidence-ID-only prompts,
   weak task answers, and missing `next_step` stages are excluded.
6. Release export runs a deterministic physics audit for every case and writes
   the result into `physical_interpretation.consistency_check`. Relation-level
   pass rate is reported only for cases where an implemented relation applies.
7. The 10 gold samples include `expert_annotation` with curator physics
   reasoning, biological reasoning, uncertainty, and reviewer notes.
8. The extended 30-case gold file is emitted for the scaled review workflow;
   the current small release includes the ranked file shape before all 30
   records are expert-annotated.

## Source provenance
| case_id | paper_title | DOI | license | n_quant_evidence |
|---|---|---|---|---|
{prov_rows}

## Licenses and source attribution
Each case carries its upstream paper's license in `source.license`; only
CC-BY / CC0 papers are included. The curated dataset and reports are released
as CC-BY-4.0 (`LICENSE-DATA`); repository code is MIT licensed. Raw PDFs and
MinerU intermediates are not redistributed.

## MinerU-derived evidence policy
Every quantitative claim and every gold answer is grounded in a MinerU
`evidence_id`; cases require a `source.mineru_parse_id` and are excluded from the
release without traceable MinerU artifacts.

## Quality metrics (this release)
- cases: {n}
- schema_valid_rate: {m('schema_valid_rate')}
- quantitative_evidence_rate: {m('quantitative_evidence_rate')}
- unit_normalization_success_rate: {m('unit_normalization_success_rate')}
- source_license_coverage: {m('source_license_coverage')}
- manual_review_pass_rate: {m('manual_review_pass_rate')}
- evidence_coverage_rate: {m('evidence_coverage_rate')}
- sci_evo_completeness_score: {m('sci_evo_completeness_score')}
- release_content_quality_pass_rate: {m('release_content_quality_pass_rate')}
- gold_expert_annotation_coverage: {m('gold_expert_annotation_coverage')}
- equation_bearing_coverage: {m('equation_bearing_coverage')}
- physics_consistency_audit_coverage: {m('physics_consistency_audit_coverage')}
- physics_consistency_checked_rate: {m('physics_consistency_checked_rate')}
- physics_consistency_pass_rate: {m('physics_consistency_pass_rate')}
- mean_modalities_per_case: {m('mean_modalities_per_case')}
- cases_with_3plus_modalities_rate: {m('cases_with_3plus_modalities_rate')}
- failure_or_revision_n: {metrics.get('failure_or_revision_n', 'n/a')}
- cases_with_failure_or_revision_rate: {m('cases_with_failure_or_revision_rate')}

See `biophys_bridge_metadata.json` for the full metric set and
`biophys_bridge_schema.json` for the canonical JSON Schema.

## Out-of-scope use
- Clinical diagnosis or any safety-critical decision making.
- Using extracted values without checking the cited `evidence_id`.
- Use as a drug-discovery oracle.

## Known limitations
- Covers {n_domains} of {_ALL_DOMAINS} schema domains; coverage reflects the
  source-paper set, not the full domain space.{sample_note}
- `failure_or_revision` is populated only where the source paper actually reports
  a failure/revision (never fabricated). Those cases are the core dynamic
  Sci-Evo subset; the remaining cases provide evidence-grounded mechanism
  reasoning substrate.
- The deterministic physics-consistency audit is written on every case. The
  relation-level checker currently covers three relations:
  ΔG = RT·ln(K) (Kd / Ki / IC50 vs reported binding free energy),
  Eyring ΔG‡ = RT·ln(k_B·T / (h·kcat)) (kcat sanity range 4–35 kcal/mol),
  and van't Hoff at Tm (Tm = ΔH_unf/ΔS_unf when all three are reported).
  Cases without any applicable trio report `not_checked` (see
  `physics_consistency_checked_rate` in the metadata).
- Fields are LLM-extracted under an evidence-only contract; review verified that
  each quantitative value is grounded in its cited block; interpretive prose and
  reasoning steps are evidence-cited but warrant a final expert read.
- The 10 gold samples include `expert_annotation` blocks with curator physics
  reasoning, biological reasoning, uncertainty, and reviewer notes. The
  extended 30-case gold file is fully expert-annotated only in the scaled
  200-case release workflow.
- Release export rejects unresolved template markers, character-split
  tool/skill vocabularies, weak task prompts, and missing `next_step` stages.
- Some MinerU table parses can miss footnoted assay conditions.

## Citation
If you use Biophys-Bridge, please cite:

{citation}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export the Biophys-Bridge release bundle.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("data/release"))
    parser.add_argument("--min-quality-score", type=float, default=0.8)
    parser.add_argument("--gold-sample-size", type=int, default=10)
    parser.add_argument("--extended-gold-sample-size", type=int, default=30)
    args = parser.parse_args(argv)

    raw = list(read_jsonl(args.input))
    valid, errors = validate_each(raw)
    if errors:
        print(f"refusing to export: {len(errors)} schema errors in input", file=sys.stderr)
        return 1
    dups = find_duplicate_case_ids(valid)
    if dups:
        print(f"refusing to export: duplicate case_ids: {dups}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)

    scored: list[tuple[float, dict]] = []
    n_unreviewed = 0
    n_content_quality_excluded = 0
    n_below_score = 0
    content_quality_failures: list[dict[str, object]] = []
    for c in valid:
        # Invariant: only expert-reviewed cases ship. Regex-built template cases
        # are marked needs_fix and score well on structural signals, so a score
        # gate alone would let them leak into a release.
        if c.quality.manual_review_status != "reviewed":
            n_unreviewed += 1
            continue
        issues = content_quality_issues(c)
        if issues:
            n_content_quality_excluded += 1
            content_quality_failures.append(
                {"case_id": c.case_id, "issues": issues[:10]}
            )
            continue
        score = per_case_score(c)
        if score < args.min_quality_score:
            n_below_score += 1
            continue
        rec = json.loads(c.model_dump_json())
        rec["quality"]["score"] = score
        rec, _ = _with_physics_audit(rec)
        scored.append((score, rec))

    if not scored:
        print(
            "no cases met the release gate "
            f"(min-quality-score={args.min_quality_score}, "
            f"excluded {n_unreviewed} not-reviewed, "
            f"{n_content_quality_excluded} content-quality failures)",
            file=sys.stderr,
        )
        return 1

    scored.sort(key=lambda x: x[0], reverse=True)

    cases_path = args.out_dir / "biophys_bridge_evo_cases.jsonl"
    gold_path = args.out_dir / "biophys_bridge_10_gold_samples.jsonl"
    extended_gold_path = args.out_dir / "biophys_bridge_30_gold_samples.jsonl"
    meta_path = args.out_dir / "biophys_bridge_metadata.json"
    schema_path = args.out_dir / "biophys_bridge_schema.json"
    data_card_path = args.out_dir / "data_card.md"

    atomic_write_jsonl(cases_path, (r for _, r in scored))
    atomic_write_jsonl(
        gold_path,
        (r for _, r in scored[: args.gold_sample_size]),
    )
    atomic_write_jsonl(
        extended_gold_path,
        (r for _, r in scored[: args.extended_gold_sample_size]),
    )
    split_manifest = _write_splits(args.out_dir, [r for _, r in scored])
    schema_path.write_text(json.dumps(emit_json_schema(), indent=2, sort_keys=True))

    view_path = args.out_dir / "biophys_bridge_sci_evo_view.jsonl"
    atomic_write_jsonl(
        view_path,
        (to_three_block(r, check_case(r)) for _, r in scored),
    )

    release_valid, _ = validate_each([r for _, r in scored])
    metrics = aggregate_metrics(release_valid, n_raw=len(scored))
    metrics["manual_review_pass_rate"] = (
        sum(
            1
            for _, r in scored
            if (r.get("quality") or {}).get("manual_review_status") == "reviewed"
        )
        / len(scored)
        if scored
        else 0.0
    )
    metrics["source_n_raw"] = len(raw)
    metrics["source_n_valid"] = len(valid)
    metrics["built_n"] = len(valid)
    metrics["shipped_n"] = len(scored)
    metrics["release_n"] = len(scored)
    metrics["gold_n"] = min(args.gold_sample_size, len(scored))
    metrics["extended_gold_n"] = min(args.extended_gold_sample_size, len(scored))
    metrics["min_quality_score"] = args.min_quality_score
    metrics["excluded_not_reviewed"] = n_unreviewed
    metrics["excluded_content_quality"] = n_content_quality_excluded
    metrics["excluded_below_score"] = n_below_score
    metrics["exclusion_counts_reconciled"] = (
        len(valid) - len(scored)
        == n_unreviewed + n_content_quality_excluded + n_below_score
    )
    metrics["content_quality_failures"] = content_quality_failures[:50]
    metrics["release_content_quality_pass_rate"] = 1.0
    gold_records = [r for _, r in scored[: args.gold_sample_size]]
    metrics["gold_expert_annotation_coverage"] = (
        sum(1 for r in gold_records if r.get("expert_annotation")) / len(gold_records)
        if gold_records
        else None
    )
    metrics["release_expert_annotation_coverage"] = (
        sum(1 for _, r in scored if r.get("expert_annotation")) / len(scored)
        if scored
        else None
    )
    metrics["domain_counts"] = dict(Counter(r.get("domain") for _, r in scored))
    metrics["physics_model_family_counts"] = dict(
        Counter(
            r.get("biophysical_model", {}).get("model_family")
            for _, r in scored
            if r.get("biophysical_model", {}).get("model_family")
        )
    )
    secondary_counts: Counter[str] = Counter()
    for _, r in scored:
        secondary_counts.update(
            r.get("biophysical_model", {}).get("secondary_model_families") or []
        )
    metrics["secondary_model_family_counts"] = dict(secondary_counts)
    extended_gold_records = [r for _, r in scored[: args.extended_gold_sample_size]]
    metrics["extended_gold_expert_annotation_coverage"] = (
        sum(1 for r in extended_gold_records if r.get("expert_annotation"))
        / len(extended_gold_records)
        if extended_gold_records
        else None
    )
    metrics["equation_bearing_coverage"] = (
        sum(
            1
            for _, r in scored
            if (r.get("biophysical_model", {}).get("equation_latex") or "").strip()
        )
        / len(scored)
        if scored
        else 0.0
    )
    checks = [check_case(r) for _, r in scored]
    checked = [c for c in checks if c and c.get("status") in ("consistent", "inconsistent")]
    metrics["physics_consistency_audit_coverage"] = 1.0 if scored else 0.0
    metrics["physics_consistency_checked_rate"] = (len(checked) / len(scored)) if scored else 0.0
    metrics["physics_consistency_pass_rate"] = (
        sum(1 for c in checked if c["status"] == "consistent") / len(checked) if checked else None
    )
    modality_counts = Counter(
        e.get("modality")
        for _, r in scored
        for e in (r.get("evidence") or [])
        if e.get("modality")
    )
    metrics["evidence_modality_counts"] = dict(modality_counts)
    modalities_per_case = [
        len({e.get("modality") for e in (r.get("evidence") or []) if e.get("modality")})
        for _, r in scored
    ]
    metrics["mean_modalities_per_case"] = (
        sum(modalities_per_case) / len(modalities_per_case)
        if modalities_per_case
        else 0.0
    )
    metrics["cases_with_3plus_modalities_rate"] = (
        sum(1 for n_modalities in modalities_per_case if n_modalities >= 3) / len(scored)
        if scored
        else 0.0
    )
    failure_n = sum(
        1
        for _, r in scored
        if (r.get("failure_or_revision") or {}).get("present")
    )
    metrics["failure_or_revision_n"] = failure_n
    metrics["cases_with_failure_or_revision_rate"] = (
        failure_n / len(scored) if scored else 0.0
    )
    metrics["agent_task_type_counts"] = dict(
        Counter(
            task.get("task_type")
            for _, r in scored
            for task in (r.get("agent_tasks") or [])
            if task.get("task_type")
        )
    )
    metrics["split_counts"] = split_manifest["split_counts"]
    metrics["split_strategy"] = split_manifest["strategy"]
    meta_path.write_text(json.dumps(metrics, indent=2, sort_keys=True))

    data_card_path.write_text(render_data_card([r for _, r in scored], metrics))

    LOG.info(
        "release exported: cases=%d gold=%d -> %s",
        len(scored),
        min(args.gold_sample_size, len(scored)),
        args.out_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
