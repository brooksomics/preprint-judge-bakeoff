Verdict rule: reliable iff kappa_0.5 >= 0.6 and n >= 8.

| model | category | n | kappa_0.5 | band | alpha_ord | verdict |
|---|---|--:|--:|---|--:|---|
| anthropic/claude-haiku-4.5 | bioinformatics | 14 | 0.00 | slight | 0.32 | not reliable |
| anthropic/claude-haiku-4.5 | genomics | 15 | 0.59 | moderate | 0.70 | not reliable |
| anthropic/claude-haiku-4.5 | microbiology | 12 | 0.62 | substantial | 0.66 | reliable |
| anthropic/claude-haiku-4.5 | off-lane | 30 | 1.00 | almost perfect | 0.18 | reliable |
| anthropic/claude-haiku-4.5 | systems biology | 15 | 0.63 | substantial | 0.67 | reliable |
| anthropic/claude-haiku-4.5 | all | 86 | 0.50 | moderate | 0.65 | not reliable |
| anthropic/claude-haiku-4.5#schema | bioinformatics | 14 | 0.00 | slight | 0.18 | not reliable |
| anthropic/claude-haiku-4.5#schema | genomics | 15 | 0.47 | moderate | 0.57 | not reliable |
| anthropic/claude-haiku-4.5#schema | microbiology | 12 | 0.62 | substantial | 0.58 | reliable |
| anthropic/claude-haiku-4.5#schema | off-lane | 30 | 0.00 | slight | 0.25 | not reliable |
| anthropic/claude-haiku-4.5#schema | systems biology | 15 | 0.44 | moderate | 0.59 | not reliable |
| anthropic/claude-haiku-4.5#schema | all | 86 | 0.38 | fair | 0.55 | not reliable |
| baseline:tfidf | bioinformatics | 14 | 0.00 | slight | -0.00 | not reliable |
| baseline:tfidf | genomics | 15 | 0.76 | substantial | 0.58 | reliable |
| baseline:tfidf | microbiology | 12 | -0.09 | worse than chance | 0.06 | not reliable |
| baseline:tfidf | off-lane | 30 | 0.00 | slight | -0.19 | not reliable |
| baseline:tfidf | systems biology | 15 | -0.11 | worse than chance | 0.23 | not reliable |
| baseline:tfidf | all | 86 | 0.21 | fair | 0.19 | not reliable |
| deepseek/deepseek-v4-flash-0731 | bioinformatics | 14 | 0.00 | slight | -0.23 | not reliable |
| deepseek/deepseek-v4-flash-0731 | genomics | 15 | 0.47 | moderate | 0.56 | not reliable |
| deepseek/deepseek-v4-flash-0731 | microbiology | 12 | 0.62 | substantial | 0.52 | reliable |
| deepseek/deepseek-v4-flash-0731 | off-lane | 30 | 0.00 | slight | 0.12 | not reliable |
| deepseek/deepseek-v4-flash-0731 | systems biology | 15 | 0.44 | moderate | 0.56 | not reliable |
| deepseek/deepseek-v4-flash-0731 | all | 86 | 0.43 | moderate | 0.46 | not reliable |
| deepseek/deepseek-v4-flash-0731@low | bioinformatics | 14 | 0.00 | slight | 0.24 | not reliable |
| deepseek/deepseek-v4-flash-0731@low | genomics | 15 | 0.76 | substantial | 0.80 | reliable |
| deepseek/deepseek-v4-flash-0731@low | microbiology | 12 | 0.43 | moderate | 0.65 | not reliable |
| deepseek/deepseek-v4-flash-0731@low | off-lane | 30 | 1.00 | almost perfect | 0.12 | reliable |
| deepseek/deepseek-v4-flash-0731@low | systems biology | 15 | 0.63 | substantial | 0.79 | reliable |
| deepseek/deepseek-v4-flash-0731@low | all | 86 | 0.54 | moderate | 0.69 | not reliable |
| deepseek/deepseek-v4-flash-0731@medium | bioinformatics | 14 | 0.00 | slight | 0.28 | not reliable |
| deepseek/deepseek-v4-flash-0731@medium | genomics | 15 | 0.76 | substantial | 0.74 | reliable |
| deepseek/deepseek-v4-flash-0731@medium | microbiology | 12 | 0.43 | moderate | 0.62 | not reliable |
| deepseek/deepseek-v4-flash-0731@medium | off-lane | 30 | 1.00 | almost perfect | 0.21 | reliable |
| deepseek/deepseek-v4-flash-0731@medium | systems biology | 15 | 0.63 | substantial | 0.83 | reliable |
| deepseek/deepseek-v4-flash-0731@medium | all | 86 | 0.54 | moderate | 0.70 | not reliable |
| deepseek/deepseek-v4.1-flash | bioinformatics | 14 | 0.00 | slight | 0.04 | not reliable |
| deepseek/deepseek-v4.1-flash | genomics | 15 | 0.37 | fair | 0.59 | not reliable |
| deepseek/deepseek-v4.1-flash | microbiology | 12 | 0.62 | substantial | 0.65 | reliable |
| deepseek/deepseek-v4.1-flash | off-lane | 30 | 1.00 | almost perfect | 0.20 | reliable |
| deepseek/deepseek-v4.1-flash | systems biology | 15 | 0.63 | substantial | 0.73 | reliable |
| deepseek/deepseek-v4.1-flash | all | 86 | 0.40 | fair | 0.58 | not reliable |
| ens:hy3+deepseek-v4-flash-0731@medium+mimo-v2.5 | bioinformatics | 14 | 0.00 | slight | 0.34 | not reliable |
| ens:hy3+deepseek-v4-flash-0731@medium+mimo-v2.5 | genomics | 15 | 0.76 | substantial | 0.78 | reliable |
| ens:hy3+deepseek-v4-flash-0731@medium+mimo-v2.5 | microbiology | 12 | 0.43 | moderate | 0.70 | not reliable |
| ens:hy3+deepseek-v4-flash-0731@medium+mimo-v2.5 | off-lane | 30 | 1.00 | almost perfect | 0.41 | reliable |
| ens:hy3+deepseek-v4-flash-0731@medium+mimo-v2.5 | systems biology | 15 | 0.44 | moderate | 0.74 | not reliable |
| ens:hy3+deepseek-v4-flash-0731@medium+mimo-v2.5 | all | 86 | 0.46 | moderate | 0.73 | not reliable |
| ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash | bioinformatics | 14 | 0.00 | slight | 0.25 | not reliable |
| ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash | genomics | 15 | 0.59 | moderate | 0.72 | not reliable |
| ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash | microbiology | 12 | 0.43 | moderate | 0.73 | not reliable |
| ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash | off-lane | 30 | 1.00 | almost perfect | 0.37 | reliable |
| ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash | systems biology | 15 | 0.63 | substantial | 0.73 | reliable |
| ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash | all | 86 | 0.46 | moderate | 0.71 | not reliable |
| ens:hy3+mimo-v2.5+mercury-2.5 | bioinformatics | 14 | 0.00 | slight | 0.23 | not reliable |
| ens:hy3+mimo-v2.5+mercury-2.5 | genomics | 15 | 0.42 | moderate | 0.75 | not reliable |
| ens:hy3+mimo-v2.5+mercury-2.5 | microbiology | 12 | 0.62 | substantial | 0.73 | reliable |
| ens:hy3+mimo-v2.5+mercury-2.5 | off-lane | 30 | 1.00 | almost perfect | 0.31 | reliable |
| ens:hy3+mimo-v2.5+mercury-2.5 | systems biology | 15 | 0.44 | moderate | 0.67 | not reliable |
| ens:hy3+mimo-v2.5+mercury-2.5 | all | 86 | 0.36 | fair | 0.68 | not reliable |
| google/gemini-3.5-flash-lite | bioinformatics | 14 | 0.00 | slight | 0.32 | not reliable |
| google/gemini-3.5-flash-lite | genomics | 15 | 0.47 | moderate | 0.59 | not reliable |
| google/gemini-3.5-flash-lite | microbiology | 12 | 0.62 | substantial | 0.56 | reliable |
| google/gemini-3.5-flash-lite | off-lane | 30 | 1.00 | almost perfect | 0.27 | reliable |
| google/gemini-3.5-flash-lite | systems biology | 15 | 0.44 | moderate | 0.61 | not reliable |
| google/gemini-3.5-flash-lite | all | 86 | 0.50 | moderate | 0.62 | not reliable |
| inception/mercury-2.5 | bioinformatics | 14 | 0.00 | slight | 0.00 | not reliable |
| inception/mercury-2.5 | genomics | 15 | 0.42 | moderate | 0.74 | not reliable |
| inception/mercury-2.5 | microbiology | 12 | 0.62 | substantial | 0.66 | reliable |
| inception/mercury-2.5 | off-lane | 30 | 1.00 | almost perfect | 0.04 | reliable |
| inception/mercury-2.5 | systems biology | 15 | 0.44 | moderate | 0.62 | not reliable |
| inception/mercury-2.5 | all | 86 | 0.33 | fair | 0.59 | not reliable |
| inception/mercury-2.5#schema | bioinformatics | 14 | 0.00 | slight | 0.01 | not reliable |
| inception/mercury-2.5#schema | genomics | 15 | 0.63 | substantial | 0.70 | reliable |
| inception/mercury-2.5#schema | microbiology | 12 | 0.62 | substantial | 0.67 | reliable |
| inception/mercury-2.5#schema | off-lane | 30 | 1.00 | almost perfect | -0.10 | reliable |
| inception/mercury-2.5#schema | systems biology | 15 | 0.44 | moderate | 0.60 | not reliable |
| inception/mercury-2.5#schema | all | 86 | 0.36 | fair | 0.57 | not reliable |
| minimax/minimax-m3 | bioinformatics | 14 | 0.00 | slight | 0.24 | not reliable |
| minimax/minimax-m3 | genomics | 15 | 0.37 | fair | 0.77 | not reliable |
| minimax/minimax-m3 | microbiology | 12 | 0.43 | moderate | 0.69 | not reliable |
| minimax/minimax-m3 | off-lane | 30 | 1.00 | almost perfect | 0.37 | reliable |
| minimax/minimax-m3 | systems biology | 15 | 0.44 | moderate | 0.75 | not reliable |
| minimax/minimax-m3 | all | 86 | 0.38 | fair | 0.69 | not reliable |
| minimax/minimax-m3@low | bioinformatics | 14 | 0.00 | slight | 0.41 | not reliable |
| minimax/minimax-m3@low | genomics | 15 | 0.59 | moderate | 0.83 | not reliable |
| minimax/minimax-m3@low | microbiology | 12 | 0.43 | moderate | 0.74 | not reliable |
| minimax/minimax-m3@low | off-lane | 30 | 1.00 | almost perfect | 0.60 | reliable |
| minimax/minimax-m3@low | systems biology | 15 | 0.44 | moderate | 0.81 | not reliable |
| minimax/minimax-m3@low | all | 86 | 0.46 | moderate | 0.79 | not reliable |
| openai/gpt-5.6-luna | bioinformatics | 14 | 0.00 | slight | 0.02 | not reliable |
| openai/gpt-5.6-luna | genomics | 15 | 0.30 | fair | 0.32 | not reliable |
| openai/gpt-5.6-luna | microbiology | 12 | 0.23 | fair | 0.32 | not reliable |
| openai/gpt-5.6-luna | off-lane | 30 | 0.00 | slight | 0.32 | not reliable |
| openai/gpt-5.6-luna | systems biology | 15 | 0.33 | fair | 0.55 | not reliable |
| openai/gpt-5.6-luna | all | 86 | 0.25 | fair | 0.43 | not reliable |
| qwen/qwen3.8-flash | bioinformatics | 14 | 0.00 | slight | 0.06 | not reliable |
| qwen/qwen3.8-flash | genomics | 15 | 0.59 | moderate | 0.69 | not reliable |
| qwen/qwen3.8-flash | microbiology | 12 | 0.31 | fair | 0.62 | not reliable |
| qwen/qwen3.8-flash | off-lane | 30 | 1.00 | almost perfect | 0.20 | reliable |
| qwen/qwen3.8-flash | systems biology | 15 | 0.44 | moderate | 0.74 | not reliable |
| qwen/qwen3.8-flash | all | 86 | 0.33 | fair | 0.61 | not reliable |
| tencent/hy3 | bioinformatics | 14 | 0.00 | slight | 0.30 | not reliable |
| tencent/hy3 | genomics | 15 | 0.63 | substantial | 0.75 | reliable |
| tencent/hy3 | microbiology | 12 | 0.43 | moderate | 0.74 | not reliable |
| tencent/hy3 | off-lane | 30 | 1.00 | almost perfect | 0.48 | reliable |
| tencent/hy3 | systems biology | 15 | 0.44 | moderate | 0.77 | not reliable |
| tencent/hy3 | all | 86 | 0.36 | fair | 0.72 | not reliable |
| xiaomi/mimo-v2.5 | bioinformatics | 14 | 0.00 | slight | 0.31 | not reliable |
| xiaomi/mimo-v2.5 | genomics | 15 | 0.59 | moderate | 0.73 | not reliable |
| xiaomi/mimo-v2.5 | microbiology | 12 | 0.62 | substantial | 0.73 | reliable |
| xiaomi/mimo-v2.5 | off-lane | 30 | 1.00 | almost perfect | 0.44 | reliable |
| xiaomi/mimo-v2.5 | systems biology | 15 | 0.33 | fair | 0.55 | not reliable |
| xiaomi/mimo-v2.5 | all | 86 | 0.43 | moderate | 0.66 | not reliable |
| z-ai/glm-5.3-flash | bioinformatics | 14 | 0.00 | slight | -0.09 | not reliable |
| z-ai/glm-5.3-flash | genomics | 15 | 0.59 | moderate | 0.59 | not reliable |
| z-ai/glm-5.3-flash | microbiology | 12 | 0.43 | moderate | 0.55 | not reliable |
| z-ai/glm-5.3-flash | off-lane | 30 | 1.00 | almost perfect | 0.22 | reliable |
| z-ai/glm-5.3-flash | systems biology | 15 | 0.33 | fair | 0.58 | not reliable |
| z-ai/glm-5.3-flash | all | 86 | 0.40 | fair | 0.53 | not reliable |
| z-ai/glm-5.3-flash#schema | bioinformatics | 14 | 0.00 | slight | 0.02 | not reliable |
| z-ai/glm-5.3-flash#schema | genomics | 15 | 0.47 | moderate | 0.46 | not reliable |
| z-ai/glm-5.3-flash#schema | microbiology | 12 | 0.43 | moderate | 0.52 | not reliable |
| z-ai/glm-5.3-flash#schema | off-lane | 30 | 1.00 | almost perfect | 0.18 | reliable |
| z-ai/glm-5.3-flash#schema | systems biology | 15 | 0.33 | fair | 0.53 | not reliable |
| z-ai/glm-5.3-flash#schema | all | 86 | 0.35 | fair | 0.51 | not reliable |
