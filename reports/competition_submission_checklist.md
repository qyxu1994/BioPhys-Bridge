# Biophys-Bridge Competition Submission Checklist

## Scientific expression and multimodal understanding
- [x] Each case carries `quantitative_evidence` linked to a MinerU
      `evidence_id` (table / formula / figure caption / text).
- [x] `biophysical_model.equation_latex` is present for cases that admit a
      closed-form thermodynamic or kinetic model.
- [x] `physical_interpretation` and `biological_mechanism` are populated
      with evidence-grounded content (no `[template - needs expert review]`
      markers) in any case shipped in the release.
- [x] At least 10 gold samples include multimodal evidence (text + table
      + formula).
- [x] Multimodality is quantified in metadata
      (`mean_modalities_per_case`, `cases_with_3plus_modalities_rate`,
      `evidence_modality_counts`).

## Scientific value and novelty
- [x] Six-domain release scope and bridge paradigms clearly
      stated in [`README.md`](../README.md) and
      [`reports/technical_report.md`](technical_report.md).
- [x] Each case populates `dataset_family = "Biophys-Bridge"` and
      `dataset_subtype = "Sci-Evo"`.
- [x] `bridge_type` is one of the six allowed values and is compatible
      with `domain` (schema-enforced).
- [x] Sci-Evo trajectories cover at least 5 of the 7 canonical stages on
      average (tracked by `sci_evo_completeness_score`).

## AI-ready schema and reasoning support
- [x] JSON Schema exported to `data/release/biophys_bridge_schema.json`
      via `python -m biophysevo.schemas.case_schema --emit-json`.
- [x] All cases pass `python -m biophysevo.validate`.
- [x] Every `agent_tasks[].gold_answer` cites at least one
      `supporting_evidence_ids`.
- [x] `agent_tasks[].required_reasoning_skills` is drawn from the
      physics-grounded skill list (unit normalization, thermodynamic
      directionality, free-energy interpretation, enzyme kinetic
      interpretation, folding stability interpretation, structure-function
      reasoning, evidence-grounded mechanism reasoning, next-experiment
      design).
- [x] Release export content-quality gate passes with no unresolved template
      markers, character-split vocabularies, weak task prompts, or missing
      `next_step` stages.
- [x] Deterministic train/validation/test splits are emitted under
      `data/release/splits/`.
- [x] HuggingFace `datasets` loading is documented with standard JSONL
      `data_files` for train/validation/test splits.
- [x] Reproducible agent-task eval harness is present:
      `python -m biophysevo.evaluation.run_agent_eval`.

## Engineering quality and reproducibility
- [x] `pytest` is green.
- [x] `python -m biophysevo.quality.validate_cases ...` produces a
      validation report with no schema errors and zero duplicates.
- [x] Smoke and full evaluation modes run from the same input and write to
      isolated folders (`runs/` vs `results/aggregate/`).
- [x] All run folders contain `config.yaml`, `command.txt`,
      `manifest.jsonl`, `checkpoints/`, `metrics.json`.
- [x] One-command release refresh is documented as `make release`.

## Open sharing and ecosystem impact
- [x] Full release bundle is published on HuggingFace; this sanitized public repo keeps lightweight release metadata/schema/card only.
- [x] License metadata for every case is present
      (`source_license_coverage == 1.0`).
- [x] Dataset license is CC-BY-4.0 (`LICENSE-DATA`); code license remains MIT.
- [x] Citation metadata is present (`CITATION.cff`).
- [x] Publish the release bundle to HuggingFace Dataset Hub: https://huggingface.co/datasets/qyxu1994/Biophys-Bridge.
- [ ] Optional: mirror the release bundle to OpenDataLab.
- [x] No secrets committed; `.env` is gitignored and `.env.example` is
      present.

## MinerU usage statement
- [x] [`reports/technical_report.md`](technical_report.md) section 7
      documents which MinerU component was used, the version/mode,
      input/output format, conversion approach, known limitations, and
      post-parse quality checks.

## Quality bar
- [x] 500 release-gate-reviewed cases across all six domains.
- [x] 10 contest gold samples, 30 extended-gold samples, and 50 held-out test
      cases include reviewed `expert_annotation` blocks with no draft markers.
- [x] `duplicate_rate == 0.0`, `source_license_coverage == 1.0`,
      `mineru_artifact_coverage == 1.0`,
      `evidence_coverage_rate >= 0.9`,
      `quantitative_evidence_rate >= 0.8`.
