# Biophys-Bridge 竞赛提交技术报告

GitHub: https://github.com/qyxu1994/Biophys-Bridge 

HuggingFace Dataset: https://huggingface.co/datasets/qyxu1994/Biophys-Bridge

## 1. 数据集简介

**Biophys-Bridge** 是一个面向生物发现的物理模型驱动 Sci-Evo 数据集。当前发布子类型为 **Sci-Evo**。每条记录都是一个 **Physics-Grounded Scientific Evolution Case**：它把定量物理模型、从科学论文中抽取的证据、生物学机制解释，以及面向智能体的科学决策任务连接为一个结构化样本。

当前竞赛发布版本包含 **500 条通过自动化校验、grounding、来源许可和语义内容门控的样本**、**10 条竞赛金标样本**、**30 条扩展金标样本**，以及 **500 条 Sci-Evo 视图记录**。其中 **107 条样本显式包含 failure/revision 阶段**，作为最接近赛题“试错、失败分析、多步决策”要求的 Sci-Evo 核心子集；其余样本作为 evidence-grounded mechanism cases，为机制推理与下一步决策提供静态证据底座。另有 **81 条样本包含已审核的 expert_annotation 字段**：50 条 held-out test 样本、全部 10 条竞赛金标样本、全部 30 条扩展金标样本，以及 1 条扩展集合之外的历史金标审核记录。`quality.manual_review_status = "reviewed"` 表示样本通过发布门控；完整专家物理/生物学标注由 `expert_annotation` 覆盖率单独统计。

## 2. 数据集设计方案

本数据集的原始动机是：用定量物理模型增强生物学发现能力。发布集采用加权领域覆盖，而不是声称六个领域完全均衡。Biophys-Bridge 不只收集孤立的生物学事实，而是记录一种可复用的科学推理链条：

```text
科学问题 -> 定量物理模型 -> 证据 -> 物理解释 -> 生物机制 -> 智能体决策 / 下一步实验
```

数据设计将生物学领域和物理模型族分开建模。`domain` 表示生物学问题场景，`biophysical_model.model_family` 表示主方程和主决策所依赖的主要物理建模方法。若论文包含辅助物理模型，则写入 `secondary_model_families`。

Biophys-Bridge 同时也是一个跨模态证据对齐数据集：每个样本用稳定的 `evidence_id` 将文本、表格、公式、图/图注、标准化单位、方程变量、物理解释、生物机制和智能体决策连接起来。因此同一个对象既能支持 Sci-Align 式的多模态 grounding，也能支持 Sci-Evo 式的推理轨迹评测。

### 2.1 生物学领域分布

| 类别 | 数量 |
|---|---:|
| `protein_ligand_binding` | 188 |
| `systems_biology_dynamics` | 126 |
| `conformational_dynamics_allostery` | 91 |
| `biomolecular_phase_separation` | 52 |
| `enzyme_kinetics` | 22 |
| `protein_stability_thermodynamics` | 21 |

### 2.2 物理模型族分布

| 类别 | 数量 |
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

### 2.3 桥接类型分布

| 类别 | 数量 |
|---|---:|
| `binding_thermodynamics_to_binding_mechanism` | 188 |
| `systems_biology_dynamics_to_pathway_mechanism` | 126 |
| `conformational_dynamics_to_allosteric_mechanism` | 91 |
| `phase_separation_to_condensate_mechanism` | 52 |
| `enzyme_kinetics_to_catalytic_mechanism` | 22 |
| `folding_stability_thermodynamics_to_mutation_mechanism` | 21 |

## 3. 数据集结构说明与字段定义

Schema 的唯一可信来源是 `src/biophysevo/schemas/case_schema.py`；`data/release/biophys_bridge_schema.json` 由代码生成，不应手工修改。所有模型均禁止未知字段，跨字段约束由 Pydantic 的 model validator 强制执行。

| 字段 | 定义 |
|---|---|
| `case_id` | 每个物理模型驱动科学演化样本的稳定唯一标识符。 |
| `dataset_family / dataset_subtype / dataset_type` | 固定数据集身份：Biophys-Bridge / Sci-Evo / Sci-Evo。 |
| `domain` | Schema 支持的六个生物发现领域之一。 |
| `bridge_type` | 从物理模型类别到生物机制类别的领域专属桥接类型。 |
| `source` | 论文溯源信息，包括标题、DOI/PMCID、许可、来源 URL、MinerU 解析标识和证据完整性元数据。 |
| `evidence[]` | 由 MinerU 标准化文本、表格、公式和图像说明生成的稳定证据块；每个证据块都有 evidence_id。 |
| `quantitative_evidence[]` | 指标/数值/单位记录，保留原始单位和值以及标准化单位和值，并引用对应 evidence_id。 |
| `biophysical_model` | 模型名称、必填 model_family、可选 secondary_model_families、equation_latex、变量、假设和适用条件。 |
| `physical_interpretation` | 派生量、方向性、内部一致性检查和 caveats，用于连接模型与测量结果。 |
| `biological_mechanism` | 机制类型和解释文本，用于说明物理结果如何支持生物功能或表型机制。 |
| `sci_evo_trajectory[]` | 推理轨迹阶段，包括研究问题、假设、方法设计、定量观察、物理解释、失败/修订和下一步。 |
| `agent_tasks[]` | 训练/评估任务，包括 task_type、input、gold_answer、supporting_evidence_ids、required_reasoning_skills 和 allowed_tools。 |
| `expert_annotation` | 金标样本审核备注，包括物理推理、生物学推理、不确定性和审核者说明。 |
| `quality` | 校验状态、审核状态、评分、来源追踪、MinerU 产物覆盖和审核备注。 |

## 4. 数据来源与合规性

本发布版本来自具有 DOI 和/或 PMCID 溯源信息的开放获取科学论文。原始 PDF、MinerU 中间产物、LLM 响应和运行日志不随数据集发布。发布包只包含标准化 JSONL 记录、schema、元数据、数据卡和报告。

500 条发布样本的来源许可分布如下：

| 类别 | 数量 |
|---|---:|
| `CC-BY-4.0` | 490 |
| `CC0-1.0` | 10 |


构建过程中执行以下合规规则：

- 仅使用开放获取或发布兼容的数据源，主要为 CC-BY 或 CC0 许可变体。
- 在 `source` 字段中保留 DOI、PMCID、论文标题、许可、来源 URL 和 MinerU 解析标识。
- 不发布原始 PDF 或 MinerU 中间 payload。
- 禁止生成虚假科学数据、伪造实验结果、虚构方程、虚构测量值或无证据支持的机制解释。
- 证据不足的字段必须保持为 `null` 或被排除，不能编造。
- 任何未通过 grounding、内容质量、schema 校验或审核状态门控的候选样本均不得进入发布数据集。

## 5. 标注规范

标注遵循 evidence-only 原则。每个定量值必须引用 `evidence[]` 中的一个 `evidence_id`。每个 agent task 必须引用至少一个支持性证据 ID。物理标注记录模型、方程、假设和适用条件；生物学标注说明物理结果如何支持机制解释；Sci-Evo 轨迹记录从问题、证据、模型、解释到下一步决策的推理过程。

发布门控审核状态分布如下：

| 类别 | 数量 |
|---|---:|
| `reviewed` | 500 |


该状态不表示“500 条都完成专家标注”。它表示每条发布样本通过了 schema、证据链接、grounding、内容质量、许可、去重和发布导出检查。专家标注是显式字段并单独计数；金标样本在具备该专家层时会包含 `expert_annotation`，记录物理推理、生物学推理、不确定性和审核者备注。

## 6. 数据集构建方案

构建流程强调可追溯、可解析、可恢复和合规。

1. **来源获取**：从 Europe PMC 及其他开放获取元数据源构建候选池。每个候选包含 DOI/PMCID、标题、摘要、许可、来源 URL、领域猜测、模型族猜测和定量/模型关键词。
2. **批次选择**：按 100 篇论文为单位选择解析批次，并跟踪领域与模型族分布，尽量降低开放获取来源偏差。
3. **PDF 下载**：将 PDF 下载到 gitignore 的 `data/raw/pdf_batches/...` 目录。下载不会覆盖历史产物；失败写入 `download_report.jsonl`。
4. **MinerU 解析**：通过 MinerU API/local/dry-run 模式解析 PDF，并将原始 payload 保存在 gitignore 的中间目录中。
5. **标准化**：把 MinerU payload 转换为统一 parsed-doc 目录，包含 `document.md`、`document.json`、`evidence_blocks.jsonl` 和 `parse_metadata.json`。
6. **候选抽取**：优先使用正则方法从文本、表格、公式和图注中抽取候选证据。
7. **Evidence-only LLM 结构化**：可选 LLM 步骤只能使用提供的 evidence blocks；prompt 明确要求对证据不支持的字段返回 `null`。
8. **Schema 校验**：每条样本必须通过 Pydantic/JSON Schema 合约。
9. **内容质量门控**：拒绝模板标记、字符拆分词表、弱任务输入、弱答案、不规范工具/技能词表，以及缺少 `next_step` 的推理轨迹。
10. **Grounding 审核**：只有当定量值能在其引用的证据块中找到时才提升为 reviewed。只有在同一 case 中某个值唯一出现在另一个证据块时，才允许保守地修复 evidence_id 引用。
11. **物理一致性审计**：对每条发布记录运行确定性的物理一致性检查。审计结果写入 `physical_interpretation.consistency_check`；只有当已实现的热力学/动力学关系适用于该样本时，才计入关系级 pass rate。
12. **发布导出**：生成 JSONL 发布文件、元数据、schema、数据卡、金标样本、分层划分和 Sci-Evo 视图。

## 7. MinerU 使用方式

本数据集使用 MinerU 作为 PDF 解析引擎。API 解析由数据构建者在能够访问 MinerU API 与上传存储端点的 shell 中手动运行：

```bash
python scripts/run_mineru_api.py \
  --out-dir data/intermediate/mineru_api_batch_<batch_id> \
  'data/raw/pdf_batches/<batch_id>/pdfs/*.pdf'
```

该脚本从 `.env` 加载 `MINERU_API_KEY`，以 MinerU API 模式（项目配置记录为 MinerU v4/API mode）上传本地 PDF，轮询解析结果，并为每篇文档保存 `full.md` 和 `payload.json`。随后通过以下命令标准化输出：

```bash
python -m biophysevo.mineru.normalize \
  --input-dir data/intermediate/mineru_api_batch_<batch_id> \
  --out-dir data/intermediate/parsed_docs_real \
  --provenance data/raw/pdf_batches/<batch_id>/provenance.json \
  --run-dir runs/<timestamp>_normalize_<batch_id> \
  --resume
```

解析后审计会检查 manifest 中每个文档是否都有必需的标准化产物。缺失的解析目录或必需文件会被显式报告，绝不会静默丢弃。

运行时依赖和可选评测依赖已在 `pyproject.toml` 中固定版本，便于可复现实装（`pip install -e ".[dev]"`，需要时再安装 `[llm]` 或 `[hf]`）。

## 8. 质量评估方法

发布质量门控包括：

- **Schema 有效性**：每条发布样本必须通过生成的 JSON Schema。
- **证据覆盖率**：所有被引用的 `evidence_id` 必须能解析到证据块。
- **定量 grounding**：定量值必须出现在其引用的证据文本中；对 OCR 和科学计数法格式提供有限容错。
- **单位标准化**：保留原始单位和值，同时在支持时提供标准化单位和值。
- **许可覆盖率**：发布样本必须带有兼容的来源许可元数据。
- **内容质量**：阻止模板残留、空任务、弱任务、字符拆分词表以及缺少 next-step 的轨迹。
- **发布门控审核**：发布样本必须为 `reviewed`；专家标注由独立字段单独计数。
- **物理一致性审计**：每条发布样本均写入确定性审计说明；可适用关系级检查与审计覆盖率分开统计。
- **运行可恢复性**：主要阶段均在 `runs/` 中写入 checkpoint 和 metrics，便于中断后恢复。

主要发布元数据如下：

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

## 9. 发布文件

竞赛发布包包含：

- `data/release/biophys_bridge_evo_cases.jsonl`：500 条通过发布门控的 reviewed 样本。
- `data/release/biophys_bridge_10_gold_samples.jsonl`：竞赛要求的 10 条金标样本。
- `data/release/biophys_bridge_30_gold_samples.jsonl`：扩展金标样本集合。
- `data/release/biophys_bridge_sci_evo_view.jsonl`：下游使用的 Sci-Evo 投影视图。
- `data/release/splits/{train,validation,test}.jsonl`：按领域分层的确定性数据划分。
- `data/release/biophys_bridge_schema.json`：生成的 JSON Schema。
- `data/release/biophys_bridge_metadata.json`：发布指标和分布统计。
- `data/release/data_card.md`：数据卡。

## 10. 数据使用方式

`biophys_bridge_evo_cases.jsonl` 的每一行都是一个完整 JSON 对象。Python 使用示例：

```python
import json
from pathlib import Path

cases = [json.loads(line) for line in Path("data/release/biophys_bridge_evo_cases.jsonl").read_text().splitlines()]
print(len(cases))
print(cases[0]["biophysical_model"]["equation_latex"])
```

HuggingFace `datasets` 使用方式：

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

Agent-task baseline 评测入口：

```bash
python -m biophysevo.evaluation.run_agent_eval \
  --input data/release/biophys_bridge_evo_cases.jsonl \
  --model lexical_retrieval_baseline \
  --provider lexical \
  --run-dir runs/<timestamp>_agent_eval_lexical_retrieval_baseline
```

当前评测 prompt 已去除泄漏：prompt 只展示不读取 `task.supporting_evidence_ids` 而选出的候选证据块，并要求模型同时返回 `answer` 和 `supporting_evidence_ids`。金标 evidence IDs 仅在评分器中使用。

当前 benchmark 结果如下：

| 模型 | 范围 | 任务数 | 平均总分 | Evidence-id F1 | Answer token F1 | 定位 |
|---|---|---:|---:|---:|---:|---|
| `lexical_retrieval_baseline` | 全量发布集 | 1517 | 0.114 | 0.216 | 0.070 | 离线检索/管线下限。 |
| `gpt-4o-mini` | 50-case test split | 154 | 0.229 | 0.312 | 0.194 | 真实模型 held-out 能力检查。 |

`lexical_retrieval_baseline` 不被当作科学推理模型；它是确定性的离线下限，用于验证 loader、评分器和证据选择链路。`gpt-4o-mini` 的 test split 结果是能力 benchmark，在同一去泄漏评分协议下优于离线下限。

推荐用途：

- 训练和评估具备物理模型驱动生物推理能力的科学智能体。
- 测试模型能否连接方程、单位、定量证据和生物机制。
- 基于证据生成下一步实验或计算决策。
- 审计科学抽取和推理系统中的 hallucination 行为。
- 构建以证据链接科学 case 为核心的检索增强系统。

## 11. 数据集应用场景

Biophys-Bridge 可用于以下方向：

- 蛋白-配体结合与热力学解释；
- 酶动力学与催化机制推理；
- 蛋白稳定性、折叠热力学与突变效应；
- 构象动力学与变构机制推断；
- 生物分子相分离与凝聚体形成；
- 系统生物学动力学、随机模型与通路决策。

## 12. 局限性与负责任使用

Biophys-Bridge 是经过策展的数据集，不应替代对原始论文的阅读。在做出实验、临床或工程决策前，用户应查阅被引用的原始论文。未通过 grounding 的候选样本被有意排除在发布集之外。部分 PDF OCR 产生的文本瑕疵会保留在证据文本中，这是为了保持到解析产物的可追溯性。

## 13. 完整数据样例

为保证技术报告可读性，正文中保留紧凑样例表。完整的 10 条样例记录可在以下两个位置查看：

- 完整 JSONL 金标样本：`data/release/biophys_bridge_10_gold_samples.jsonl`
- 包含同样 10 条完整 JSON 记录的 Markdown 附录：`reports/appendix_10_complete_samples_zh.md`

10 条完整样例的紧凑概览如下：

| # | case_id | 领域 | 模型族 | 论文/来源 | 主要方程 | 任务数 |
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
