# Where the 24 usable models disagree

Population std dev of the per-model mean score, over the 24 usable models (every preprint scored within the repeats, ceiling excluded). `ceiling` is the ceiling's own mean.

## Top 10 most disputed

| # | sd | ceiling | min (model) | max (model) | category / lane | title | doi |
|--:|--:|--:|---|---|---|---|---|
| 1 | 0.191 | 0.17 | 0.08 (minimax/minimax-m3@low) | 0.74 (upstage/solar-mini4) | plant biology / off | Tissue Context Shapes the Circadian Transcriptome of the Arabidopsis Leaf | 10.1101/2025.06.12.659411 |
| 2 | 0.184 | 0.10 | 0.07 (tencent/hy3) | 1.00 (baseline:tfidf) | plant biology / off | Barley genetic architecture conditionally impacts recruitment of rhizosphere microorganisms and crop performance has bee | 10.1101/2024.11.21.624704 |
| 3 | 0.174 | 0.63 | 0.22 (tencent/hy3) | 0.93 (openai/gpt-5.6-luna) | genomics / in | Haplotype-Resolved Long-Read Sequencing in Hundreds of Diverse Brains Identifies Structural Variant Impacts on Expressio | 10.1101/2024.12.16.628723 |
| 4 | 0.171 | 0.15 | 0.12 (baseline:tfidf) | 0.81 (openai/gpt-6-luna) | genomics / in | Mapping the Phenotypic Landscape of Beta-lactam Resistance in Streptococcus pneumoniae | 10.1101/2025.09.12.675231 |
| 5 | 0.161 | 0.43 | 0.27 (deepseek/deepseek-v4-flash-0731@medium) | 0.87 (openai/gpt-5.6-luna) | genomics / in | Telomere-to-Telomere Accurate and Gapless Korean Standard Reference Genome | 10.1101/2025.11.17.688257 |
| 6 | 0.161 | 0.27 | 0.28 (inception/mercury-2.5) | 0.88 (openai/gpt-5.6-luna) | systems biology / in | Analytical resolution governs cross-laboratory and cross-species concordance in murine cardiometabolic HFpEF transcripto | 10.64898/2026.04.30.721824 |
| 7 | 0.160 | 0.15 | 0.13 (tencent/hy3) | 0.74 (openai/gpt-6-luna) | genomics / in | Allelic coverage analyses reveal a high proportion and uneven chromosomal distribution of SNPs associated with polymorph | 10.1101/2025.06.24.661118 |
| 8 | 0.154 | 0.25 | 0.25 (tencent/hy3) | 0.84 (openai/gpt-5.6-luna) | genomics / in | Spatial mapping of cellular and molecular plasticity in the maternal and postpartum mouse brain | 10.64898/2026.01.03.697464 |
| 9 | 0.154 | 0.10 | 0.04 (minimax/minimax-m3@low) | 0.79 (upstage/solar-mini4) | plant biology / off | Transcription Start Site Heterogeneity Confounds the Landscape and Functional Interpretation of uORFs | 10.1101/2024.04.25.591216 |
| 10 | 0.153 | 0.10 | 0.13 (google/gemini-3.5-flash-lite) | 0.75 (qwen/qwen3.8-flash) | bioinformatics / in | Real-time repository-scale spectral search and global molecular networking with HNSW-MS | 10.64898/2026.06.02.729602 |

## Top 10 most agreed

| # | sd | ceiling | min (model) | max (model) | category / lane | title | doi |
|--:|--:|--:|---|---|---|---|---|
| 1 | 0.023 | 0.02 | 0.00 (deepseek/deepseek-v4-flash-0731@medium) | 0.10 (upstage/solar-mini4) | paleontology / off | Garamaudo bauciensis, a new freshwater Mosasauridae (Reptilia, Squamata) from the Santonian (Late Cretaceous) of Provenc | 10.64898/2025.12.11.693649 |
| 2 | 0.033 | 0.04 | 0.00 (ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash) | 0.13 (baseline:tfidf) | animal behavior and cognition / off | Reward quantity discrimination in an associative learning task in wild zebrafish (Danio rerio) | 10.1101/2022.03.17.484678 |
| 3 | 0.035 | 0.03 | 0.00 (ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash) | 0.12 (deepseek/deepseek-v4-flash-0731@low) | zoology / off | The impact of temperature-induced vertebral anomalies on C-start swimming performance in Astyanax mexicanus (Teleostei:  | 10.64898/2026.08.06.743195 |
| 4 | 0.037 | 0.03 | 0.00 (baseline:tfidf) | 0.15 (upstage/solar-mini4) | animal behavior and cognition / off | Spectrograms of kent sounds from seven Ivory-billed Woodpecker expeditions show 587 Hertz as a pattern | 10.1101/2024.05.07.592969 |
| 5 | 0.038 | 0.03 | 0.00 (ens:hy3+deepseek-v4-flash-0731@medium+mimo-v2.5) | 0.12 (inception/mercury-2.5#schema) | animal behavior and cognition / off | Shifting sensitivity and signal-dependent timing in the copulatory displays of songbirds | 10.1101/2021.05.19.444794 |
| 6 | 0.039 | 0.03 | 0.00 (google/gemini-3.5-flash-lite) | 0.17 (xiaomi/mimo-v2.6-flash) | zoology / off | A Characterisation of the Invasive Lema Beetle, Lema equestris (Coleoptera: Chrysomelidae), in Hawaii | 10.64898/2026.04.28.721477 |
| 7 | 0.039 | 0.05 | 0.03 (minimax/minimax-m3@low) | 0.21 (deepseek/deepseek-v4-flash-0731) | microbiology / in | Enterococcus faecalis biofilm rewires neutrophil metabolism to suppress antimicrobial activity | 10.64898/2026.06.18.733107 |
| 8 | 0.039 | 0.03 | 0.00 (tencent/hy3) | 0.17 (deepseek/deepseek-v4-flash-0731) | neuroscience / off | Genetic screening identifies glial adenosine as a therapeutic target in alpha-synucleinopathy | 10.1101/2024.05.15.594309 |
| 9 | 0.040 | 0.03 | 0.00 (ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash) | 0.15 (anthropic/claude-haiku-4.5) | animal behavior and cognition / off | Serotonin signaling in the rat prefrontal cortex is required for Retrieval-Induced Forgetting | 10.1101/2025.03.05.641624 |
| 10 | 0.041 | 0.04 | 0.00 (tencent/hy3) | 0.17 (deepseek/deepseek-v4-flash-0731) | systems biology / in | Systems analysis reveals neuregulin-1 control of cardiomyocyte size and shape mediated by distinct PI3K and p38 pathways | 10.1101/2025.10.01.679873 |
