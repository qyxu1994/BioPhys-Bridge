<img width="600" height="150" alt="Logo-BioPhys-Bridge" src="https://github.com/user-attachments/assets/ad220aa8-145e-4cb1-9916-2839d09fb6f6" />

**A physics-grounded Sci-Evo dataset for biological mechanism reasoning.**

Biophys-Bridge is an AI-for-Science dataset that connects quantitative
biophysical models, evidence extracted from open-access papers, biological
mechanism interpretation, and agent-facing scientific decision tasks.

- **Dataset Hub:** [qyxu1994/Biophys-Bridge](https://huggingface.co/datasets/qyxu1994/BioPhys-Bridge)
- **Technical report:** [reports/technical_report.md](reports/technical_report.md)
- **Dataset card:** [data/release/data_card.md](data/release/data_card.md)
- **License:** code is MIT; curated data and reports are CC-BY-4.0

## Release At A Glance

| Item | Value |
|---|---:|
| Release cases | 500 |
| Train / validation / test | 400 / 50 / 50 |
| Agent tasks | 1,517 |
| Cases with explicit failure/revision | 107 |
| Reviewed expert annotations | 81 |
| Contest gold / extended gold | 10 / 30 |
| Schema-valid rate | 1.000 |
| Evidence coverage rate | 1.000 |
| Quantitative-evidence rate | 1.000 |
| Source-license coverage | 1.000 |
| Duplicate rate | 0.000 |

## Why This Dataset Exists

Scientific agents need to do more than retrieve facts. In biophysics and
biology, useful reasoning often requires moving between equations, measured
quantities, assumptions, molecular or cellular mechanisms, and the next
experiment or computation.

Biophys-Bridge packages that reasoning pattern as a reusable Sci-Evo case:

```text
scientific question -> physical model -> quantitative evidence
-> biological mechanism -> physical interpretation -> next scientific decision
```

Each case is grounded in evidence blocks parsed from source papers and linked
through stable `evidence_id` references. The full 500-case JSONL release is
hosted on HuggingFace; this GitHub repository keeps the code, schema, reports,
metadata, benchmark summaries, and small mock samples needed for reproducible
inspection and development.

## What A Case Contains

Each release record includes:

- paper provenance: DOI/PMCID, title, license, and MinerU parse identifier;
- multimodal evidence blocks from text, tables, formulas, and figure/caption
  material;
- normalized quantitative evidence with canonical units and cited evidence IDs;
- a `biophysical_model` with equation, variables, assumptions, model family, and
  validity conditions;
- a `physical_interpretation` with directionality, caveats, and consistency
  notes;
- a `biological_mechanism` linking the physics to mechanism-level biology;
- a staged `sci_evo_trajectory` from research question to next step;
- agent tasks for derivation, mechanism reasoning, discrepancy explanation, and
  next-experiment design;
- reviewed `expert_annotation` fields for the 50 held-out test cases, 10 contest
  gold samples, and 30 extended-gold samples.

## Domain Coverage

The v1 release uses weighted coverage across six biophysical discovery domains:

| Domain | Cases |
|---|---:|
| `protein_ligand_binding` | 188 |
| `systems_biology_dynamics` | 126 |
| `conformational_dynamics_allostery` | 91 |
| `biomolecular_phase_separation` | 52 |
| `enzyme_kinetics` | 22 |
| `protein_stability_thermodynamics` | 21 |

Primary physics model families include binding thermodynamics, enzyme reaction
kinetics, folding stability thermodynamics, conformational/allosteric energy
landscapes, polymer phase-separation statistical mechanics, spatial transport,
and systems stochastic dynamics.

## Data Access

Install the optional HuggingFace dependency:

```bash
pip install datasets
```

Load the public JSONL splits directly:

```python
from datasets import load_dataset

repo_id = "qyxu1994/BioPhys-Bridge"
data_files = {
    "train": "data/release/splits/train.jsonl",
    "validation": "data/release/splits/validation.jsonl",
    "test": "data/release/splits/test.jsonl",
}

ds = load_dataset(repo_id, data_files=data_files)
print(ds)
print(ds["train"][0]["case_id"])
```

Expected split sizes:

```text
train: 400
validation: 50
test: 50
```

The GitHub repository intentionally does not track the full release JSONL files.
Those files live in the HuggingFace dataset repo. Local generated release files
under `data/release/*.jsonl` are ignored to keep GitHub lightweight.

## Repository Layout

```text
configs/                         Pipeline configuration templates
src/biophysevo/                  Extraction, validation, release, and eval code
data/release/                    Lightweight release metadata, schema, card, split manifest
data/samples/sample_cases.jsonl  Small mock samples for schema/tests
reports/                         Technical report, dataset card, appendix, checklist
results/aggregate/               Final benchmark aggregate summaries
tests/                           Unit and smoke tests
```

Not tracked in GitHub: raw PDFs, MinerU intermediates, run folders, full release
JSONL payloads, review queues, submission bundles, and HF upload staging files.

## Reproducibility

Set up the project:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Validate the mock samples:

```bash
python -m biophysevo.validate --input data/samples/sample_cases.jsonl
```

Run the focused public test suite:

```bash
PYTHONPATH=src python -m pytest \
  tests/test_agent_eval.py \
  tests/test_sample_cases_validate.py \
  tests/test_schema.py \
  tests/test_release.py \
  tests/test_data_card.py
```

Regenerate the JSON schema:

```bash
python -m biophysevo.schemas.case_schema --emit-json
```

Run the de-leaked lexical retrieval baseline on a local full release file:

```bash
python -m biophysevo.evaluation.run_agent_eval \
  --input data/release/biophys_bridge_evo_cases.jsonl \
  --model lexical_retrieval_baseline \
  --provider lexical \
  --run-dir runs/<timestamp>_agent_eval_lexical_retrieval_baseline
```

## Benchmark Summary

The evaluation harness is de-leaked: prompts do not include gold supporting
evidence IDs, and gold IDs are used only by the scorer after prediction.

| Model | Scope | Tasks | Overall | Evidence-id F1 | Answer token F1 |
|---|---|---:|---:|---:|---:|
| `lexical_retrieval_baseline` | full release | 1,517 | 0.114 | 0.216 | 0.070 |
| `gpt-4o-mini` | 50-case test split | 154 | 0.229 | 0.312 | 0.194 |

The lexical row is a deterministic retrieval/plumbing floor. The real-model row
is a held-out capability check over the test split.

## Quality Controls

The release pipeline enforces:

- schema validation through Pydantic and JSON Schema;
- evidence ID referential integrity for quantitative evidence and agent tasks;
- source license coverage checks for open-access provenance;
- unit normalization for quantitative evidence;
- duplicate case ID checks;
- semantic content gates that reject unresolved templates and weak task prompts;
- deterministic physics consistency notes where a supported closed-form relation
  applies;
- explicit separation between release-gate review status and human expert
  annotation coverage.

## Responsible Use

Biophys-Bridge is a scientific reasoning and evaluation dataset, not a substitute
for primary literature review. Users should verify important scientific claims
against the cited source papers before using them in research, engineering,
clinical, or safety-critical contexts.

## Citation

```bibtex
@dataset{xu2026biophysbridge,
  author    = {Xu, Qingyang},
  title     = {Biophys-Bridge: A Physics-Grounded Sci-Evo Dataset for Biological Mechanism Reasoning},
  year      = {2026},
  url       = {https://github.com/qyxu1994/BioPhys-Bridge},
  license   = {CC-BY-4.0}
}
```

## License

Repository code is released under the MIT License. The curated dataset metadata,
reports, and public dataset release are released under CC-BY-4.0. Upstream source
papers retain their original licenses, recorded per case in `source.license`.
