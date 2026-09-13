# Where the 19 usable models disagree

Population std dev of the per-model mean score, over the 19 usable models (>= 99% coverage, ceiling excluded). `ceiling` is the ceiling's own mean.

## Top 10 most disputed

| # | sd | ceiling | min (model) | max (model) | category / lane | title | doi |
|--:|--:|--:|---|---|---|---|---|
| 1 | 0.197 | 0.10 | 0.07 (tencent/hy3) | 1.00 (baseline:tfidf) | plant biology / off | Barley genetic architecture conditionally impacts recruitment of rhizosphere microorganisms and crop performance has bee | 10.1101/2024.11.21.624704 |
| 2 | 0.190 | 0.63 | 0.22 (tencent/hy3) | 0.93 (openai/gpt-5.6-luna) | genomics / in | Haplotype-Resolved Long-Read Sequencing in Hundreds of Diverse Brains Identifies Structural Variant Impacts on Expressio | 10.1101/2024.12.16.628723 |
| 3 | 0.170 | 0.25 | 0.25 (tencent/hy3) | 0.84 (openai/gpt-5.6-luna) | genomics / in | Spatial mapping of cellular and molecular plasticity in the maternal and postpartum mouse brain | 10.64898/2026.01.03.697464 |
| 4 | 0.163 | 0.43 | 0.27 (deepseek/deepseek-v4-flash-0731@medium) | 0.87 (openai/gpt-5.6-luna) | genomics / in | Telomere-to-Telomere Accurate and Gapless Korean Standard Reference Genome | 10.1101/2025.11.17.688257 |
| 5 | 0.160 | 0.27 | 0.28 (inception/mercury-2.5) | 0.88 (openai/gpt-5.6-luna) | systems biology / in | Analytical resolution governs cross-laboratory and cross-species concordance in murine cardiometabolic HFpEF transcripto | 10.64898/2026.04.30.721824 |
| 6 | 0.153 | 0.17 | 0.08 (qwen/qwen3.8-flash) | 0.66 (anthropic/claude-haiku-4.5#schema) | plant biology / off | Tissue Context Shapes the Circadian Transcriptome of the Arabidopsis Leaf | 10.1101/2025.06.12.659411 |
| 7 | 0.150 | 0.18 | 0.25 (inception/mercury-2.5#schema) | 0.86 (openai/gpt-5.6-luna) | microbiology / in | Diversity of Novel Bacteriophages Infecting Ammonia-Oxidizing Bacteria | 10.64898/2026.05.02.722434 |
| 8 | 0.150 | 0.15 | 0.12 (baseline:tfidf) | 0.71 (google/gemini-3.5-flash-lite) | genomics / in | Mapping the Phenotypic Landscape of Beta-lactam Resistance in Streptococcus pneumoniae | 10.1101/2025.09.12.675231 |
| 9 | 0.147 | 0.62 | 0.23 (baseline:tfidf) | 0.91 (openai/gpt-5.6-luna) | microbiology / in | The Updateable Human Virome Database and toolkit: A novel framework for human virome analysis | 10.64898/2026.05.01.722327 |
| 10 | 0.145 | 0.10 | 0.13 (google/gemini-3.5-flash-lite) | 0.75 (qwen/qwen3.8-flash) | bioinformatics / in | Real-time repository-scale spectral search and global molecular networking with HNSW-MS | 10.64898/2026.06.02.729602 |

## Top 10 most agreed

| # | sd | ceiling | min (model) | max (model) | category / lane | title | doi |
|--:|--:|--:|---|---|---|---|---|
| 1 | 0.016 | 0.02 | 0.00 (deepseek/deepseek-v4-flash-0731@medium) | 0.05 (inception/mercury-2.5) | paleontology / off | Garamaudo bauciensis, a new freshwater Mosasauridae (Reptilia, Squamata) from the Santonian (Late Cretaceous) of Provenc | 10.64898/2025.12.11.693649 |
| 2 | 0.029 | 0.03 | 0.00 (google/gemini-3.5-flash-lite) | 0.11 (baseline:tfidf) | zoology / off | A Characterisation of the Invasive Lema Beetle, Lema equestris (Coleoptera: Chrysomelidae), in Hawaii | 10.64898/2026.04.28.721477 |
| 3 | 0.029 | 0.03 | 0.00 (baseline:tfidf) | 0.10 (inception/mercury-2.5) | animal behavior and cognition / off | Spectrograms of kent sounds from seven Ivory-billed Woodpecker expeditions show 587 Hertz as a pattern | 10.1101/2024.05.07.592969 |
| 4 | 0.036 | 0.03 | 0.00 (ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash) | 0.12 (deepseek/deepseek-v4-flash-0731@low) | zoology / off | The impact of temperature-induced vertebral anomalies on C-start swimming performance in Astyanax mexicanus (Teleostei:  | 10.64898/2026.08.06.743195 |
| 5 | 0.036 | 0.04 | 0.00 (ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash) | 0.13 (baseline:tfidf) | animal behavior and cognition / off | Reward quantity discrimination in an associative learning task in wild zebrafish (Danio rerio) | 10.1101/2022.03.17.484678 |
| 6 | 0.036 | n/a | 0.05 (xiaomi/mimo-v2.5) | 0.18 (baseline:tfidf) | microbiology / in | Field-isolate recombinant tick-borne encephalitis viruses define reporter-stability guidelines for antiviral testing in  | 10.64898/2026.02.23.707037 |
| 7 | 0.037 | 0.04 | 0.00 (tencent/hy3) | 0.15 (anthropic/claude-haiku-4.5) | systems biology / in | Diurnal rhythmicity in metabolism and salivary effector expression shapes aphid performance on host plants | 10.1101/2024.01.20.576473 |
| 8 | 0.037 | 0.03 | 0.03 (baseline:tfidf) | 0.19 (deepseek/deepseek-v4-flash-0731) | biophysics / off | Hierarchical Heterogeneities in Spatiotemporal Dynamics of the Cytoplasm | 10.1101/2025.05.08.652886 |
| 9 | 0.038 | 0.03 | 0.00 (ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash) | 0.15 (anthropic/claude-haiku-4.5) | animal behavior and cognition / off | Serotonin signaling in the rat prefrontal cortex is required for Retrieval-Induced Forgetting | 10.1101/2025.03.05.641624 |
| 10 | 0.038 | 0.03 | 0.00 (ens:hy3+deepseek-v4-flash-0731@medium+mimo-v2.5) | 0.12 (inception/mercury-2.5#schema) | animal behavior and cognition / off | Shifting sensitivity and signal-dependent timing in the copulatory displays of songbirds | 10.1101/2021.05.19.444794 |
