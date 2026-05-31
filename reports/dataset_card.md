# Biophys-Bridge Dataset Card

## Name
Biophys-Bridge (Sci-Evo dataset subtype: Sci-Evo) — 500 cases.

## Intended use
Training and evaluating AI research agents on physics-grounded scientific
reasoning: each case is a physics-grounded Scientific Evolution Case linking a
physical model -> quantitative evidence -> biological mechanism -> agent
decision (research question -> physical model -> quantitative observation ->
biophysical interpretation -> mechanism -> next-step decision). Suitable for
AGI4S evaluation, scientific-reasoning benchmarks, and AI research agents.

## Domains in this release
This release covers 6 of the 6 schema-supported v1 domains
(domain is assigned per paper from its actual content):

- `protein_ligand_binding`: 188 case(s)
- `systems_biology_dynamics`: 126 case(s)
- `conformational_dynamics_allostery`: 91 case(s)
- `biomolecular_phase_separation`: 52 case(s)
- `enzyme_kinetics`: 22 case(s)
- `protein_stability_thermodynamics`: 21 case(s)

## Physics model families
The primary `biophysical_model.model_family` records the physics model family
used by the main equation and agent decision; supporting families, when
present, are listed in `secondary_model_families`.

- `binding_thermodynamics`: 185 case(s)
- `systems_stochastic_dynamics`: 128 case(s)
- `conformational_allostery_energy_landscape`: 93 case(s)
- `polymer_phase_separation_statistical_mechanics`: 41 case(s)
- `enzyme_reaction_kinetics`: 23 case(s)
- `folding_stability_thermodynamics`: 20 case(s)
- `spatial_transport_electrostatics`: 6 case(s)
- `evolutionary_fitness_landscape`: 2 case(s)
- `mechanical_force_response`: 2 case(s)

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
7. The 10 contest gold samples, 30 extended-gold samples, and 50 held-out
   test cases include reviewed `expert_annotation` blocks with physics
   reasoning, biological reasoning, uncertainty, and reviewer notes.
8. Expert annotations are counted separately from release-gate review status so
   users can distinguish dataset validation from human expert review coverage.

## Source provenance
| case_id | paper_title | DOI | license | n_quant_evidence |
|---|---|---|---|---|
| biophysbridge_000004 | Sequence determinants of protein phase behavior from a coarse-grained model | 10.1371/journal.pcbi.1005941 | CC0-1.0 | 4 |
| biophysbridge_000006 | Insights into the activation mechanism of class I HDAC complexes by inositol phosphates | 10.1038/ncomms11262 | CC-BY-4.0 | 5 |
| biophysbridge_000021 | UniKP: a unified framework for the prediction of enzyme kinetic parameters | 10.1038/s41467-023-44113-1 | CC-BY-4.0 | 6 |
| biophysbridge_000023 | Studies of a ring-cleaving dioxygenase illuminate the role of cholesterol metabolism in the pathogenesis of Mycobacterium tuberculosis | 10.1371/journal.ppat.1000344 | CC-BY-4.0 | 7 |
| biophysbridge_000025 | Single-mutation fitness landscapes for an enzyme on multiple substrates reveal specificity is globally encoded | 10.1038/ncomms15695 | CC-BY-4.0 | 5 |
| biophysbridge_000031 | Potent Allosteric Dengue Virus NS5 Polymerase Inhibitors: Mechanism of Action and Resistance Profiling | 10.1371/journal.ppat.1005737 | CC-BY-4.0 | 6 |
| biophysbridge_000037 | Change in allosteric network affects binding affinities of PDZ domains: analysis through perturbation response scanning | 10.1371/journal.pcbi.1002154 | CC-BY-4.0 | 6 |
| biophysbridge_000040 | Autoregulation of GPCR signalling through the third intracellular loop | 10.1038/s41586-023-05789-z | CC-BY-4.0 | 6 |
| biophysbridge_000047 | A canonical model of multistability and scale-invariance in biological systems | 10.1371/journal.pcbi.1002634 | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000010 | Personalized neoantigen vaccine and pembrolizumab in advanced hepatocellular carcinoma: a phase 1/2 trial. | 10.1038/s41591-024-02894-y | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000017 | FRET-based reporters for the direct visualization of abscisic acid concentration changes and distribution in Arabidopsis. | 10.7554/elife.01739 | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000023 | Diabetic Macular Edema: Current Understanding, Molecular Mechanisms and Therapeutic Implications. | 10.3390/cells11213362 | CC-BY-4.0 | 3 |
| biophysbridge_batch001_000039 | De novo enzyme design using Rosetta3. | 10.1371/journal.pone.0019230 | CC-BY-4.0 | 7 |
| biophysbridge_batch001_000060 | Relationships Between Immune Landscapes, Genetic Subtypes and Responses to Immunotherapy in Colorectal Cancer. | 10.3389/fimmu.2020.00369 | CC-BY-4.0 | 4 |
| biophysbridge_batch001_000066 | Manganese is critical for antitumor immune responses via cGAS-STING and improves the efficacy of clinical immunotherapy. | 10.1038/s41422-020-00395-4 | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000086 | N501Y mutation of spike protein in SARS-CoV-2 strengthens its binding to receptor ACE2. | 10.7554/elife.69091 | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000088 | Interleukin-1 Beta-A Friend or Foe in Malignancies? | 10.3390/ijms19082155 | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000093 | PARP-2 and PARP-3 are selectively activated by 5' phosphorylated DNA breaks through an allosteric regulatory mechanism shared with PARP-1. | 10.1093/nar/gku474 | CC-BY-4.0 | 6 |
| biophysbridge_batch002_000007 | Molecular mechanisms of acquired resistance to tyrosine kinase targeted therapy. | 10.1186/1476-4598-9-75 | CC-BY-4.0 | 6 |
| biophysbridge_batch002_000035 | The Molecular Mechanisms That Underlie the Immune Biology of Anti-drug Antibody Formation Following Treatment With Monoclonal Antibodies. | 10.3389/fimmu.2020.01951 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000045 | Current Status of the Diagnosis and Management of Osteoporosis. | 10.3390/ijms23169465 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000051 | FGF21 alleviates neuroinflammation following ischemic stroke by modulating the temporal and spatial dynamics of microglia/macrophages. | 10.1186/s12974-020-01921-2 | CC-BY-4.0 | 4 |
| biophysbridge_batch002_000064 | An autoradiographic evaluation of AV-1451 Tau PET in dementia. | 10.1186/s40478-016-0315-6 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000074 | Mechanisms of resistance to trastuzumab emtansine (T-DM1) in HER2-positive breast cancer. | 10.1038/s41416-019-0635-y | CC-BY-4.0 | 4 |
| biophysbridge_batch002_000075 | CX-5461 is a DNA G-quadruplex stabilizer with selective lethality in BRCA1/2 deficient tumours. | 10.1038/ncomms14432 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000079 | Small-Molecule Binding Aptamers: Selection Strategies, Characterization, and Applications. | 10.3389/fchem.2016.00014 | CC-BY-4.0 | 6 |
| biophysbridge_batch002_000091 | Estrogen receptor alpha somatic mutations Y537S and D538G confer breast cancer endocrine resistance by stabilizing the activating function-2 binding conformation. | 10.7554/elife.12792 | CC-BY-4.0 | 8 |
| biophysbridge_batch002_000092 | NetMHCpan, a method for quantitative predictions of peptide binding to any HLA-A and -B locus protein of known sequence. | 10.1371/journal.pone.0000796 | CC0-1.0 | 6 |
| biophysbridge_batch002_000093 | Combining machine learning systems and multiple docking simulation packages to improve docking prediction reliability for network pharmacology. | 10.1371/journal.pone.0083922 | CC-BY-4.0 | 6 |
| biophysbridge_batch003_000022 | Signal pathways of melanoma and targeted therapy. | 10.1038/s41392-021-00827-6 | CC-BY-4.0 | 4 |
| biophysbridge_batch003_000049 | Structural basis for subtype-specific inhibition of the P2X7 receptor. | 10.7554/elife.22153 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000057 | Trastuzumab emtansine: mechanisms of action and drug resistance. | 10.1186/bcr3621 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000068 | Improving prime editing with an endogenous small RNA-binding protein. | 10.1038/s41586-024-07259-6 | CC-BY-4.0 | 3 |
| biophysbridge_batch004_000002 | Overcoming mutation-based resistance to antiandrogens with rational drug design. | 10.7554/elife.00499 | CC-BY-4.0 | 6 |
| biophysbridge_batch004_000003 | Bispecific T cell engagers: an emerging therapy for management of hematologic malignancies. | 10.1186/s13045-021-01084-4 | CC-BY-4.0 | 7 |
| biophysbridge_batch004_000020 | Rheumatoid arthritis: pathological mechanisms and modern pharmacologic therapies. | 10.1038/s41413-018-0016-9 | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000025 | Rosetta FlexPepDock ab-initio: simultaneous folding, docking and refinement of peptides onto their receptors. | 10.1371/journal.pone.0018934 | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000054 | Structural basis of pathogen recognition by an integrated HMA domain in a plant NLR immune receptor. | 10.7554/elife.08709 | CC-BY-4.0 | 6 |
| biophysbridge_batch004_000071 | Identification of COUP-TFII orphan nuclear receptor as a retinoic acid-activated receptor. | 10.1371/journal.pbio.0060227 | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000079 | Receptor Tyrosine Kinase-Targeted Cancer Therapy. | 10.3390/ijms19113491 | CC-BY-4.0 | 3 |
| biophysbridge_batch004_000081 | Intratumoral heterogeneity and clonal evolution in liver cancer. | 10.1038/s41467-019-14050-z | CC-BY-4.0 | 2 |
| biophysbridge_batch004_000082 | Altered Iron Metabolism and Impact in Cancer Biology, Metastasis, and Immunology. | 10.3389/fonc.2020.00476 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000003 | Local mutational diversity drives intratumoral immune heterogeneity in non-small cell lung cancer. | 10.1038/s41467-018-07767-w | CC-BY-4.0 | 5 |
| biophysbridge_extra_000007 | Structural biology contributions to the discovery of drugs to treat chronic myelogenous leukaemia. | 10.1107/s0907444906047287 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000023 | A network integration approach for drug-target interaction prediction and computational drug repositioning from heterogeneous information. | 10.1038/s41467-017-00680-8 | CC-BY-4.0 | 8 |
| biophysbridge_extra_000055 | Reprogramming of Tumor-Associated Macrophages with Anticancer Therapies: Radiotherapy versus Chemo- and Immunotherapies. | 10.3389/fimmu.2017.00828 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000060 | Roles of METTL3 in cancer: mechanisms and therapeutic targeting. | 10.1186/s13045-020-00951-w | CC-BY-4.0 | 1 |
| biophysbridge_extra_000072 | Hypoxia-enhanced Blood-Brain Barrier Chip recapitulates human barrier function and shuttling of drugs and antibodies. | 10.1038/s41467-019-10588-0 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000087 | Mutation of a nicotinic acetylcholine receptor β subunit is associated with resistance to neonicotinoid insecticides in the aphid Myzus persicae. | 10.1186/1471-2202-12-51 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000096 | NN-align. An artificial neural network-based alignment algorithm for MHC class II peptide binding prediction. | 10.1186/1471-2105-10-296 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000097 | RNAs Containing Modified Nucleotides Fail To Trigger RIG-I Conformational Changes for Innate Immune Signaling. | 10.1128/mbio.00833-16 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000094 | NK Cell-Mediated Antibody-Dependent Cellular Cytotoxicity in Cancer Immunotherapy. | 10.3389/fimmu.2015.00368 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000113 | Tauopathies: new perspectives and challenges. | 10.1186/s13024-022-00533-z | CC-BY-4.0 | 5 |
| biophysbridge_extra_000122 | Variability in docking success rates due to dataset preparation. | 10.1007/s10822-012-9570-1 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000124 | A Comprehensive Evaluation of the Activity and Selectivity Profile of Ligands for RGD-binding Integrins. | 10.1038/srep39805 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000128 | A Path Toward Precision Medicine for Neuroinflammatory Mechanisms in Alzheimer's Disease. | 10.3389/fimmu.2020.00456 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000129 | Accurate calculation of the absolute free energy of binding for drug molecules. | 10.1039/c5sc02678d | CC-BY-4.0 | 8 |
| biophysbridge_extra_000147 | Tau PET imaging in neurodegenerative tauopathies-still a challenge. | 10.1038/s41380-018-0342-8 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000150 | Direct identification of clinically relevant neoepitopes presented on native human melanoma tissue by mass spectrometry. | 10.1038/ncomms13404 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000178 | Structure and interactions of the human programmed cell death 1 receptor. | 10.1074/jbc.m112.448126 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000179 | Synergistic insights into human health from aptamer- and antibody-based proteomic profiling. | 10.1038/s41467-021-27164-0 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000192 | Whole-genome cartography of estrogen receptor alpha binding sites. | 10.1371/journal.pgen.0030087 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000197 | Candida albicans mannans mediate Streptococcus mutans exoenzyme GtfB binding to modulate cross-kingdom biofilm development in vivo. | 10.1371/journal.ppat.1006407 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000201 | Berberine modulates AP-1 activity to suppress HPV transcription and downstream signaling to induce growth arrest and apoptosis in cervical cancer cells. | 10.1186/1476-4598-10-39 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000202 | Force generation upon T cell receptor engagement. | 10.1371/journal.pone.0019680 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000207 | In vivo correction of anaemia in β-thalassemic mice by γPNA-mediated gene editing with nanoparticle delivery. | 10.1038/ncomms13304 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000225 | Characterization of Notch1 antibodies that inhibit signaling of both normal and mutated Notch1 receptors. | 10.1371/journal.pone.0009094 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000228 | Protein disulfide isomerase a multifunctional protein with multiple physiological roles. | 10.3389/fchem.2014.00070 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000231 | A potent SARS-CoV-2 neutralising nanobody shows therapeutic efficacy in the Syrian golden hamster model of COVID-19. | 10.1038/s41467-021-25480-z | CC-BY-4.0 | 5 |
| biophysbridge_extra_000245 | HMGB1 promotes ERK-mediated mitochondrial Drp1 phosphorylation for chemoresistance through RAGE in colorectal cancer. | 10.1038/s41419-018-1019-6 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000251 | Up-regulated TLR4 in cardiomyocytes exacerbates heart failure after long-term myocardial infarction. | 10.1111/jcmm.12659 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000262 | Recent Advances in NAMPT Inhibitors: A Novel Immunotherapic Strategy. | 10.3389/fphar.2020.00656 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000267 | CTLA4 blockade increases Th17 cells in patients with metastatic melanoma. | 10.1186/1479-5876-7-35 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000271 | The extracytoplasmic domain of the Mycobacterium tuberculosis Ser/Thr kinase PknB binds specific muropeptides and is required for PknB localization. | 10.1371/journal.ppat.1002182 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000279 | Translocator protein is a marker of activated microglia in rodent models but not human neurodegenerative diseases. | 10.1038/s41467-023-40937-z | CC-BY-4.0 | 5 |
| biophysbridge_extra_000293 | Multifaceted functions of STING in human health and disease: from molecular mechanism to targeted strategy. | 10.1038/s41392-022-01252-z | CC-BY-4.0 | 3 |
| biophysbridge_extra_000300 | Inflammation Triggered by SARS-CoV-2 and ACE2 Augment Drives Multiple Organ Failure of Severe COVID-19: Molecular Mechanisms and Implications. | 10.1007/s10753-020-01337-3 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000316 | Single particle cryo-EM reconstruction of 52 kDa streptavidin at 3.2 Angstrom resolution. | 10.1038/s41467-019-10368-w | CC-BY-4.0 | 6 |
| biophysbridge_extra_000318 | Structure-based prediction of T cell receptor:peptide-MHC interactions. | 10.7554/elife.82813 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000032 | The kinase LYK5 is a major chitin receptor in Arabidopsis and forms a chitin-induced complex with related kinase CERK1. | 10.7554/elife.03766 | CC0-1.0 | 3 |
| biophysbridge_extra_000033 | Anion Recognition in Water: Recent Advances from a Supramolecular and Macromolecular Perspective. | 10.1002/anie.201506589 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000028 | A structural explanation for the low effectiveness of the seasonal influenza H3N2 vaccine. | 10.1371/journal.ppat.1006682 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000067 | Tau and neuroinflammation in Alzheimer's disease: interplay mechanisms and clinical translation. | 10.1186/s12974-023-02853-3 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000108 | Structure-Based Virtual Screening: From Classical to Artificial Intelligence. | 10.3389/fchem.2020.00343 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000140 | Mechanisms of GII.4 norovirus persistence in human populations. | 10.1371/journal.pmed.0050031 | CC0-1.0 | 3 |
| biophysbridge_extra_000146 | Single nucleotide polymorphisms of human STING can affect innate immune response to cyclic dinucleotides. | 10.1371/journal.pone.0077846 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000186 | The Role of Selenium in Pathologies: An Updated Review. | 10.3390/antiox11020251 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000196 | B Cells in Rheumatoid Arthritis：Pathogenic Mechanisms and Treatment Prospects. | 10.3389/fimmu.2021.750753 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000222 | Emerging roles of eraser enzymes in the dynamic control of protein ADP-ribosylation. | 10.1038/s41467-019-08859-x | CC-BY-4.0 | 3 |
| biophysbridge_extra_000232 | Amyloid-beta modulates microglial responses by binding to the triggering receptor expressed on myeloid cells 2 (TREM2). | 10.1186/s13024-018-0247-7 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000242 | Extrapyramidal side effects of antipsychotics are linked to their association kinetics at dopamine D<sub>2</sub> receptors. | 10.1038/s41467-017-00716-z | CC-BY-4.0 | 4 |
| biophysbridge_extra_000253 | Preclinical assessment of the efficacy and specificity of GD2-B7H3 SynNotch CAR-T in metastatic neuroblastoma. | 10.1038/s41467-020-20785-x | CC-BY-4.0 | 4 |
| biophysbridge_extra_000277 | Cryo-EM structure of the human ferritin-transferrin receptor 1 complex. | 10.1038/s41467-019-09098-w | CC-BY-4.0 | 3 |
| biophysbridge_extra_000280 | USP8 inhibition reshapes an inflamed tumor microenvironment that potentiates the immunotherapy. | 10.1038/s41467-022-29401-6 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000319 | T-cell responses and therapies against SARS-CoV-2 infection. | 10.1111/imm.13262 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000327 | Widespread intronic polyadenylation diversifies immune cell transcriptomes. | 10.1038/s41467-018-04112-z | CC-BY-4.0 | 1 |
| biophysbridge_extra_000334 | A potent broadly neutralizing human RSV antibody targets conserved site IV of the fusion glycoprotein. | 10.1038/s41467-019-12137-1 | CC-BY-4.0 | 5 |
| biophysbridge_000001 | Low-dose metformin targets the lysosomal AMPK pathway through PEN2 | 10.1038/s41586-022-04431-8 | CC-BY-4.0 | 4 |
| biophysbridge_000002 | Phase transitions of multivalent proteins can promote clustering of membrane receptors | 10.7554/eLife.04123 | CC-BY-4.0 | 8 |
| biophysbridge_000003 | DynaMut2: Assessing changes in stability and flexibility upon single and multiple point missense mutations | 10.1002/pro.3942 | CC-BY-4.0 | 6 |
| biophysbridge_000005 | A role for both conformational selection and induced fit in ligand binding by the LAO protein | 10.1371/journal.pcbi.1002054 | CC-BY-4.0 | 5 |
| biophysbridge_000007 | Phenotypic bistability in Escherichia coli's central carbon metabolism | 10.15252/msb.20135022 | CC-BY-4.0 | 6 |
| biophysbridge_000008 | A unified view of how allostery works | 10.1371/journal.pcbi.1003394 | CC0-1.0 | 5 |
| biophysbridge_000010 | Phosphoproteomics reveals that Parkinson's disease kinase LRRK2 regulates a subset of Rab GTPases | 10.7554/elife.12813 | CC-BY-4.0 | 5 |
| biophysbridge_000015 | Contacts-based prediction of binding affinity in protein-protein complexes | 10.7554/elife.07454 | CC-BY-4.0 | 5 |
| biophysbridge_000019 | Two strategies to engineer flexible loops for improved enzyme thermostability | 10.1038/srep41212 | CC-BY-4.0 | 7 |
| biophysbridge_000020 | Psychrophilic enzymes: from folding to function and biotechnology | 10.1155/2013/512840 | CC-BY-4.0 | 7 |
| biophysbridge_000026 | Lactate Regulates Metabolic and Pro-inflammatory Circuits in Control of T Cell Migration and Effector Functions | 10.1371/journal.pbio.1002202 | CC-BY-4.0 | 6 |
| biophysbridge_000030 | Pharmacological dimerization and activation of the exchange factor eIF2B antagonizes the integrated stress response | 10.7554/elife.07314 | CC-BY-4.0 | 5 |
| biophysbridge_000033 | Proteotoxic stress induces phosphorylation of p62/SQSTM1 by ULK1 to regulate selective autophagic clearance of protein aggregates | 10.1371/journal.pgen.1004987 | CC-BY-4.0 | 4 |
| biophysbridge_000034 | Biophysical characterization of the olfactomedin domain of myocilin, an extracellular matrix protein implicated in inherited forms of glaucoma | 10.1371/journal.pone.0016347 | CC-BY-4.0 | 5 |
| biophysbridge_000042 | Charge-driven condensation of RNA and proteins suggests broad role of phase separation in cytoplasmic environments | 10.7554/elife.64004 | CC-BY-4.0 | 7 |
| biophysbridge_000043 | Narrow equilibrium window for complex coacervation of tau and RNA under cellular conditions | 10.7554/elife.42571 | CC-BY-4.0 | 5 |
| biophysbridge_000044 | Thermodynamic forces from protein and water govern condensate formation of an intrinsically disordered protein domain | 10.1038/s41467-023-41586-y | CC-BY-4.0 | 5 |
| biophysbridge_000045 | Quantitative theory for the diffusive dynamics of liquid condensates | 10.7554/elife.68620 | CC-BY-4.0 | 5 |
| biophysbridge_000048 | Modeling a snap-action, variable-delay switch controlling extrinsic cell death | 10.1371/journal.pbio.0060299 | CC-BY-4.0 | 5 |
| biophysbridge_000049 | Interrogating the topological robustness of gene regulatory circuits by randomization | 10.1371/journal.pcbi.1005456 | CC-BY-4.0 | 5 |
| biophysbridge_000009 | The ribosome lowers the entropic penalty of protein folding | 10.1038/s41586-024-07784-4 | CC-BY-4.0 | 7 |
| biophysbridge_000024 | Ensemble-based enzyme design can recapitulate the effects of laboratory directed evolution in silico | 10.1038/s41467-020-18619-x | CC-BY-4.0 | 6 |
| biophysbridge_000027 | A conformational switch high-throughput screening assay and allosteric inhibition of the flavivirus NS2B-NS3 protease | 10.1371/journal.ppat.1006411 | CC-BY-4.0 | 6 |
| biophysbridge_000028 | Single-molecule chemo-mechanical unfolding reveals multiple transition state barriers in a small single-domain protein | 10.1038/ncomms7861 | CC-BY-4.0 | 7 |
| biophysbridge_000046 | Efficient search, mapping, and optimization of multi-protein genetic systems in diverse bacteria | 10.15252/msb.20134955 | CC-BY-4.0 | 7 |
| biophysbridge_batch001_000001 | AlphaFold accelerates artificial intelligence powered drug discovery: efficient discovery of a novel CDK20 small molecule inhibitor. | 10.1039/d2sc05709c | CC-BY-4.0 | 4 |
| biophysbridge_batch001_000012 | Phase separation of FSP1 promotes ferroptosis. | 10.1038/s41586-023-06255-6 | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000013 | Recent Advances in SELEX Technology and Aptamer Applications in Biomedicine. | 10.3390/ijms18102142 | CC-BY-4.0 | 7 |
| biophysbridge_batch001_000014 | The Discovery and Development of Liraglutide and Semaglutide. | 10.3389/fendo.2019.00155 | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000019 | A Basic Review on Estrogen Receptor Signaling Pathways in Breast Cancer. | 10.3390/ijms24076834 | CC-BY-4.0 | 4 |
| biophysbridge_batch001_000020 | Biologic activity and safety of belimumab, a neutralizing anti-B-lymphocyte stimulator (BLyS) monoclonal antibody: a phase I trial in patients with systemic lupus erythematosus. | 10.1186/ar2506 | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000021 | Small-molecule inhibition of Lats kinases may promote Yap-dependent proliferation in postmitotic mammalian tissues. | 10.1038/s41467-021-23395-3 | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000025 | A mechanism for the activation of the mechanosensitive Piezo1 channel by the small molecule Yoda1. | 10.1038/s41467-019-12501-1 | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000004 | Endoplasmic reticulum stress: molecular mechanism and therapeutic targets. | 10.1038/s41392-023-01570-w | CC-BY-4.0 | 2 |
| biophysbridge_batch001_000026 | Synthetic biology for the directed evolution of protein biocatalysts: navigating sequence space intelligently. | 10.1039/c4cs00351a | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000027 | The C-F bond as a conformational tool in organic and biological chemistry. | 10.3762/bjoc.6.38 | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000029 | Antibody Structure and Function: The Basis for Engineering Therapeutics. | 10.3390/antib8040055 | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000033 | Advanced nanocarrier- and microneedle-based transdermal drug delivery strategies for skin diseases treatment. | 10.7150/thno.69999 | CC-BY-4.0 | 2 |
| biophysbridge_batch001_000035 | Beyond DNA Repair: Additional Functions of PARP-1 in Cancer. | 10.3389/fonc.2013.00290 | CC-BY-4.0 | 3 |
| biophysbridge_batch001_000037 | Crossing the Blood-Brain Barrier: Advances in Nanoparticle Technology for Drug Delivery in Neuro-Oncology. | 10.3390/ijms23084153 | CC-BY-4.0 | 4 |
| biophysbridge_batch001_000038 | CAR-T cell therapy: current limitations and potential strategies. | 10.1038/s41408-021-00459-7 | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000042 | Quercetin as an Antiviral Agent Inhibits Influenza A Virus (IAV) Entry. | 10.3390/v8010006 | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000043 | On the role of phase separation in the biogenesis of membraneless compartments. | 10.15252/embj.2021109952 | CC-BY-4.0 | 2 |
| biophysbridge_batch001_000045 | Phase transitions of multivalent proteins can promote clustering of membrane receptors. | 10.7554/elife.04123 | CC-BY-4.0 | 8 |
| biophysbridge_batch001_000047 | Current strategies for the design of PROTAC linkers: a critical review. | 10.37349/etat.2020.00018 | CC-BY-4.0 | 8 |
| biophysbridge_batch001_000048 | Advances in immunotherapy for triple-negative breast cancer. | 10.1186/s12943-023-01850-7 | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000050 | Toward more realistic drug-target interaction predictions. | 10.1093/bib/bbu010 | CC-BY-4.0 | 7 |
| biophysbridge_batch001_000056 | Aminoglycoside-Induced Cochleotoxicity: A Review. | 10.3389/fncel.2017.00308 | CC-BY-4.0 | 3 |
| biophysbridge_batch001_000057 | Cannabidiol for Pain Treatment: Focus on Pharmacology and Mechanism of Action. | 10.3390/ijms21228870 | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000058 | Cellular entry of the porcine epidemic diarrhea virus. | 10.1016/j.virusres.2016.05.031 | CC-BY-4.0 | 4 |
| biophysbridge_batch001_000059 | Fluorogenic RNA Mango aptamers for imaging small non-coding RNAs in mammalian cells. | 10.1038/s41467-018-02993-8 | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000064 | Emerging new therapeutic antibody derivatives for cancer treatment. | 10.1038/s41392-021-00868-x | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000065 | Crystallographic and electrophilic fragment screening of the SARS-CoV-2 main protease. | 10.1038/s41467-020-18709-w | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000069 | Cyanidin-3-O-glucoside: Physical-Chemistry, Foodomics and Health Effects. | 10.3390/molecules21091264 | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000071 | Identify potent SARS-CoV-2 main protease inhibitors via accelerated free energy perturbation-based virtual screening of existing drugs. | 10.1073/pnas.2010470117 | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000073 | Hydrogen peroxide - production, fate and role in redox signaling of tumor cells. | 10.1186/s12964-015-0118-6 | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000075 | Antimicrobial Peptides and Their Therapeutic Potential for Bacterial Skin Infections and Wounds. | 10.3389/fphar.2018.00281 | CC-BY-4.0 | 2 |
| biophysbridge_batch001_000076 | Glucocorticoids-All-Rounders Tackling the Versatile Players of the Immune System. | 10.3389/fimmu.2019.01744 | CC-BY-4.0 | 3 |
| biophysbridge_batch001_000078 | Broadly neutralizing antibody PGT121 allosterically modulates CD4 binding via recognition of the HIV-1 gp120 V3 base and multiple surrounding glycans. | 10.1371/journal.ppat.1003342 | CC-BY-4.0 | 7 |
| biophysbridge_batch001_000081 | In vitro glycoengineering of IgG1 and its effect on Fc receptor binding and ADCC activity. | 10.1371/journal.pone.0134949 | CC-BY-4.0 | 4 |
| biophysbridge_batch001_000082 | Cellular zinc metabolism and zinc signaling: from biological functions to diseases and therapeutic targets. | 10.1038/s41392-023-01679-y | CC-BY-4.0 | 3 |
| biophysbridge_batch001_000083 | An overview of PROTACs: a promising drug discovery paradigm. | 10.1186/s43556-022-00112-0 | CC-BY-4.0 | 5 |
| biophysbridge_batch001_000084 | IGF-Binding Proteins: Why Do They Exist and Why Are There So Many? | 10.3389/fendo.2018.00117 | CC-BY-4.0 | 4 |
| biophysbridge_batch001_000089 | Insights into the activation mechanism of class I HDAC complexes by inositol phosphates. | 10.1038/ncomms11262 | CC-BY-4.0 | 7 |
| biophysbridge_batch001_000092 | Kinase-targeted cancer therapies: progress, challenges and future directions. | 10.1186/s12943-018-0804-2 | CC-BY-4.0 | 2 |
| biophysbridge_batch002_000001 | Targeting FLT3 mutations in AML: review of current knowledge and evidence. | 10.1038/s41375-018-0357-9 | CC-BY-4.0 | 6 |
| biophysbridge_batch002_000003 | Mechanistic and structural basis for activation of cardiac myosin force production by omecamtiv mecarbil. | 10.1038/s41467-017-00176-5 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000004 | Potent and selective chemical probe of hypoxic signalling downstream of HIF-α hydroxylation via VHL inhibition. | 10.1038/ncomms13312 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000008 | Recent Advances in the Enantioselective Synthesis of Chiral Amines via Transition Metal-Catalyzed Asymmetric Hydrogenation. | 10.1021/acs.chemrev.1c00496 | CC-BY-4.0 | 4 |
| biophysbridge_batch002_000011 | NK Cell-Based Immune Checkpoint Inhibition. | 10.3389/fimmu.2020.00167 | CC-BY-4.0 | 3 |
| biophysbridge_batch002_000012 | SARS-CoV-2-Specific Immune Response and the Pathogenesis of COVID-19. | 10.3390/ijms23031716 | CC-BY-4.0 | 2 |
| biophysbridge_batch002_000013 | IgG subclasses and allotypes: from structure to effector functions. | 10.3389/fimmu.2014.00520 | CC-BY-4.0 | 6 |
| biophysbridge_batch002_000015 | Neurogenic inflammation after traumatic brain injury and its potentiation of classical inflammation. | 10.1186/s12974-016-0738-9 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000018 | Comprehensive Review on Alzheimer's Disease: Causes and Treatment. | 10.3390/molecules25245789 | CC-BY-4.0 | 3 |
| biophysbridge_batch002_000019 | Neurotrophic Factor BDNF, Physiological Functions and Therapeutic Potential in Depression, Neurodegeneration and Brain Cancer. | 10.3390/ijms21207777 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000022 | Graphical analysis of pH-dependent properties of proteins predicted using PROPKA. | 10.1186/1472-6807-11-6 | CC-BY-4.0 | 3 |
| biophysbridge_batch002_000025 | Phosphorylation meets nuclear import: a review. | 10.1186/1478-811x-8-32 | CC-BY-4.0 | 4 |
| biophysbridge_batch002_000028 | Targeting Cullin-RING E3 ubiquitin ligases for drug discovery: structure, assembly and small-molecule modulation. | 10.1042/bj20141450 | CC-BY-4.0 | 3 |
| biophysbridge_batch002_000032 | The Concise Guide to PHARMACOLOGY 2013/14: G protein-coupled receptors. | 10.1111/bph.12445 | CC-BY-4.0 | 6 |
| biophysbridge_batch002_000033 | Targeting integrin pathways: mechanisms and advances in therapy. | 10.1038/s41392-022-01259-6 | CC-BY-4.0 | 1 |
| biophysbridge_batch002_000034 | Polymeric Nanoparticles for Drug Delivery: Recent Developments and Future Prospects. | 10.3390/nano10071403 | CC-BY-4.0 | 8 |
| biophysbridge_batch002_000039 | Understanding the Effectiveness of Natural Compound Mixtures in Cancer through Their Molecular Mode of Action. | 10.3390/ijms18030656 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000049 | A small-molecule TNIK inhibitor targets fibrosis in preclinical and clinical models. | 10.1038/s41587-024-02143-0 | CC-BY-4.0 | 4 |
| biophysbridge_batch002_000050 | Phage Display Derived Monoclonal Antibodies: From Bench to Bedside. | 10.3389/fimmu.2020.01986 | CC-BY-4.0 | 2 |
| biophysbridge_batch002_000052 | APOE and Alzheimer's Disease: From Lipid Transport to Physiopathology and Therapeutics. | 10.3389/fnins.2021.630502 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000053 | The neutralizing antibody, LY-CoV555, protects against SARS-CoV-2 infection in nonhuman primates. | 10.1126/scitranslmed.abf1906 | CC-BY-4.0 | 4 |
| biophysbridge_batch002_000054 | Fibroblast Growth Factor Receptors (FGFRs): Structures and Small Molecule Inhibitors. | 10.3390/cells8060614 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000058 | Aggregation-Induced Emission (AIE), Life and Health. | 10.1021/acsnano.3c03925 | CC-BY-4.0 | 1 |
| biophysbridge_batch002_000060 | Integrin-specific hydrogels modulate transplanted human bone marrow-derived mesenchymal stem cell survival, engraftment, and reparative activities. | 10.1038/s41467-019-14000-9 | CC-BY-4.0 | 4 |
| biophysbridge_batch002_000062 | Mechanism of regulation of stem cell differentiation by matrix stiffness. | 10.1186/s13287-015-0083-4 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000068 | Mechanism of baricitinib supports artificial intelligence-predicted testing in COVID-19 patients. | 10.15252/emmm.202012697 | CC-BY-4.0 | 7 |
| biophysbridge_batch002_000069 | Association between serum perfluorooctanoic acid (PFOA) and thyroid disease in the U.S. National Health and Nutrition Examination Survey. | 10.1289/ehp.0901584 | CC0-1.0 | 6 |
| biophysbridge_batch002_000071 | PoPMuSiC 2.1: a web server for the estimation of protein stability changes upon mutation and sequence optimality. | 10.1186/1471-2105-12-151 | CC-BY-4.0 | 6 |
| biophysbridge_batch002_000072 | Binding-induced folding of a natively unstructured transcription factor. | 10.1371/journal.pcbi.1000060 | CC0-1.0 | 4 |
| biophysbridge_batch002_000083 | NF-κB Pathway as a Potential Target for Treatment of Critical Stage COVID-19 Patients. | 10.3389/fimmu.2020.598444 | CC-BY-4.0 | 6 |
| biophysbridge_batch002_000085 | Bisphenol AF is a full agonist for the estrogen receptor ERalpha but a highly specific antagonist for ERbeta. | 10.1289/ehp.0901819 | CC0-1.0 | 5 |
| biophysbridge_batch002_000088 | Clinically-Relevant ABC Transporter for Anti-Cancer Drug Resistance. | 10.3389/fphar.2021.648407 | CC-BY-4.0 | 5 |
| biophysbridge_batch002_000089 | Natural killer cell homing and trafficking in tissues and tumors: from biology to application. | 10.1038/s41392-022-01058-z | CC-BY-4.0 | 3 |
| biophysbridge_batch002_000094 | Structural mechanism of ligand activation in human calcium-sensing receptor. | 10.7554/elife.13662 | CC-BY-4.0 | 4 |
| biophysbridge_batch002_000096 | Concurrent inhibition of oncogenic and wild-type RAS-GTP for cancer therapy. | 10.1038/s41586-024-07205-6 | CC-BY-4.0 | 7 |
| biophysbridge_batch002_000097 | Therapeutic cancer vaccines: advancements, challenges, and prospects. | 10.1038/s41392-023-01674-3 | CC-BY-4.0 | 2 |
| biophysbridge_batch002_000098 | Next-generation immuno-oncology agents: current momentum shifts in cancer immunotherapy. | 10.1186/s13045-020-00862-w | CC-BY-4.0 | 6 |
| biophysbridge_batch003_000001 | AXL receptor tyrosine kinase as a promising anti-cancer approach: functions, molecular mechanisms and clinical applications. | 10.1186/s12943-019-1090-3 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000003 | Nitric Oxide: Physiological Functions, Delivery, and Biomedical Applications. | 10.1002/advs.202303259 | CC-BY-4.0 | 2 |
| biophysbridge_batch003_000005 | PTEN/PTENP1: 'Regulating the regulator of RTK-dependent PI3K/Akt signalling', new targets for cancer therapy. | 10.1186/s12943-018-0803-3 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000008 | Peroxisome proliferator-activated receptor gamma coactivator-1 (PGC-1) family in physiological and pathophysiological process and diseases. | 10.1038/s41392-024-01756-w | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000009 | NAD<sup>+</sup> analog reveals PARP-1 substrate-blocking mechanism and allosteric communication from catalytic center to DNA-binding domains. | 10.1038/s41467-018-03234-8 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000013 | Recent advances in non-small cell lung cancer targeted therapy; an update review. | 10.1186/s12935-023-02990-y | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000014 | G protein-coupled receptors (GPCRs): advances in structures, mechanisms, and drug discovery. | 10.1038/s41392-024-01803-6 | CC-BY-4.0 | 4 |
| biophysbridge_batch003_000017 | Transition-Metal-Catalyzed C-H Bond Activation for the Formation of C-C Bonds in Complex Molecules. | 10.1021/acs.chemrev.2c00888 | CC-BY-4.0 | 4 |
| biophysbridge_batch003_000023 | Mass spectrometry of human leukocyte antigen class I peptidomes reveals strong effects of protein abundance and turnover on antigen presentation. | 10.1074/mcp.m114.042812 | CC-BY-4.0 | 7 |
| biophysbridge_batch003_000024 | Fulvestrant: an oestrogen receptor antagonist with a novel mechanism of action. | 10.1038/sj.bjc.6601629 | CC-BY-4.0 | 6 |
| biophysbridge_batch003_000025 | Small molecules in targeted cancer therapy: advances, challenges, and future perspectives. | 10.1038/s41392-021-00572-w | CC-BY-4.0 | 4 |
| biophysbridge_batch003_000026 | A new class of small molecule inhibitor of BMP signaling. | 10.1371/journal.pone.0062721 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000031 | Functionalized Nanomaterials Capable of Crossing the Blood-Brain Barrier. | 10.1021/acsnano.3c10674 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000034 | Molecular Targets for Components of Essential Oils in the Insect Nervous System-A Review. | 10.3390/molecules23010034 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000037 | Mesoporous Silica Nanoparticles: A Comprehensive Review on Synthesis and Recent Advances. | 10.3390/pharmaceutics10030118 | CC-BY-4.0 | 6 |
| biophysbridge_batch003_000039 | The biological function and clinical utilization of CD147 in human diseases: a review of the current scientific literature. | 10.3390/ijms151017411 | CC-BY-4.0 | 2 |
| biophysbridge_batch003_000048 | Therapeutic siRNA: state of the art. | 10.1038/s41392-020-0207-x | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000051 | Therapeutic strategies for EGFR-mutated non-small cell lung cancer patients with osimertinib resistance. | 10.1186/s13045-022-01391-4 | CC-BY-4.0 | 6 |
| biophysbridge_batch003_000056 | METTL3/IGF2BP3 axis inhibits tumor immune surveillance by upregulating N<sup>6</sup>-methyladenosine modification of PD-L1 mRNA in breast cancer. | 10.1186/s12943-021-01447-y | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000058 | IgA: Structure, Function, and Developability. | 10.3390/antib8040057 | CC-BY-4.0 | 4 |
| biophysbridge_batch003_000062 | Metalloproteinases and Their Inhibitors: Potential for the Development of New Therapeutics. | 10.3390/cells9051313 | CC-BY-4.0 | 2 |
| biophysbridge_batch003_000063 | Unveiling the mechanisms and challenges of cancer drug resistance. | 10.1186/s12964-023-01302-1 | CC-BY-4.0 | 1 |
| biophysbridge_batch003_000069 | Molecular Mechanisms and Emerging Therapeutics for Osteoporosis. | 10.3390/ijms21207623 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000070 | A General Introduction to Glucocorticoid Biology. | 10.3389/fimmu.2019.01545 | CC-BY-4.0 | 1 |
| biophysbridge_batch003_000074 | PROTACs: great opportunities for academia and industry. | 10.1038/s41392-019-0101-6 | CC-BY-4.0 | 6 |
| biophysbridge_batch003_000076 | An Overview of Coumarin as a Versatile and Readily Accessible Scaffold with Broad-Ranging Biological Activities. | 10.3390/ijms21134618 | CC-BY-4.0 | 6 |
| biophysbridge_batch003_000077 | Brigatinib combined with anti-EGFR antibody overcomes osimertinib resistance in EGFR-mutated non-small-cell lung cancer. | 10.1038/ncomms14768 | CC-BY-4.0 | 6 |
| biophysbridge_batch003_000078 | Morphogen rules: design principles of gradient-mediated embryo patterning. | 10.1242/dev.129452 | CC-BY-4.0 | 3 |
| biophysbridge_batch003_000083 | Assessment of the evolution of cancer treatment therapies. | 10.3390/cancers3033279 | CC-BY-4.0 | 4 |
| biophysbridge_batch003_000084 | Proteolysis-targeting chimera (PROTAC) for targeted protein degradation and cancer therapy. | 10.1186/s13045-020-00885-3 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000086 | BCMA-targeted immunotherapy for multiple myeloma. | 10.1186/s13045-020-00962-7 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000087 | Differential TAM receptor-ligand-phospholipid interactions delimit differential TAM bioactivities. | 10.7554/elife.03385 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000089 | Benzo[<i>a</i>]pyrene-Environmental Occurrence, Human Exposure, and Mechanisms of Toxicity. | 10.3390/ijms23116348 | CC-BY-4.0 | 5 |
| biophysbridge_batch003_000090 | RAB31 marks and controls an ESCRT-independent exosome pathway. | 10.1038/s41422-020-00409-1 | CC-BY-4.0 | 2 |
| biophysbridge_batch003_000093 | Stealth properties to improve therapeutic efficacy of drug nanocarriers. | 10.1155/2013/374252 | CC-BY-4.0 | 6 |
| biophysbridge_batch004_000009 | Cell-Penetrating Peptides in Diagnosis and Treatment of Human Diseases: From Preclinical Research to Clinical Application. | 10.3389/fphar.2020.00697 | CC-BY-4.0 | 2 |
| biophysbridge_batch004_000010 | Peptide binding predictions for HLA DR, DP and DQ molecules. | 10.1186/1471-2105-11-568 | CC-BY-4.0 | 6 |
| biophysbridge_batch004_000011 | mRNA vaccine for cancer immunotherapy. | 10.1186/s12943-021-01335-5 | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000012 | Post-stroke inflammation-target or tool for therapy? | 10.1007/s00401-018-1930-z | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000013 | Cilengitide: the first anti-angiogenic small molecule drug candidate design, synthesis and clinical evaluation. | 10.2174/187152010794728639 | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000014 | Sialic acid receptor detection in the human respiratory tract: evidence for widespread distribution of potential binding sites for human and avian influenza viruses. | 10.1186/1465-9921-8-73 | CC-BY-4.0 | 3 |
| biophysbridge_batch004_000015 | Protein arginine methyltransferases: promising targets for cancer therapy. | 10.1038/s12276-021-00613-y | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000017 | Real-time reliable determination of binding kinetics of DNA hybridization using a multi-channel graphene biosensor. | 10.1038/ncomms14902 | CC-BY-4.0 | 3 |
| biophysbridge_batch004_000021 | Critical role of FOXO3a in carcinogenesis. | 10.1186/s12943-018-0856-3 | CC-BY-4.0 | 2 |
| biophysbridge_batch004_000024 | Cryo-EM structure of an activated VIP1 receptor-G protein complex revealed by a NanoBiT tethering strategy. | 10.1038/s41467-020-17933-8 | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000026 | Unraveling the Interaction between FcRn and Albumin: Opportunities for Design of Albumin-Based Therapeutics. | 10.3389/fimmu.2014.00682 | CC-BY-4.0 | 6 |
| biophysbridge_batch004_000036 | Engineering mesoporous silica nanoparticles for drug delivery: where are we after two decades? | 10.1039/d1cs00659b | CC-BY-4.0 | 3 |
| biophysbridge_batch004_000039 | Insulin-like growth factor system in cancer: novel targeted therapies. | 10.1155/2015/538019 | CC-BY-4.0 | 6 |
| biophysbridge_batch004_000042 | A community resource benchmarking predictions of peptide binding to MHC-I molecules. | 10.1371/journal.pcbi.0020065 | CC-BY-4.0 | 4 |
| biophysbridge_batch004_000043 | Signaling pathways and therapeutic interventions in gastric cancer. | 10.1038/s41392-022-01190-w | CC-BY-4.0 | 4 |
| biophysbridge_batch004_000044 | FDG PET/CT for assessing tumour response to immunotherapy : Report on the EANM symposium on immune modulation and recent review of the literature. | 10.1007/s00259-018-4171-4 | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000047 | A cross-kingdom conserved ER-phagy receptor maintains endoplasmic reticulum homeostasis during stress. | 10.7554/elife.58396 | CC-BY-4.0 | 3 |
| biophysbridge_batch004_000049 | Fibroblast growth factor receptors in cancer: genetic alterations, diagnostics, therapeutic targets and mechanisms of resistance. | 10.1038/s41416-020-01157-0 | CC-BY-4.0 | 4 |
| biophysbridge_batch004_000050 | MARCO, TLR2, and CD14 are required for macrophage cytokine responses to mycobacterial trehalose dimycolate and Mycobacterium tuberculosis. | 10.1371/journal.ppat.1000474 | CC-BY-4.0 | 4 |
| biophysbridge_batch004_000051 | Structural basis of RNA recognition by the SARS-CoV-2 nucleocapsid phosphoprotein. | 10.1371/journal.ppat.1009100 | CC-BY-4.0 | 7 |
| biophysbridge_batch004_000052 | Functional Regulation of PPARs through Post-Translational Modifications. | 10.3390/ijms19061738 | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000053 | A post-synaptic scaffold at the origin of the animal kingdom. | 10.1371/journal.pone.0000506 | CC-BY-4.0 | 2 |
| biophysbridge_batch004_000056 | Molecular Pharmacology of VEGF-A Isoforms: Binding and Signalling at VEGFR2. | 10.3390/ijms19041264 | CC-BY-4.0 | 1 |
| biophysbridge_batch004_000057 | Structural biology of SARS-CoV-2: open the door for novel therapies. | 10.1038/s41392-022-00884-5 | CC-BY-4.0 | 1 |
| biophysbridge_batch004_000058 | Glycosylation of immunoglobulin G determines osteoclast differentiation and bone loss. | 10.1038/ncomms7651 | CC-BY-4.0 | 4 |
| biophysbridge_batch004_000059 | A structurally distinct TGF-β mimic from an intestinal helminth parasite potently induces regulatory T cells. | 10.1038/s41467-017-01886-6 | CC-BY-4.0 | 6 |
| biophysbridge_batch004_000062 | Targeting FGFR4 inhibits hepatocellular carcinoma in preclinical mouse models. | 10.1371/journal.pone.0036713 | CC-BY-4.0 | 6 |
| biophysbridge_batch004_000064 | The ECM-cell interaction of cartilage extracellular matrix on chondrocytes. | 10.1155/2014/648459 | CC-BY-4.0 | 2 |
| biophysbridge_batch004_000065 | HDAC Inhibitors as Epigenetic Regulators of the Immune System: Impacts on Cancer Therapy and Inflammatory Diseases. | 10.1155/2016/8797206 | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000067 | Activating cGAS-STING pathway for the optimal effect of cancer immunotherapy. | 10.1186/s13045-019-0721-x | CC-BY-4.0 | 1 |
| biophysbridge_batch004_000069 | Overview of the Mechanisms that May Contribute to the Non-Redundant Activities of Interferon-Inducible CXC Chemokine Receptor 3 Ligands. | 10.3389/fimmu.2017.01970 | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000072 | Active Targeting Strategies Using Biological Ligands for Nanoparticle Drug Delivery Systems. | 10.3390/cancers11050640 | CC-BY-4.0 | 2 |
| biophysbridge_batch004_000073 | The discovery and development of selective estrogen receptor modulators (SERMs) for clinical practice. | 10.2174/1574884711308020006 | CC-BY-4.0 | 3 |
| biophysbridge_batch004_000074 | Ras/Raf/MEK/ERK and PI3K/PTEN/Akt/mTOR cascade inhibitors: how mutations can result in therapy resistance and how to overcome resistance. | 10.18632/oncotarget.659 | CC-BY-4.0 | 3 |
| biophysbridge_batch004_000076 | Insights into the role of sialylation in cancer progression and metastasis. | 10.1038/s41416-020-01126-7 | CC-BY-4.0 | 5 |
| biophysbridge_batch004_000080 | Tumor necrosis factor alpha: a link between neuroinflammation and excitotoxicity. | 10.1155/2014/861231 | CC-BY-4.0 | 2 |
| biophysbridge_batch004_000084 | Liquid biopsy: a step closer to transform diagnosis, prognosis and future of cancer treatments. | 10.1186/s12943-022-01543-7 | CC-BY-4.0 | 3 |
| biophysbridge_batch004_000085 | Structural and chemical profiling of the human cytosolic sulfotransferases. | 10.1371/journal.pbio.0050097 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000001 | Chemokine CXCL1 mediated neutrophil recruitment: Role of glycosaminoglycan interactions. | 10.1038/srep33123 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000008 | mRNA therapeutics in cancer immunotherapy. | 10.1186/s12943-021-01348-0 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000010 | Antibacterial photodynamic therapy: overview of a promising approach to fight antibiotic-resistant bacterial infections. | 10.18053/jctres.201503.002 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000011 | p62/SQSTM1/Sequestosome-1 is an N-recognin of the N-end rule pathway which modulates autophagosome biogenesis. | 10.1038/s41467-017-00085-7 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000012 | MALAT1: a druggable long non-coding RNA for targeted anti-cancer approaches. | 10.1186/s13045-018-0606-4 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000013 | Structure of severe acute respiratory syndrome coronavirus receptor-binding domain complexed with neutralizing antibody. | 10.1074/jbc.m600697200 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000015 | Meclofenamic acid selectively inhibits FTO demethylation of m6A over ALKBH5. | 10.1093/nar/gku1276 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000017 | A Guide to Human Zinc Absorption: General Overview and Recent Advances of In Vitro Intestinal Models. | 10.3390/nu12030762 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000019 | A Structural View of SARS-CoV-2 RNA Replication Machinery: RNA Synthesis, Proofreading and Final Capping. | 10.3390/cells9051267 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000024 | The JAK/STAT signaling pathway: from bench to clinic. | 10.1038/s41392-021-00791-1 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000025 | A next-generation cleaved, soluble HIV-1 Env trimer, BG505 SOSIP.664 gp140, expresses multiple epitopes for broadly neutralizing but not non-neutralizing antibodies. | 10.1371/journal.ppat.1003618 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000026 | Molecular mechanism of interaction between SARS-CoV-2 and host cells and interventional therapy. | 10.1038/s41392-021-00653-w | CC-BY-4.0 | 6 |
| biophysbridge_extra_000027 | Bioactivity, Health Benefits, and Related Molecular Mechanisms of Curcumin: Current Progress, Challenges, and Perspectives. | 10.3390/nu10101553 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000009 | Lung cancer immunotherapy: progress, pitfalls, and promises. | 10.1186/s12943-023-01740-y | CC-BY-4.0 | 1 |
| biophysbridge_extra_000031 | An ABC transporter mutation is correlated with insect resistance to Bacillus thuringiensis Cry1Ac toxin. | 10.1371/journal.pgen.1001248 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000040 | Biochemical and structural insights into the mechanisms of SARS coronavirus RNA ribose 2'-O-methylation by nsp16/nsp10 protein complex. | 10.1371/journal.ppat.1002294 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000035 | Antibody evasion by SARS-CoV-2 Omicron subvariants BA.2.12.1, BA.4 and BA.5. | 10.1038/s41586-022-05053-w | CC-BY-4.0 | 6 |
| biophysbridge_extra_000048 | De novo mutations in moderate or severe intellectual disability. | 10.1371/journal.pgen.1004772 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000049 | Comprehensive elaboration of the cGAS-STING signaling axis in cancer development and immunotherapy. | 10.1186/s12943-020-01250-1 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000043 | Phage display screening of therapeutic peptide for cancer targeting and therapy. | 10.1007/s13238-019-0639-7 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000045 | Copper homeostasis and cuproptosis in health and disease. | 10.1038/s41392-022-01229-y | CC-BY-4.0 | 1 |
| biophysbridge_extra_000047 | Comparative Structure and Function Analysis of the RIG-I-Like Receptors: RIG-I and MDA5. | 10.3389/fimmu.2019.01586 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000051 | Design of protein-binding proteins from the target structure alone. | 10.1038/s41586-022-04654-9 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000054 | Detection of Atherosclerotic Inflammation by &lt;sup&gt;68&lt;/sup&gt;Ga-DOTATATE PET Compared to [&lt;sup&gt;18&lt;/sup&gt;F]FDG PET Imaging. | 10.1016/j.jacc.2017.01.060 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000061 | ESR1 mutation as an emerging clinical biomarker in metastatic hormone receptor-positive breast cancer. | 10.1186/s13058-021-01462-3 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000062 | Discovery of ODM-201, a new-generation androgen receptor inhibitor targeting resistance mechanisms to androgen signaling-directed prostate cancer therapies. | 10.1038/srep12007 | CC-BY-4.0 | 8 |
| biophysbridge_extra_000063 | From Animal Poisons and Venoms to Medicines: Achievements, Challenges and Perspectives in Drug Discovery. | 10.3389/fphar.2020.01132 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000066 | Evaluation of MHC class I peptide binding prediction servers: applications for vaccine research. | 10.1186/1471-2172-9-8 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000070 | High-throughput and Sensitive Immunopeptidomics Platform Reveals Profound Interferonγ-Mediated Remodeling of the Human Leukocyte Antigen (HLA) Ligandome. | 10.1074/mcp.tir117.000383 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000073 | The emerging treatment landscape of targeted therapy in non-small-cell lung cancer. | 10.1038/s41392-019-0099-9 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000076 | Interaction between circulating galectin-3 and cancer-associated MUC1 enhances tumour cell homotypic aggregation and prevents anoikis. | 10.1186/1476-4598-9-154 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000075 | The impact of tonic GABAA receptor-mediated inhibition on neuronal excitability varies across brain region and cell type. | 10.3389/fncir.2014.00003 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000085 | Mouse Genome Database (MGD): Knowledgebase for mouse-human comparative biology. | 10.1093/nar/gkaa1083 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000079 | Key Topics in Molecular Docking for Drug Design. | 10.3390/ijms20184574 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000082 | Tirzepatide is an imbalanced and biased dual GIP and GLP-1 receptor agonist. | 10.1172/jci.insight.140532 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000095 | Protein-Based Nanoparticles as Drug Delivery Systems. | 10.3390/pharmaceutics12070604 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000098 | PD-1/PD-L1 Blockade: Have We Found the Key to Unleash the Antitumor Immune Response? | 10.3389/fimmu.2017.01597 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000101 | Protein-Ligand Blind Docking Using QuickVina-W With Inter-Process Spatio-Temporal Integration. | 10.1038/s41598-017-15571-7 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000099 | Prediction of MHC class II binding affinity using SMM-align, a novel stabilization matrix alignment method. | 10.1186/1471-2105-8-238 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000103 | Quantitative predictions of peptide binding to any HLA-DR molecule of known sequence: NetMHCIIpan. | 10.1371/journal.pcbi.1000107 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000105 | Targeting EphA2 in cancer. | 10.1186/s13045-020-00944-9 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000100 | Role of Nrf2/HO-1 system in development, oxidative stress response and diseases: an evolutionarily conserved mechanism. | 10.1007/s00018-016-2223-0 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000106 | RNA-based therapeutics: an overview and prospectus. | 10.1038/s41419-022-05075-2 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000107 | Structure, mechanism and crystallographic fragment screening of the SARS-CoV-2 NSP13 helicase. | 10.1038/s41467-021-25166-6 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000104 | Psychedelics promote plasticity by directly binding to BDNF receptor TrkB. | 10.1038/s41593-023-01316-5 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000110 | Structure-based virtual screening for drug discovery: a problem-centric review. | 10.1208/s12248-012-9322-0 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000111 | The CK1 Family: Contribution to Cellular Stress Response and Its Role in Carcinogenesis. | 10.3389/fonc.2014.00096 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000112 | Tau PET imaging: present and future directions. | 10.1186/s13024-017-0162-3 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000092 | Production of chitooligosaccharides and their potential applications in medicine. | 10.3390/md8051482 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000119 | The sirtuin family in health and disease. | 10.1038/s41392-022-01257-8 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000115 | The blood-brain barrier: structure, regulation, and drug delivery. | 10.1038/s41392-023-01481-w | CC-BY-4.0 | 7 |
| biophysbridge_extra_000120 | Transcriptome-wide identification of transient RNA G-quadruplexes in human cells. | 10.1038/s41467-018-07224-8 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000123 | 8-Oxoguanine: from oxidative damage to epigenetic and epitranscriptional modification. | 10.1038/s12276-022-00822-z | CC-BY-4.0 | 2 |
| biophysbridge_extra_000126 | Targeting Transcription Factors for Cancer Treatment. | 10.3390/molecules23061479 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000132 | Affibody molecules as engineered protein drugs. | 10.1038/emm.2017.35 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000133 | Cannabinoid CB<sub>2</sub> receptor ligand profiling reveals biased signalling and off-target activity. | 10.1038/ncomms13958 | CC-BY-4.0 | 8 |
| biophysbridge_extra_000127 | The construction, expression, and enhanced anti-tumor activity of YM101: a bispecific antibody simultaneously targeting TGF-β and PD-L1. | 10.1186/s13045-021-01045-x | CC-BY-4.0 | 6 |
| biophysbridge_extra_000121 | Tumor Necrosis Factor Receptors: Pleiotropic Signaling Complexes and Their Differential Effects. | 10.3389/fimmu.2020.585880 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000137 | C-terminal calcium binding of α-synuclein modulates synaptic vesicle interaction. | 10.1038/s41467-018-03111-4 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000142 | Connecting genetic risk to disease end points through the human blood plasma proteome. | 10.1038/ncomms14357 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000143 | Performance of machine-learning scoring functions in structure-based virtual screening. | 10.1038/srep46710 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000149 | Derivation of an amino acid similarity matrix for peptide: MHC binding and its application as a Bayesian prior. | 10.1186/1471-2105-10-394 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000148 | Deciphering HLA-I motifs across HLA peptidomes improves neo-antigen predictions and identifies allostery regulating HLA specificity. | 10.1371/journal.pcbi.1005725 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000151 | Evolution and Conservation of Plant NLR Functions. | 10.3389/fimmu.2013.00297 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000154 | Intriguing role of water in protein-ligand binding studied by neutron crystallography on trypsin complexes. | 10.1038/s41467-018-05769-2 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000155 | Localized Surface Plasmon Resonance Biosensing: Current Challenges and Approaches. | 10.3390/s150715684 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000152 | G protein-coupled receptors: structure- and function-based drug discovery. | 10.1038/s41392-020-00435-w | CC-BY-4.0 | 3 |
| biophysbridge_extra_000157 | Low-frequency and rare exome chip variants associate with fasting glucose and type 2 diabetes susceptibility. | 10.1038/ncomms6897 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000158 | Major advances in targeted protein degradation: PROTACs, LYTACs, and MADTACs. | 10.1016/j.jbc.2021.100647 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000161 | Metal-Organic Framework-Based Stimuli-Responsive Systems for Drug Delivery. | 10.1002/advs.201801526 | CC-BY-4.0 | 8 |
| biophysbridge_extra_000165 | Nanomaterials for cancer therapy: current progress and perspectives. | 10.1186/s13045-021-01096-0 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000163 | N6-methyladenosine methyltransferases: functions, regulation, and clinical potential. | 10.1186/s13045-021-01129-8 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000168 | Novel immune checkpoint targets: moving beyond PD-1 and CTLA-4. | 10.1186/s12943-019-1091-2 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000170 | Prediction of drug-target interactions and drug repositioning via network-based inference. | 10.1371/journal.pcbi.1002503 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000171 | Prospective discovery of small molecule enhancers of an E3 ligase-substrate interaction. | 10.1038/s41467-019-09358-9 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000176 | Structural Biology in the Clouds: The WeNMR-EOSC Ecosystem. | 10.3389/fmolb.2021.729513 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000174 | Radiochemistry for positron emission tomography. | 10.1038/s41467-023-36377-4 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000175 | Sex differences in severity and mortality from COVID-19: are males more vulnerable? | 10.1186/s13293-020-00330-7 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000177 | Structural, chemical and biological aspects of antioxidants for strategies against metal and metalloid exposure. | 10.4161/oxim.2.4.9112 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000188 | The role of BCL-2 family proteins in regulating apoptosis and cancer therapy. | 10.3389/fonc.2022.985363 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000189 | Towards third generation matrix metalloproteinase inhibitors for cancer therapy. | 10.1038/sj.bjc.6603043 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000190 | Tumor Microenvironment in Ovarian Cancer: Function and Therapeutic Strategy. | 10.3389/fcell.2020.00758 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000193 | Wnt/β-catenin signalling in ovarian cancer: Insights into its hyperactivation and function in tumorigenesis. | 10.1186/s13048-019-0596-z | CC-BY-4.0 | 5 |
| biophysbridge_extra_000199 | Engineering a minimal G protein to facilitate crystallisation of G protein-coupled receptors in their active conformation. | 10.1093/protein/gzw049 | CC-BY-4.0 | 8 |
| biophysbridge_extra_000194 | Cyclobutanes in Small-Molecule Drug Candidates. | 10.1002/cmdc.202200020 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000198 | Copper signalling: causes and consequences. | 10.1186/s12964-018-0277-3 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000205 | Major satellite repeat RNA stabilize heterochromatin retention of Suv39h enzymes by RNA-nucleosome association and RNA:DNA hybrid formation. | 10.7554/elife.25293 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000204 | Neutralization, effector function and immune imprinting of Omicron variants. | 10.1038/s41586-023-06487-6 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000210 | A novel co-crystal structure affords the design of gain-of-function lentiviral integrase mutants in the presence of modified PSIP1/LEDGF/p75. | 10.1371/journal.ppat.1000259 | CC-BY-4.0 | 8 |
| biophysbridge_extra_000214 | FcγR-Binding Is an Important Functional Attribute for Immune Checkpoint Antibodies in Cancer Immunotherapy. | 10.3389/fimmu.2019.00292 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000215 | P-Glycoprotein: One Mechanism, Many Tasks and the Consequences for Pharmacotherapy of Cancers. | 10.3389/fonc.2020.576559 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000217 | Resveratrol as a pan-HDAC inhibitor alters the acetylation status of histone [corrected] proteins in human-derived hepatoblastoma cells. | 10.1371/journal.pone.0073097 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000223 | RVX-208, an inducer of ApoA-I in humans, is a BET bromodomain antagonist. | 10.1371/journal.pone.0083190 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000218 | Historical and Current Adenosine Receptor Agonists in Preclinical and Clinical Development. | 10.3389/fncel.2019.00124 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000221 | <sup>44</sup>Sc-PSMA-617 for radiotheragnostics in tandem with <sup>177</sup>Lu-PSMA-617-preclinical investigations in comparison with <sup>68</sup>Ga-PSMA-11 and <sup>68</sup>Ga-PSMA-617. | 10.1186/s13550-017-0257-4 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000229 | A genetically encoded probe for imaging nascent and mature HA-tagged proteins in vivo. | 10.1038/s41467-019-10846-1 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000236 | The neuroprotective effects of glucagon-like peptide 1 in Alzheimer's and Parkinson's disease: An in-depth review. | 10.3389/fnins.2022.970925 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000237 | Therapeutic advances of targeting receptor tyrosine kinases in cancer. | 10.1038/s41392-024-01899-w | CC-BY-4.0 | 5 |
| biophysbridge_extra_000240 | Bromodomain and extraterminal (BET) proteins: biological functions, diseases, and targeted therapy. | 10.1038/s41392-023-01647-6 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000239 | Celastrol suppresses colorectal cancer via covalent targeting peroxiredoxin 1. | 10.1038/s41392-022-01231-4 | CC-BY-4.0 | 8 |
| biophysbridge_extra_000246 | Interferon-inducible mechanism of dendritic cell-mediated HIV-1 dissemination is dependent on Siglec-1/CD169. | 10.1371/journal.ppat.1003291 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000243 | Citraconate inhibits ACOD1 (IRG1) catalysis, reduces interferon responses and oxidative stress, and modulates inflammation and cell metabolism. | 10.1038/s42255-022-00577-x | CC-BY-4.0 | 8 |
| biophysbridge_extra_000247 | High mobility group box 1 (HMGB1): a pivotal regulator of hematopoietic malignancies. | 10.1186/s13045-020-00920-3 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000249 | In vitro and in vivo pharmacological activity of minor cannabinoids isolated from Cannabis sativa. | 10.1038/s41598-020-77175-y | CC-BY-4.0 | 8 |
| biophysbridge_extra_000244 | Dysregulated naive B cells and de novo autoreactivity in severe COVID-19. | 10.1038/s41586-022-05273-0 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000257 | Neoadjuvant anti-OX40 (MEDI6469) therapy in patients with head and neck squamous cell carcinoma activates and expands antigen-specific tumor-infiltrating T cells. | 10.1038/s41467-021-21383-1 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000259 | A potent broad-spectrum protective human monoclonal antibody crosslinking two haemagglutinin monomers of influenza A virus. | 10.1038/ncomms8708 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000260 | Research Progress in the Modification of Quercetin Leading to Anticancer Agents. | 10.3390/molecules22081270 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000263 | Peptide-based therapeutic cancer vaccine: Current trends in clinical application. | 10.1111/cpr.13025 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000266 | Structural basis of the activation of type 1 insulin-like growth factor receptor. | 10.1038/s41467-019-12564-0 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000269 | Cholesterol binding to ion channels. | 10.3389/fphys.2014.00065 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000265 | Sensing of autoinducer-2 by functionally distinct receptors in prokaryotes. | 10.1038/s41467-020-19243-5 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000270 | The environmental estrogen bisphenol a inhibits estradiol-induced hippocampal synaptogenesis. | 10.1289/ehp.7633 | CC0-1.0 | 6 |
| biophysbridge_extra_000273 | Targeted inhibition of STAT3 as a potential treatment strategy for atherosclerosis. | 10.7150/thno.35528 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000272 | Comparative study between transcriptionally- and translationally-acting adenine riboswitches reveals key differences in riboswitch regulatory mechanisms. | 10.1371/journal.pgen.1001278 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000276 | Therapeutic Inhibition of Myc in Cancer. Structural Bases and Computer-Aided Drug Discovery Approaches. | 10.3390/ijms20010120 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000275 | Targeting Gas6/TAM in cancer cells and tumor microenvironment. | 10.1186/s12943-018-0769-1 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000274 | The role of inflammasomes in human diseases and their potential as therapeutic targets. | 10.1038/s41392-023-01687-y | CC-BY-4.0 | 5 |
| biophysbridge_extra_000285 | Xenoestrogen-induced ERK-1 and ERK-2 activation via multiple membrane-initiated signaling pathways. | 10.1289/ehp.7175 | CC0-1.0 | 5 |
| biophysbridge_extra_000282 | The interactions between cGAS-STING pathway and pathogens. | 10.1038/s41392-020-0198-7 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000286 | Activation of mitochondrial TUFM ameliorates metabolic dysregulation through coordinating autophagy induction. | 10.1038/s42003-020-01566-0 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000290 | Arsenic targets Pin1 and cooperates with retinoic acid to inhibit cancer-driving pathways and tumor-initiating cells. | 10.1038/s41467-018-05402-2 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000289 | Application of in vitro bioaccessibility and bioavailability methods for calcium, carotenoids, folate, iron, magnesium, polyphenols, zinc, and vitamins B(6), B(12), D, and E. | 10.3389/fphys.2012.00317 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000291 | BET inhibition silences expression of MYCN and BCL2 and induces cytotoxicity in neuroblastoma tumor models. | 10.1371/journal.pone.0072967 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000292 | Broad host range of SARS-CoV-2 and the molecular basis for SARS-CoV-2 binding to cat ACE2. | 10.1038/s41421-020-00210-9 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000294 | Humanized single domain antibodies neutralize SARS-CoV-2 by targeting the spike receptor binding domain. | 10.1038/s41467-020-18387-8 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000301 | Discovery and preclinical characterization of [<sup>18</sup>F]PI-2620, a next-generation tau PET tracer for the assessment of tau pathology in Alzheimer's disease and other tauopathies. | 10.1007/s00259-019-04397-2 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000305 | Molecular determinants regulating selective binding of autophagy adapters and receptors to ATG8 proteins. | 10.1038/s41467-019-10059-6 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000303 | Emerging and Novel Functions of Complement Protein C1q. | 10.3389/fimmu.2015.00317 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000308 | Network-Based Methods for Prediction of Drug-Target Interactions. | 10.3389/fphar.2018.01134 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000309 | Lactobacillus reuteri tryptophan metabolism promotes host susceptibility to CNS autoimmunity. | 10.1186/s40168-022-01408-7 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000310 | Novel riboswitch ligand analogs as selective inhibitors of guanine-related metabolic pathways. | 10.1371/journal.ppat.1000865 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000314 | RNA:DNA hybrids are a novel molecular pattern sensed by TLR9. | 10.1002/embj.201386117 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000306 | Nanobody: a promising toolkit for molecular imaging and disease therapy. | 10.1186/s13550-021-00750-5 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000317 | Structural and biochemical basis for development of influenza virus inhibitors targeting the PA endonuclease. | 10.1371/journal.ppat.1002830 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000323 | The peri-menopause in a woman's life: a systemic inflammatory phase that enables later neurodegenerative disease. | 10.1186/s12974-020-01998-9 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000324 | The structural basis of translational control by eIF2 phosphorylation. | 10.1038/s41467-019-10167-3 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000328 | A structural model of the Staphylococcus aureus ClfA-fibrinogen interaction opens new avenues for the design of anti-staphylococcal therapeutics. | 10.1371/journal.ppat.1000226 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000331 | A deep-learning framework for multi-level peptide-protein interaction prediction. | 10.1038/s41467-021-25772-4 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000329 | Calculating an optimal box size for ligand docking and virtual screening against experimental and predicted binding pockets. | 10.1186/s13321-015-0067-5 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000058 | DockRMSD: an open-source tool for atom mapping and RMSD calculation of symmetric molecules through graph isomorphism. | 10.1186/s13321-019-0362-7 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000004 | An updated review of tyrosinase inhibitors. | 10.3390/ijms10062440 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000005 | Vinardo: A Scoring Function Based on Autodock Vina Improves Scoring, Docking, and Virtual Screening. | 10.1371/journal.pone.0155183 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000006 | Long noncoding RNA GAS5 inhibits progression of colorectal cancer by interacting with and triggering YAP phosphorylation and degradation and is negatively regulated by the m<sup>6</sup>A reader YTHDF3. | 10.1186/s12943-019-1079-y | CC-BY-4.0 | 2 |
| biophysbridge_extra_000016 | Antibody drug conjugate: the "biological missile" for targeted cancer therapy. | 10.1038/s41392-022-00947-7 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000020 | A TREM2-activating antibody with a blood-brain barrier transport vehicle enhances microglial metabolism in Alzheimer's disease models. | 10.1038/s41593-022-01240-0 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000021 | MicroRNA-Based Diagnosis and Therapy. | 10.3390/ijms23137167 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000022 | Modulation of M2 macrophage polarization by the crosstalk between Stat6 and Trim24. | 10.1038/s41467-019-12384-2 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000029 | Monoclonal Antibodies in Cancer Therapy. | 10.3390/antib9030034 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000014 | A Global Review on Short Peptides: Frontiers and Perspectives. | 10.3390/molecules26020430 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000030 | Multidrug Resistance in Cancer: Understanding Molecular Mechanisms, Immunoprevention and Therapeutic Approaches. | 10.3389/fonc.2022.891652 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000038 | Neoantigens Generated by Individual Mutations and Their Role in Cancer Immunity and Immunotherapy. | 10.3389/fimmu.2017.01679 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000044 | Chemotaxis-driven delivery of nano-pathogenoids for complete eradication of tumors post-phototherapy. | 10.1038/s41467-020-14963-0 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000042 | Brain-targeted drug delivery by manipulating protein corona functions. | 10.1038/s41467-019-11593-z | CC-BY-4.0 | 4 |
| biophysbridge_extra_000050 | Developmental and Functional Control of Natural Killer Cells by Cytokines. | 10.3389/fimmu.2017.00930 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000056 | Development of Polymeric Nanoparticles for Blood-Brain Barrier Transfer-Strategies and Challenges. | 10.1002/advs.202003937 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000059 | Differential PROTAC substrate specificity dictated by orientation of recruited E3 ligase. | 10.1038/s41467-018-08027-7 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000064 | Targeted drug delivery for cancer therapy: the other side of antibodies. | 10.1186/1756-8722-5-70 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000068 | GLP-1 receptor agonists (GLP-1RAs): cardiovascular actions and therapeutic potential. | 10.7150/ijbs.59965 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000069 | IgA subclasses have different effector functions associated with distinct glycosylation profiles. | 10.1038/s41467-019-13992-8 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000071 | The HPA - Immune Axis and the Immunomodulatory Actions of Glucocorticoids in the Brain. | 10.3389/fimmu.2014.00136 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000074 | Inhibition of PI3K/AKT and MAPK/ERK pathways causes activation of FOXO transcription factor, leading to cell cycle arrest and apoptosis in pancreatic cancer. | 10.1186/1750-2187-5-10 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000081 | Thymol and Thyme Essential Oil-New Insights into Selected Therapeutic Applications. | 10.3390/molecules25184125 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000083 | Liposomes for use in gene delivery. | 10.1155/2011/326497 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000086 | Aptamers Chemistry: Chemical Modifications and Conjugation Strategies. | 10.3390/molecules25010003 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000091 | Elabela/Toddler Is an Endogenous Agonist of the Apelin APJ Receptor in the Adult Cardiovascular System, and Exogenous Administration of the Peptide Compensates for the Downregulation of Its Expression in Pulmonary Arterial Hypertension. | 10.1161/circulationaha.116.023218 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000090 | Network-based approach to prediction and population-based validation of in silico drug repurposing. | 10.1038/s41467-018-05116-5 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000093 | Mesenchymal stem cell-derived molecules reverse fulminant hepatic failure. | 10.1371/journal.pone.0000941 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000116 | The low-density lipoprotein receptor-related protein 1 and amyloid-β clearance in Alzheimer's disease. | 10.3389/fnagi.2014.00093 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000117 | Towards a structurally resolved human protein interaction network. | 10.1038/s41594-022-00910-8 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000131 | Acquisition of human-type receptor binding specificity by new H5N1 influenza virus sublineages during their emergence in birds in Egypt. | 10.1371/journal.ppat.1002068 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000136 | Binding and neutralization of vascular endothelial growth factor (VEGF) and related ligands by VEGF Trap, ranibizumab and bevacizumab. | 10.1007/s10456-011-9249-6 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000134 | Antibodies Targeting the Transferrin Receptor 1 (TfR1) as Direct Anti-cancer Agents. | 10.3389/fimmu.2021.607692 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000138 | Exploring Leishmania secretory proteins to design B and T cell multi-epitope subunit vaccine using immunoinformatics approach. | 10.1038/s41598-017-08842-w | CC-BY-4.0 | 5 |
| biophysbridge_extra_000139 | FUT8 promotes breast cancer cell invasiveness by remodeling TGF-β receptor core fucosylation. | 10.1186/s13058-017-0904-8 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000153 | Human papillomavirus as a driver of head and neck cancers. | 10.1038/s41416-019-0602-7 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000160 | Mesenchymal stem cell-derived exosomes in cancer therapy resistance: recent advances and therapeutic potential. | 10.1186/s12943-022-01650-5 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000162 | Modulation of Immune Tolerance via Siglec-Sialic Acid Interactions. | 10.3389/fimmu.2018.02807 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000166 | Native Mass Spectrometry: What is in the Name? | 10.1007/s13361-016-1545-3 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000172 | Proteolysis-targeting chimeras (PROTACs) in cancer therapy. | 10.1186/s12943-021-01434-3 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000169 | Platelet integrin αIIbβ3: signal transduction, regulation, and its therapeutic targeting. | 10.1186/s13045-019-0709-6 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000173 | Quantitative peptide binding motifs for 19 human and mouse MHC class I molecules derived using positional scanning combinatorial peptide libraries. | 10.1186/1745-7580-4-2 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000182 | The Balance of TNF Mediated Pathways Regulates Inflammatory Cell Death Signaling in Healthy and Diseased Tissues. | 10.3389/fcell.2020.00365 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000183 | The Concept of an Ideal Antibiotic: Implications for Drug Design. | 10.3390/molecules24050892 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000181 | Telomeres and Telomere Length: A General Overview. | 10.3390/cancers12030558 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000191 | Virological characteristics of the SARS-CoV-2 XBB variant derived from recombination of two Omicron subvariants. | 10.1038/s41467-023-38435-3 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000203 | Blockade of MIF-CD74 Signalling on Macrophages and Dendritic Cells Restores the Antitumour Immune Response Against Metastatic Melanoma. | 10.3389/fimmu.2018.01132 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000200 | An anti-HER2 biparatopic antibody that induces unique HER2 clustering and complement-dependent cytotoxicity. | 10.1038/s41467-023-37029-3 | CC-BY-4.0 | 6 |
| biophysbridge_extra_000211 | Osteoporosis pathogenesis and treatment: existing and emerging avenues. | 10.1186/s11658-022-00371-3 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000208 | A covalent PIN1 inhibitor selectively targets cancer cells by a dual mechanism of action. | 10.1038/ncomms15772 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000219 | Potentiating CD8<sup>+</sup> T cell antitumor activity by inhibiting PCSK9 to promote LDLR-mediated TCR recycling and signaling. | 10.1007/s13238-021-00821-2 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000213 | Data-informed discovery of hydrolytic nanozymes. | 10.1038/s41467-022-28344-2 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000220 | Structure and antagonism of the receptor complex mediated by human TSLP in allergy and asthma. | 10.1038/ncomms14937 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000224 | Overcoming Resistance to Natural Killer Cell Based Immunotherapies for Solid Tumors. | 10.3389/fonc.2019.00051 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000226 | Bile Acids and Their Derivatives as Potential Modifiers of Drug Release and Pharmacokinetic Profiles. | 10.3389/fphar.2018.01283 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000230 | Radiation resistance in head and neck squamous cell carcinoma: dire need for an appropriate sensitizer. | 10.1038/s41388-020-1250-3 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000227 | A Klotho-derived peptide protects against kidney fibrosis by targeting TGF-β signaling. | 10.1038/s41467-022-28096-z | CC-BY-4.0 | 2 |
| biophysbridge_extra_000234 | TGF-Beta as a Master Regulator of Diabetic Nephropathy. | 10.3390/ijms22157881 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000238 | Applications of amyloid, tau, and neuroinflammation PET imaging to Alzheimer's disease and mild cognitive impairment. | 10.1002/hbm.24782 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000248 | Identification of pyrogallol as a warhead in design of covalent inhibitors for the SARS-CoV-2 3CL protease. | 10.1038/s41467-021-23751-3 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000252 | Molecular docking study of potential phytochemicals and their effects on the complex of SARS-CoV2 spike protein and human ACE2. | 10.1038/s41598-020-74715-4 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000256 | Protein acylation: mechanisms, biological functions and therapeutic targets. | 10.1038/s41392-022-01245-y | CC-BY-4.0 | 3 |
| biophysbridge_extra_000258 | Regulation of BDNF-TrkB Signaling and Potential Therapeutic Strategies for Parkinson's Disease. | 10.3390/jcm9010257 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000255 | Nano-Based Approved Pharmaceuticals for Cancer Treatment: Present and Future Challenges. | 10.3390/biom12060784 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000261 | Advance in peptide-based drug development: delivery platforms, therapeutics and vaccines. | 10.1038/s41392-024-02107-5 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000281 | Zinc transporter ZIP14 functions in hepatic zinc, iron and glucose homeostasis during the innate immune response (endotoxemia). | 10.1371/journal.pone.0048679 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000288 | Application of Fragment-Based Drug Discovery to Versatile Targets. | 10.3389/fmolb.2020.00180 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000284 | <i>In vivo</i> genome editing in animals using AAV-CRISPR system: applications to translational research of human disease. | 10.12688/f1000research.11243.1 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000295 | Computer-Aided Design of Antimicrobial Peptides: Are We Generating Effective Drug Candidates? | 10.3389/fmicb.2019.03097 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000296 | Pseudomonas aeruginosa pili and flagella mediate distinct binding and signaling events at the apical and basolateral surface of airway epithelium. | 10.1371/journal.ppat.1002616 | CC-BY-4.0 | 7 |
| biophysbridge_extra_000307 | In utero nanoparticle delivery for site-specific genome editing. | 10.1038/s41467-018-04894-2 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000312 | Normal Aging Induces Changes in the Brain and Neurodegeneration Progress: Review of the Structural, Biochemical, Metabolic, Cellular, and Molecular Changes. | 10.3389/fnagi.2022.931536 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000313 | RGD peptide in cancer targeting: Benefits, challenges, solutions, and possible integrin-RGD interactions. | 10.1002/cam4.6800 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000315 | Structural Features of Tight-Junction Proteins. | 10.3390/ijms20236020 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000325 | Tuning the dynamic range of bacterial promoters regulated by ligand-inducible transcription factors. | 10.1038/s41467-017-02473-5 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000321 | Systems Pharmacology for Investigation of the Mechanisms of Action of Traditional Chinese Medicine in Drug Discovery. | 10.3389/fphar.2019.00743 | CC-BY-4.0 | 2 |
| biophysbridge_extra_000330 | A comprehensive review on plasmonic-based biosensors used in viral diagnostics. | 10.1038/s42003-020-01615-8 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000333 | A metabolic signature of long life in Caenorhabditis elegans. | 10.1186/1741-7007-8-14 | CC-BY-4.0 | 1 |
| biophysbridge_extra_000322 | The sphingolipid receptor S1PR2 is a receptor for Nogo-a repressing synaptic plasticity. | 10.1371/journal.pbio.1001763 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000336 | Ligand pose and orientational sampling in molecular docking. | 10.1371/journal.pone.0075992 | CC-BY-4.0 | 4 |
| biophysbridge_extra_000335 | An in silico deep learning approach to multi-epitope vaccine design: a SARS-CoV-2 case study. | 10.1038/s41598-021-81749-9 | CC-BY-4.0 | 6 |
| biophysbridge_batch001_000008 | Growth Factor Engineering Strategies for Regenerative Medicine Applications. | 10.3389/fbioe.2019.00469 | CC-BY-4.0 | 6 |
| biophysbridge_batch002_000027 | PROTACs: great opportunities for academia and industry (an update from 2020 to 2021). | 10.1038/s41392-022-00999-9 | CC-BY-4.0 | 8 |
| biophysbridge_batch003_000081 | Recent progress on magnetic iron oxide nanoparticles: synthesis, surface functional strategies and biomedical applications. | 10.1088/1468-6996/16/2/023501 | CC-BY-4.0 | 6 |
| biophysbridge_batch004_000029 | The pharmacology and therapeutic applications of monoclonal antibodies. | 10.1002/prp2.535 | CC-BY-4.0 | 3 |
| biophysbridge_extra_000089 | Theory and applications of differential scanning fluorimetry in early-stage drug discovery. | 10.1007/s12551-020-00619-2 | CC-BY-4.0 | 5 |
| biophysbridge_extra_000287 | Recent developments in epigenetic cancer therapeutics: clinical advancement and emerging trends. | 10.1186/s12929-021-00721-x | CC-BY-4.0 | 5 |
| biophysbridge_extra_000241 | Cordycepin prevents radiation ulcer by inhibiting cell senescence via NRF2 and AMPK in rodents. | 10.1038/s41467-019-10386-8 | CC-BY-4.0 | 3 |

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
- cases: 500
- schema_valid_rate: 1.000
- quantitative_evidence_rate: 1.000
- unit_normalization_success_rate: 1.000
- source_license_coverage: 1.000
- manual_review_pass_rate: 1.000
- expert_annotation_n: 81
- expert_annotation_draft_n: 0
- release_expert_annotation_coverage: 0.162
- test_expert_annotation_coverage: 1.000
- evidence_coverage_rate: 1.000
- sci_evo_completeness_score: 0.883
- release_content_quality_pass_rate: 1.000
- gold_expert_annotation_coverage: 1.000
- equation_bearing_coverage: 1.000
- physics_consistency_audit_coverage: 1.000
- physics_consistency_checked_rate: 0.020
- physics_consistency_pass_rate: 0.800
- mean_modalities_per_case: 2.944
- cases_with_3plus_modalities_rate: 0.804
- failure_or_revision_n: 107
- cases_with_failure_or_revision_rate: 0.214

See `biophys_bridge_metadata.json` for the full metric set and
`biophys_bridge_schema.json` for the canonical JSON Schema.

## Out-of-scope use
- Clinical diagnosis or any safety-critical decision making.
- Using extracted values without checking the cited `evidence_id`.
- Use as a drug-discovery oracle.

## Known limitations
- Covers 6 of 6 schema domains; coverage reflects the
  source-paper set, not the full domain space.
- `failure_or_revision` is populated only where the source paper actually reports
  a failure/revision (never fabricated). Those 107 cases are the core dynamic
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
- The 10 contest gold samples, 30 extended-gold samples, and 50 held-out test
  cases include reviewed `expert_annotation` blocks with physics reasoning,
  biological reasoning, uncertainty, and reviewer notes. Expert annotations are
  counted separately from release-gate review status.
- Release export rejects unresolved template markers, character-split
  tool/skill vocabularies, weak task prompts, and missing `next_step` stages.
- Some MinerU table parses can miss footnoted assay conditions.

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
