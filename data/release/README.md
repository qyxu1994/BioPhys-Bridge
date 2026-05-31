---
license: cc-by-4.0
task_categories:
  - question-answering
  - text-generation
  - table-question-answering
language:
  - en
tags:
  - ai4science
  - biophysics
  - biology
  - scientific-reasoning
  - physics-grounded
  - agent-evaluation
  - evidence-grounded
  - multimodal-science
  - jsonl
pretty_name: Biophys-Bridge (Sci-Evo)
size_categories:
  - 100<n<1K
---

# Biophys-Bridge (Sci-Evo)

Biophys-Bridge is a physics-grounded scientific reasoning dataset for AI-for-Science agents. The dataset subtype, Sci-Evo, represents each record as a **Physics-Grounded Scientific Evolution Case** linking:

```text
physical model -> quantitative evidence -> biological mechanism -> agent decision
```

Each case is built from open-access scientific literature and includes evidence-linked text, tables, formulas, figure/caption blocks, normalized quantitative measurements, biophysical model fields, biological mechanism interpretation, Sci-Evo trajectory steps, and agent-facing tasks with gold answers.

## Dataset Summary

The current release contains **500 cases** across six biophysical discovery domains:

- protein-ligand binding
- enzyme kinetics
- protein stability and folding thermodynamics
- conformational dynamics and allostery
- biomolecular phase separation
- systems biology dynamics

The dataset is designed for:

- evaluating scientific agents on evidence-grounded mechanism reasoning;
- testing whether models can connect equations, units, quantitative evidence, and biology;
- training or benchmarking next-experiment / next-computation decision tasks;
- studying hallucination resistance in scientific reasoning pipelines.

## Files

| File | Description |
|---|---|
| `biophys_bridge_evo_cases.jsonl` | Full 500-case release. |
| `biophys_bridge_10_gold_samples.jsonl` | Top 10 gold samples, all with expert annotations. |
| `biophys_bridge_30_gold_samples.jsonl` | Extended 30-case gold-review subset, all with expert annotations. |
| `biophys_bridge_sci_evo_view.jsonl` | Compact Sci-Evo projection for downstream evaluation. |
| `biophys_bridge_metadata.json` | Aggregate quality, modality, split, and coverage metrics. |
| `biophys_bridge_schema.json` | Generated JSON Schema for the case format. |
| `splits/train.jsonl` | Deterministic domain-stratified train split. |
| `splits/validation.jsonl` | Deterministic domain-stratified validation split. |
| `splits/test.jsonl` | Deterministic domain-stratified test split. |
| `splits/split_manifest.json` | Split counts and strategy. |

## Loading

The JSONL files can be read directly:

```python
import json
from pathlib import Path

cases = [
    json.loads(line)
    for line in Path("data/release/biophys_bridge_evo_cases.jsonl").read_text().splitlines()
    if line.strip()
]

print(len(cases))
print(cases[0]["biophysical_model"]["equation_latex"])
```

HuggingFace `datasets` can load the JSONL splits directly:

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

## Schema Overview

Each case contains:

- `case_id`: stable unique case identifier.
- `dataset_type`: fixed to `Sci-Evo`.
- `dataset_family`: fixed to `Biophys-Bridge`.
- `dataset_subtype`: fixed to `Sci-Evo`.
- `domain`: biological discovery domain.
- `bridge_type`: domain-specific physics-to-biology bridge.
- `source`: paper provenance, DOI/PMCID/source URL, source license, and MinerU parse identifier.
- `evidence[]`: MinerU-normalized text/table/formula/figure/caption blocks with stable `evidence_id`s.
- `quantitative_evidence[]`: metric/value/unit records with normalized units and evidence citations.
- `biophysical_model`: model name, model family, equation, variables, assumptions, and validity conditions.
- `physical_interpretation`: derived quantity, directionality, caveats, and deterministic physics-audit note.
- `biological_mechanism`: mechanism type and structure-function interpretation.
- `sci_evo_trajectory[]`: reasoning stages from research question to next step.
- `failure_or_revision`: explicit failure/revision stage when present in the source.
- `agent_tasks[]`: agent-facing tasks with gold answers and supporting evidence IDs.
- `expert_annotation`: curator physics/biology reasoning for gold samples where available.
- `quality`: release-gate status and quality score.

The canonical JSON Schema is included as `biophys_bridge_schema.json`.

## Splits

The release includes deterministic domain-stratified splits:

| Split | Cases |
|---|---:|
| train | 400 |
| validation | 50 |
| test | 50 |

The split strategy is recorded in `splits/split_manifest.json`.

## Baseline

The repository includes a resumable agent-task evaluation harness. The prompt is de-leaked: candidate evidence is selected without reading gold `supporting_evidence_ids`, and the scorer uses gold IDs only after prediction.

```bash
python -m biophysevo.evaluation.run_agent_eval \
  --input data/release/biophys_bridge_evo_cases.jsonl \
  --model lexical_retrieval_baseline \
  --provider lexical \
  --run-dir runs/<timestamp>_agent_eval_lexical_retrieval_baseline
```

| Model | Scope | Tasks | Mean overall score | Evidence-id F1 | Answer token F1 |
|---|---|---:|---:|---:|---:|
| `lexical_retrieval_baseline` | full release | 1517 | 0.114 | 0.216 | 0.070 |
| `gpt-4o-mini` | 50-case test split | 154 | 0.229 | 0.312 | 0.194 |

The lexical row is a deterministic retrieval/plumbing floor. The OpenAI row is a held-out real-model capability check. The 50 held-out test cases, 10 contest gold samples, and 30 extended-gold samples now include reviewed `expert_annotation` blocks.

## Quality Metrics

Selected release metrics:

- `schema_valid_rate`: 1.000
- `evidence_coverage_rate`: 1.000
- `quantitative_evidence_rate`: 1.000
- `unit_normalization_success_rate`: 1.000
- `source_license_coverage`: 1.000
- `manual_review_pass_rate`: 1.000
- `expert_annotation_n`: 81
- `expert_annotation_draft_n`: 0
- `release_expert_annotation_coverage`: 0.162
- `test_expert_annotation_coverage`: 1.000
- `equation_bearing_coverage`: 1.000
- `physics_consistency_audit_coverage`: 1.000
- `physics_consistency_checked_rate`: 0.020
- `physics_consistency_pass_rate`: 0.800
- `mean_modalities_per_case`: 2.944
- `cases_with_3plus_modalities_rate`: 0.804
- `failure_or_revision_n`: 107
- `cases_with_failure_or_revision_rate`: 0.214

See `biophys_bridge_metadata.json` for the complete metric set.

## Licensing

The curated Biophys-Bridge / Sci-Evo dataset is released under **CC-BY-4.0**.

Upstream source papers retain their original licenses, recorded per case in `source.license`. Raw PDFs and MinerU intermediate artifacts are not redistributed.

Repository code is licensed separately under MIT in the source GitHub repository.

## Citation

If you use Biophys-Bridge, please cite:

```bibtex
@dataset{xu2026biophysbridge,
  author    = {Xu, Qingyang},
  title     = {Biophys-Bridge: A Physics-Grounded Sci-Evo Dataset for Biological Mechanism Reasoning},
  year      = {2026},
  url       = {https://github.com/qyxu1994/Biophys-Bridge},
  license   = {CC-BY-4.0}
}
```

## Responsible Use

Biophys-Bridge is a scientific reasoning and evaluation dataset, not a substitute for primary literature review. Users should verify important scientific claims against the cited source papers before using them in research, engineering, clinical, or safety-critical contexts.
