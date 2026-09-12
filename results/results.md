| model | cov% | strict% | wrong-field | sigma | MAE vs ceiling | top-10 | latency s | $/call |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| anthropic/claude-sonnet-5 | 94.4 | 97.3 | 0 | 0.011 | 0.000 | 10/10 | 3.25 | 0.00394 |
| minimax/minimax-m3@low | 82.2 | 100.0 | 1 | 0.047 | 0.072 | 6/10 | 1.43 | 0.00022 |
| minimax/minimax-m3 | 79.6 | 100.0 | 1 | 0.046 | 0.101 | 6/10 | 1.39 | 0.00026 |
| xiaomi/mimo-v2.5 | 100.0 | 100.0 | 2 | 0.065 | 0.103 | 6/10 | 5.55 | 0.00007 |
| deepseek/deepseek-v4-flash-0731@low | 100.0 | 100.0 | 0 | 0.069 | 0.121 | 6/10 | 18.53 | 0.00015 |
| google/gemini-3.5-flash-lite | 100.0 | 100.0 | 0 | 0.015 | 0.124 | 7/10 | 1.06 | 0.00044 |
| anthropic/claude-haiku-4.5 | 100.0 | 0.0 | 0 | 0.010 | 0.136 | 7/10 | 2.35 | 0.00161 |
| deepseek/deepseek-v4-flash-0731 | 100.0 | 100.0 | 3 | 0.081 | 0.158 | 6/10 | 4.33 | 0.00008 |
