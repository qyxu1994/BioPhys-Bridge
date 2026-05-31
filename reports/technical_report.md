# Biophys-Bridge Contest Submission Technical Report

GitHub: https://github.com/qyxu1994/Biophys-Bridge 

HuggingFace Dataset: https://huggingface.co/datasets/qyxu1994/Biophys-Bridge

## 1. Dataset Introduction

**Biophys-Bridge** is a physics-grounded Sci-Evo dataset for biological discovery. The release subtype is **Sci-Evo** and each record is a **Physics-Grounded Scientific Evolution Case**: a structured link from a quantitative physical model, to evidence extracted from scientific papers, to a biological mechanism, and finally to an agent-facing scientific decision task.

The current contest release contains **500 cases that passed automated validation, grounding, source-license, and semantic content gates**, **10 contest gold samples**, **30 extended gold samples**, and **500 Sci-Evo view records**. **107 cases explicitly include a failure/revision stage**; these are the core Sci-Evo subset for trial-and-error, failure analysis, and multi-step decision evaluation. The remaining records are framed as evidence-grounded mechanism cases that provide the static substrate for mechanism reasoning and next-step decisions. **81 cases now include reviewed expert_annotation blocks**: the 50 held-out test cases, all 10 contest gold samples, all 30 extended-gold samples, plus one legacy gold-review record outside the extended subset. The `quality.manual_review_status = "reviewed"` flag means the case passed release gates; full expert physics/biology annotation is tracked separately by `expert_annotation` coverage.

## 2. Dataset Design

The dataset is designed around the original motivation: improving biological discovery with quantitative physics models. The 500-case release uses weighted domain coverage rather than claiming perfectly balanced six-domain coverage. Instead of collecting isolated biological facts, Biophys-Bridge records a reusable reasoning pattern:

```text
scientific question -> quantitative physical model -> evidence -> physical interpretation -> biological mechanism -> agent decision / next step
```

The design separates biological domain from physics model family. `domain` captures the biological problem setting, while `biophysical_model.model_family` captures the primary physical modeling strategy used by the main equation and decision. Secondary model families can be listed when a paper uses supporting physics.

Biophys-Bridge is also a cross-modal evidence-alignment dataset: a case binds text, table, formula, figure/caption, normalized units, equation variables, physical interpretation, biological mechanism, and agent decision through stable `evidence_id`s. That bridge lets the same object serve Sci-Align-style multimodal grounding and Sci-Evo-style reasoning-trajectory evaluation.

### 2.1 Biological Domains

| Category | Count |
|---|---:|
| `protein_ligand_binding` | 188 |
| `systems_biology_dynamics` | 126 |
| `conformational_dynamics_allostery` | 91 |
| `biomolecular_phase_separation` | 52 |
| `enzyme_kinetics` | 22 |
| `protein_stability_thermodynamics` | 21 |

### 2.2 Physics Model Families

| Category | Count |
|---|---:|
| `binding_thermodynamics` | 185 |
| `systems_stochastic_dynamics` | 128 |
| `conformational_allostery_energy_landscape` | 93 |
| `polymer_phase_separation_statistical_mechanics` | 41 |
| `enzyme_reaction_kinetics` | 23 |
| `folding_stability_thermodynamics` | 20 |
| `spatial_transport_electrostatics` | 6 |
| `evolutionary_fitness_landscape` | 2 |
| `mechanical_force_response` | 2 |

### 2.3 Bridge Types

| Category | Count |
|---|---:|
| `binding_thermodynamics_to_binding_mechanism` | 188 |
| `systems_biology_dynamics_to_pathway_mechanism` | 126 |
| `conformational_dynamics_to_allosteric_mechanism` | 91 |
| `phase_separation_to_condensate_mechanism` | 52 |
| `enzyme_kinetics_to_catalytic_mechanism` | 22 |
| `folding_stability_thermodynamics_to_mutation_mechanism` | 21 |

## 3. Dataset Structure and Field Definitions

The source-of-truth schema is `src/biophysevo/schemas/case_schema.py`; `data/release/biophys_bridge_schema.json` is generated from it and should not be hand-edited. Unknown fields are forbidden. Cross-field invariants are enforced in Pydantic model validators.

| Field | Definition |
|---|---|
| `case_id` | Stable unique identifier for one physics-grounded scientific evolution case. |
| `dataset_family / dataset_subtype / dataset_type` | Fixed dataset identity: Biophys-Bridge / Sci-Evo / Sci-Evo. |
| `domain` | One of six biological discovery domains supported by the schema. |
| `bridge_type` | The domain-specific bridge from a physical model class to a biological mechanism class. |
| `source` | Paper provenance: title, DOI/PMCID, license, source URL, MinerU parse identifier, and evidence-completeness metadata. |
| `evidence[]` | Stable evidence blocks from MinerU-normalized text, tables, formulas, and figures. Each block has an evidence_id. |
| `quantitative_evidence[]` | Metric/value/unit records with raw and normalized units, each citing an evidence_id. |
| `biophysical_model` | Model name, required model_family, optional secondary_model_families, equation_latex, variables, assumptions, and validity conditions. |
| `physical_interpretation` | Derived quantity, directionality, consistency check, and caveats linking the model to measurements. |
| `biological_mechanism` | Mechanism type and explanatory text linking the physical result to biological function or phenotype. |
| `sci_evo_trajectory[]` | Reasoning trajectory stages: research question, hypothesis, method design, quantitative observation, biophysical interpretation, failure/revision when present, and next step. |
| `agent_tasks[]` | Training/evaluation tasks with task_type, input, gold_answer, supporting_evidence_ids, required_reasoning_skills, and allowed_tools. |
| `expert_annotation` | Gold-sample review notes: physics reasoning, biological reasoning, uncertainty, and reviewer notes when available. |
| `quality` | Validation status, review status, score, source trace, MinerU artifact coverage, and reviewer notes. |

## 4. Data Sources and Compliance

The release is built from open-access scientific papers with DOI and/or PMCID provenance. Raw PDFs, MinerU intermediates, LLM responses, and run logs are not shipped. The dataset ships only normalized JSONL records, schema files, metadata, a dataset card, and reports.

Source license distribution in the 500-case release:

| Category | Count |
|---|---:|
| `CC-BY-4.0` | 490 |
| `CC0-1.0` | 10 |


Compliance rules used during construction:

- Use only open-access or release-compatible source records, primarily CC-BY or CC0 variants.
- Preserve DOI, PMCID, title, license, and MinerU parse identifiers in `source`.
- Do not redistribute raw PDFs or MinerU intermediate payloads.
- Do not fabricate scientific measurements, equations, experimental outcomes, or unsupported mechanisms.
- Unsupported fields must remain `null` or be excluded rather than invented.
- Any candidate that fails grounding, content quality, schema validation, or review status is excluded from the shipped release.

## 5. Annotation Specification

Annotation follows an evidence-only protocol. Each quantitative value must cite an `evidence_id` from `evidence[]`. Each agent task must cite at least one supporting evidence ID. The physics annotation records the governing model, equation, assumptions, and validity conditions. The biological annotation explains how the physical result supports a mechanism. The Sci-Evo trajectory captures the reasoning steps that connect question, evidence, model, interpretation, and next-step decision.

The release-gate review statuses are:

| Category | Count |
|---|---:|
| `reviewed` | 500 |


This status should not be read as "500 expert-annotated cases." It means each shipped case passed automated schema, evidence-link, grounding, content-quality, license, duplicate, and release-export checks. Expert annotation is explicit and separately counted: gold samples carry `expert_annotation` fields for physics reasoning, biological reasoning, uncertainty, and reviewer notes when that expert layer is present.

## 6. Dataset Construction Pipeline

The construction pipeline is designed to be traceable, parseable, resumable, and compliant.

1. **Source acquisition**: build an open-access candidate pool from Europe PMC and related OA-compatible metadata sources. Each candidate includes DOI/PMCID, title, abstract, license, source URL, domain guess, model-family guess, and quantitative/model keywords.
2. **Batch selection**: choose balanced 100-paper parse batches while tracking domain and model-family distributions to reduce OA source bias.
3. **PDF download**: download PDFs into gitignored `data/raw/pdf_batches/...` folders. Downloads never overwrite previous artifacts; failures are written to `download_report.jsonl`.
4. **MinerU parsing**: parse PDFs with the MinerU API/local/dry-run modes while keeping raw payloads in gitignored intermediate folders.
5. **Normalization**: convert MinerU payloads to canonical parsed-document folders containing `document.md`, `document.json`, `evidence_blocks.jsonl`, and `parse_metadata.json`.
6. **Candidate extraction**: run regex-first extraction over parsed text, tables, formulas, and figure captions.
7. **Evidence-only LLM structuring**: optional LLM enrichment is restricted to provided evidence blocks. The prompt instructs the model to return `null` for unsupported fields.
8. **Schema validation**: validate every case against the Pydantic/JSON Schema contract.
9. **Content-quality gate**: reject unresolved template markers, character-split vocabularies, weak task prompts, weak answers, malformed tool/skill vocabularies, and missing `next_step` trajectory stages.
10. **Grounding audit**: promote only cases whose quantitative values can be found in their cited evidence blocks. Conservative evidence recitation repair is allowed only when a value appears in exactly one alternative evidence block in the same case.
11. **Physics audit**: run deterministic physics-consistency checks over every shipped record. The audit is written into `physical_interpretation.consistency_check`; relation-level pass rate is reported only for cases where an implemented thermodynamic/kinetic relation applies.
12. **Release export**: write JSONL release files, metadata, schema, dataset card, gold samples, stratified splits, and Sci-Evo view.

## 7. MinerU Usage

MinerU is used as the PDF parsing engine. API parsing was run manually by the dataset builder from a shell with access to the MinerU API and upload storage endpoints:

```bash
python scripts/run_mineru_api.py \
  --out-dir data/intermediate/mineru_api_batch_<batch_id> \
  'data/raw/pdf_batches/<batch_id>/pdfs/*.pdf'
```

The standalone API script loads `MINERU_API_KEY` from `.env`, uploads local PDFs to MinerU API mode (the project config records this as MinerU v4/API mode), polls for completion, and stores one `full.md` and `payload.json` per document in a gitignored intermediate folder. Normalization then uses:

```bash
python -m biophysevo.mineru.normalize \
  --input-dir data/intermediate/mineru_api_batch_<batch_id> \
  --out-dir data/intermediate/parsed_docs_real \
  --provenance data/raw/pdf_batches/<batch_id>/provenance.json \
  --run-dir runs/<timestamp>_normalize_<batch_id> \
  --resume
```

Post-parse audits check that every manifest document has required normalized artifacts. Missing parse folders or missing required files are reported explicitly and are never silently dropped.

Runtime and optional evaluation dependencies are pinned in `pyproject.toml` for reproducible installs (`pip install -e ".[dev]"`, plus `[llm]` or `[hf]` when needed).

## 8. Quality Assessment

The release quality gates are intentionally strict:

- **Schema validity**: every shipped case validates under the generated JSON Schema.
- **Evidence coverage**: every cited `evidence_id` resolves to an evidence block.
- **Quantitative grounding**: quantitative values must be present in the cited evidence text, allowing modest formatting tolerance for OCR and scientific notation.
- **Unit normalization**: raw units and normalized units are retained when normalization is supported.
- **License coverage**: shipped cases require release-compatible source license metadata.
- **Content quality**: template markers, empty or weak agent tasks, character-split vocabularies, and missing next-step stages are blocked.
- **Release-gate review**: shipped cases must be marked `reviewed`; expert annotation remains a separate counted field.
- **Physics audit**: every shipped case receives a deterministic audit note; applicable relation-level checks are counted separately from audit coverage.
- **Run recoverability**: all major stages write resumable checkpoints and metrics under `runs/`.

Selected release metadata:

```json
{
  "agent_task_type_counts": {
    "derivation": 355,
    "discrepancy_explanation": 279,
    "mechanism_from_evidence": 480,
    "next_experiment_design": 403
  },
  "built_n": 500,
  "cases_with_3plus_modalities_rate": 0.804,
  "cases_with_failure_or_revision_rate": 0.214,
  "content_quality_failures": [],
  "domain_counts": {
    "biomolecular_phase_separation": 52,
    "conformational_dynamics_allostery": 91,
    "enzyme_kinetics": 22,
    "protein_ligand_binding": 188,
    "protein_stability_thermodynamics": 21,
    "systems_biology_dynamics": 126
  },
  "duplicate_case_ids": [],
  "duplicate_rate": 0.0,
  "equation_bearing_coverage": 1.0,
  "evidence_coverage_rate": 1.0,
  "evidence_modality_counts": {
    "figure": 4987,
    "formula": 496,
    "table": 1507,
    "text": 128601
  },
  "excluded_below_score": 0,
  "excluded_content_quality": 0,
  "excluded_not_reviewed": 0,
  "exclusion_counts_reconciled": true,
  "expert_annotation_draft_n": 0,
  "expert_annotation_n": 81,
  "extended_gold_expert_annotation_coverage": 1.0,
  "extended_gold_expert_annotation_n": 30,
  "extended_gold_n": 30,
  "failure_or_revision_n": 107,
  "gold_expert_annotation_coverage": 1.0,
  "gold_expert_annotation_n": 10,
  "gold_n": 10,
  "manual_review_pass_rate": 1.0,
  "mean_modalities_per_case": 2.944,
  "min_quality_score": 0.8,
  "mineru_artifact_coverage": 1.0,
  "n_raw": 500,
  "n_valid": 500,
  "physics_consistency_audit_coverage": 1.0,
  "physics_consistency_checked_rate": 0.02,
  "physics_consistency_pass_rate": 0.8,
  "physics_model_family_counts": {
    "binding_thermodynamics": 185,
    "conformational_allostery_energy_landscape": 93,
    "enzyme_reaction_kinetics": 23,
    "evolutionary_fitness_landscape": 2,
    "folding_stability_thermodynamics": 20,
    "mechanical_force_response": 2,
    "polymer_phase_separation_statistical_mechanics": 41,
    "spatial_transport_electrostatics": 6,
    "systems_stochastic_dynamics": 128
  },
  "quantitative_evidence_rate": 1.0,
  "release_content_quality_pass_rate": 1.0,
  "release_expert_annotation_coverage": 0.162,
  "release_finalized_at": "2026-05-31",
  "release_n": 500,
  "schema_valid_rate": 1.0,
  "sci_evo_completeness_score": 0.8828571428571428,
  "secondary_model_family_counts": {
    "binding_thermodynamics": 56,
    "conformational_allostery_energy_landscape": 12,
    "enzyme_reaction_kinetics": 26,
    "evolutionary_fitness_landscape": 8,
    "mechanical_force_response": 12,
    "polymer_phase_separation_statistical_mechanics": 1,
    "spatial_transport_electrostatics": 9,
    "systems_stochastic_dynamics": 42
  },
  "shipped_n": 500,
  "source_license_coverage": 1.0,
  "source_n_raw": 500,
  "source_n_valid": 500,
  "split_counts": {
    "test": 50,
    "train": 400,
    "validation": 50
  },
  "split_strategy": "deterministic stratified by domain; case_id-sorted within each domain",
  "test_expert_annotation_coverage": 1.0,
  "test_expert_annotation_n": 50,
  "unit_normalization_success_rate": 1.0
}
```

## 9. Release Files

The contest bundle is centered on:

- `data/release/biophys_bridge_evo_cases.jsonl`: 500 release-gate-reviewed cases.
- `data/release/biophys_bridge_10_gold_samples.jsonl`: contest-required top 10 gold samples.
- `data/release/biophys_bridge_30_gold_samples.jsonl`: extended gold sample set.
- `data/release/biophys_bridge_sci_evo_view.jsonl`: Sci-Evo projection for downstream use.
- `data/release/splits/{train,validation,test}.jsonl`: deterministic domain-stratified splits.
- `data/release/biophys_bridge_schema.json`: generated JSON Schema.
- `data/release/biophys_bridge_metadata.json`: release metrics and distribution counts.
- `data/release/data_card.md`: dataset card.

## 10. Data Usage

Each line of `biophys_bridge_evo_cases.jsonl` is a complete JSON object. Example Python usage:

```python
import json
from pathlib import Path

cases = [json.loads(line) for line in Path("data/release/biophys_bridge_evo_cases.jsonl").read_text().splitlines()]
print(len(cases))
print(cases[0]["biophysical_model"]["equation_latex"])
```

HuggingFace `datasets` usage:

```python
from datasets import load_dataset

data_files = {
    "train": "data/release/splits/train.jsonl",
    "validation": "data/release/splits/validation.jsonl",
    "test": "data/release/splits/test.jsonl",
}

dataset = load_dataset("json", data_files=data_files)
print(dataset["train"][0]["case_id"])
```

Agent-task evaluation harness:

```bash
python -m biophysevo.evaluation.run_agent_eval \
  --input data/release/biophys_bridge_evo_cases.jsonl \
  --model lexical_retrieval_baseline \
  --provider lexical \
  --run-dir runs/<timestamp>_agent_eval_lexical_retrieval_baseline
```

The benchmark prompt is intentionally de-leaked: it shows candidate evidence blocks selected without reading `task.supporting_evidence_ids`, then asks the model to return both `answer` and `supporting_evidence_ids`. The gold evidence IDs are used only by the scorer.

Current benchmark results:

| Model | Scope | Tasks | Mean overall | Evidence-id F1 | Answer token F1 | Role |
|---|---|---:|---:|---:|---:|---|
| `lexical_retrieval_baseline` | full release | 1517 | 0.114 | 0.216 | 0.070 | Offline retrieval/plumbing floor. |
| `gpt-4o-mini` | 50-case test split | 154 | 0.229 | 0.312 | 0.194 | Real-model held-out capability check. |

The lexical row is not presented as a reasoning model; it is a deterministic floor that verifies loader, scoring, and evidence-selection plumbing. The real-model test-split row is the capability benchmark and shows that a model with scientific language ability improves over the offline floor under the same de-leaked scoring protocol.

Recommended uses:

- Training and evaluating scientific agents on physics-grounded biological reasoning.
- Testing whether models can connect equations, units, quantitative evidence, and mechanisms.
- Generating next-experiment or next-computation decisions from evidence.
- Auditing hallucination behavior in scientific extraction and reasoning systems.
- Building retrieval-augmented systems over evidence-linked scientific cases.

## 11. Application Scenarios

Biophys-Bridge supports applications in:

- protein-ligand binding and thermodynamic interpretation;
- enzyme kinetics and catalytic mechanism reasoning;
- protein stability, folding thermodynamics, and mutation effects;
- conformational dynamics and allosteric mechanism inference;
- biomolecular phase separation and condensate formation;
- systems biology dynamics, stochastic models, and pathway decision-making.

## 12. Limitations and Responsible Use

Biophys-Bridge is a curated dataset, not a replacement for reading the original paper. Users should consult the cited source papers before making laboratory or clinical decisions. Failed-grounding candidates are intentionally excluded from the release. Some OCR artifacts from scientific PDFs remain visible in evidence text, but they are preserved to maintain traceability to parsed source artifacts.

## 13. Complete Data Samples

The report keeps the sample section compact for readability. The release provides at least 10 complete examples in two machine-readable / reviewable locations:

- Complete JSONL gold samples: `data/release/biophys_bridge_10_gold_samples.jsonl`
- Markdown appendix with the same 10 complete JSON records: `reports/appendix_10_complete_samples.md`

Compact overview of the 10 complete samples:

| # | case_id | Domain | Model family | Paper/source | Main equation | Tasks |
|---:|---|---|---|---|---|---:|
| 1 | `biophysevo_000004` | `biomolecular_phase_separation` | `polymer_phase_separation_statistical_mechanics` | Sequence determinants of protein phase behavior from a coarse-grained model | `E_{ij}(r) = \frac{q_i q_j}{4 \pi D r} \exp[-r/\kappa]` | 4 |
| 2 | `biophysevo_000006` | `conformational_dynamics_allostery` | `conformational_allostery_energy_landscape` | Insights into the activation mechanism of class I HDAC complexes by inositol phosphates | `K_{d} = \frac{[HDAC][InsP]}{[HDAC-InsP]}` | 4 |
| 3 | `biophysevo_000021` | `enzyme_kinetics` | `enzyme_reaction_kinetics` | UniKP: a unified framework for the prediction of enzyme kinetic parameters | `k_{cat} = \frac{V_{max}}{[E_{total}]}, K_m = \left[\text{substrate conc. at half } V_{m...` | 4 |
| 4 | `biophysevo_000023` | `enzyme_kinetics` | `enzyme_reaction_kinetics` | Studies of a ring-cleaving dioxygenase illuminate the role of cholesterol metabolism in... | `v = \frac{k_{cat}[S]}{K_m + [S]}` | 3 |
| 5 | `biophysevo_000025` | `enzyme_kinetics` | `enzyme_reaction_kinetics` | Single-mutation fitness landscapes for an enzyme on multiple substrates reveal specific... | `\zeta _ { i } = \log _ { 2 } \left( \frac { \mu _ { \mathrm { s , i } } } { \mu _ { \ma...` | 2 |
| 6 | `biophysevo_000031` | `enzyme_kinetics` | `enzyme_reaction_kinetics` | Potent Allosteric Dengue Virus NS5 Polymerase Inhibitors: Mechanism of Action and Resis... | `\text{Activity} = \frac{V_{\max}[S]}{K_m + [S]} \times (1 + \frac{[I]}{K_i})^{-1}` | 4 |
| 7 | `biophysevo_000037` | `conformational_dynamics_allostery` | `conformational_allostery_energy_landscape` | Change in allosteric network affects binding affinities of PDZ domains: analysis throug... | `\begin{array} { l } { { \displaystyle \sum _ { i } f _ { i j } \cos \alpha _ { i j } ^ ...` | 3 |
| 8 | `biophysevo_000040` | `conformational_dynamics_allostery` | `conformational_allostery_energy_landscape` | Autoregulation of GPCR signalling through the third intracellular loop | `\mathrm{FRET}_{\mathrm{eff}} = 1 - \frac{\tau_{\mathrm{FRET}}}{\tau_{\mathrm{donor}}} +...` | 2 |
| 9 | `biophysevo_000047` | `systems_biology_dynamics` | `systems_stochastic_dynamics` | A canonical model of multistability and scale-invariance in biological systems | `\frac{d r}{d t} = -r^5 + \lambda r^3 + \beta r + \eta [(1 - \rho) \xi_1(t) + \rho r \xi...` | 4 |
| 10 | `biophysevo_batch001_000010` | `biomolecular_phase_separation` | `systems_stochastic_dynamics` | Personalized neoantigen vaccine and pembrolizumab in advanced hepatocellular carcinoma:... | `T_{response} = f(N, A_{affinity})` | 3 |
