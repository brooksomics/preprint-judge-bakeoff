# Where the 12 usable models disagree

Population std dev of the per-model mean score, over the 12 usable models (>= 99% coverage, ceiling excluded). `ceiling` is the ceiling's own mean.

## Top 10 most disputed

| # | sd | ceiling | min (model) | max (model) | category / lane | title | doi |
|--:|--:|--:|---|---|---|---|---|
| 1 | 0.200 | 0.63 | 0.22 (tencent/hy3) | 0.93 (openai/gpt-5.6-luna) | genomics / in | Haplotype-Resolved Long-Read Sequencing in Hundreds of Diverse Brains Identifies Structural Variant Impacts on Expressio | 10.1101/2024.12.16.628723 |
| 2 | 0.181 | 0.43 | 0.27 (deepseek/deepseek-v4-flash-0731@medium) | 0.87 (openai/gpt-5.6-luna) | genomics / in | Telomere-to-Telomere Accurate and Gapless Korean Standard Reference Genome | 10.1101/2025.11.17.688257 |
| 3 | 0.176 | 0.27 | 0.28 (inception/mercury-2.5) | 0.88 (openai/gpt-5.6-luna) | systems biology / in | Analytical resolution governs cross-laboratory and cross-species concordance in murine cardiometabolic HFpEF transcripto | 10.64898/2026.04.30.721824 |
| 4 | 0.174 | 0.25 | 0.25 (tencent/hy3) | 0.84 (openai/gpt-5.6-luna) | genomics / in | Spatial mapping of cellular and molecular plasticity in the maternal and postpartum mouse brain | 10.64898/2026.01.03.697464 |
| 5 | 0.171 | 0.37 | 0.17 (deepseek/deepseek-v4-flash-0731@low) | 0.82 (google/gemini-3.5-flash-lite) | genomics / in | Genetic association data are broadly consistent with stabilizing selection shaping human common diseases and traits | 10.1101/2024.06.19.599789 |
| 6 | 0.167 | 0.10 | 0.13 (google/gemini-3.5-flash-lite) | 0.75 (qwen/qwen3.8-flash) | bioinformatics / in | Real-time repository-scale spectral search and global molecular networking with HNSW-MS | 10.64898/2026.06.02.729602 |
| 7 | 0.165 | 0.33 | 0.20 (deepseek/deepseek-v4-flash-0731@medium) | 0.82 (google/gemini-3.5-flash-lite) | bioinformatics / in | Interpolating and Extrapolating Node Counts in Colored Compacted de Bruijn Graphs for Pangenome Diversity | 10.64898/2026.03.16.711983 |
| 8 | 0.155 | 0.18 | 0.36 (anthropic/claude-haiku-4.5) | 0.86 (openai/gpt-5.6-luna) | microbiology / in | Diversity of Novel Bacteriophages Infecting Ammonia-Oxidizing Bacteria | 10.64898/2026.05.02.722434 |
| 9 | 0.154 | 0.15 | 0.20 (deepseek/deepseek-v4-flash-0731@low) | 0.71 (google/gemini-3.5-flash-lite) | genomics / in | Mapping the Phenotypic Landscape of Beta-lactam Resistance in Streptococcus pneumoniae | 10.1101/2025.09.12.675231 |
| 10 | 0.153 | 0.15 | 0.30 (deepseek/deepseek-v4-flash-0731@medium) | 0.85 (openai/gpt-5.6-luna) | bioinformatics / in | NetSyn: prokaryotic genomic context exploration of protein families | 10.1101/2023.02.15.528638 |

## Top 10 most agreed

| # | sd | ceiling | min (model) | max (model) | category / lane | title | doi |
|--:|--:|--:|---|---|---|---|---|
| 1 | 0.015 | 0.02 | 0.00 (deepseek/deepseek-v4-flash-0731@medium) | 0.05 (inception/mercury-2.5) | paleontology / off | Garamaudo bauciensis, a new freshwater Mosasauridae (Reptilia, Squamata) from the Santonian (Late Cretaceous) of Provenc | 10.64898/2025.12.11.693649 |
| 2 | 0.024 | 0.04 | 0.00 (google/gemini-3.5-flash-lite) | 0.10 (deepseek/deepseek-v4-flash-0731@low) | zoology / off | New Approaches to Fast Plate Composition, with a Software Implementation for Taxonomy | 10.64898/2026.07.07.736512 |
| 3 | 0.027 | 0.03 | 0.00 (google/gemini-3.5-flash-lite) | 0.10 (inception/mercury-2.5) | zoology / off | A Characterisation of the Invasive Lema Beetle, Lema equestris (Coleoptera: Chrysomelidae), in Hawaii | 10.64898/2026.04.28.721477 |
| 4 | 0.030 | 0.03 | 0.00 (google/gemini-3.5-flash-lite) | 0.10 (inception/mercury-2.5) | animal behavior and cognition / off | Spectrograms of kent sounds from seven Ivory-billed Woodpecker expeditions show 587 Hertz as a pattern | 10.1101/2024.05.07.592969 |
| 5 | 0.030 | 0.04 | 0.00 (google/gemini-3.5-flash-lite) | 0.10 (deepseek/deepseek-v4-flash-0731) | animal behavior and cognition / off | Reward quantity discrimination in an associative learning task in wild zebrafish (Danio rerio) | 10.1101/2022.03.17.484678 |
| 6 | 0.033 | 0.03 | 0.00 (google/gemini-3.5-flash-lite) | 0.10 (deepseek/deepseek-v4-flash-0731) | ecology / off | Diversity and Community Structure of Collembola (Hexapoda) across sites and microhabitats in the Bula Protected Area, a  | 10.1101/2025.05.20.650270 |
| 7 | 0.034 | 0.03 | 0.00 (google/gemini-3.5-flash-lite) | 0.10 (deepseek/deepseek-v4-flash-0731) | paleontology / off | Constraining Palaeogeography and Palaeotides for the Cambrian using cnidarian medusae | 10.64898/2026.08.27.747545 |
| 8 | 0.034 | 0.00 | 0.00 (anthropic/claude-haiku-4.5) | 0.12 (deepseek/deepseek-v4.1-flash) | neuroscience / off | WITHDRAWN: Multisensory learning binds modality-specific neurons into a cross-modal memory engram | 10.1101/2022.07.08.499174 |
| 9 | 0.034 | 0.04 | 0.00 (tencent/hy3) | 0.15 (anthropic/claude-haiku-4.5) | systems biology / in | Diurnal rhythmicity in metabolism and salivary effector expression shapes aphid performance on host plants | 10.1101/2024.01.20.576473 |
| 10 | 0.036 | 0.03 | 0.00 (google/gemini-3.5-flash-lite) | 0.10 (inception/mercury-2.5) | animal behavior and cognition / off | Shifting sensitivity and signal-dependent timing in the copulatory displays of songbirds | 10.1101/2021.05.19.444794 |
