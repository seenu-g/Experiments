# Regression Results

Generated 2026-08-13 18:26:10 by `run_regression.py` against `config.LOCAL_MODEL`.
Commit this file after each run -- the git diff against the previous run is the point.

## Deterministic (6)

| Sample | Result | Version | Run |
|---|---|---|---|
| sockets_echo | FAIL | all 3 exhausted | 20260813_175649 |
| matplotlib_bar_chart | PASS | v1 | 20260813_180340 |
| pandas_average_score | PASS | v3 | 20260813_180613 |
| python_lambda | PASS | v1 | 20260813_180934 |
| networkx_knowledge_graph | PASS | v2 | 20260813_181053 |
| pandas_matplotlib_combined | FAIL | all 3 exhausted | 20260813_181338 |

## Probabilistic (3) -- a FAIL here may just be model variance (the response text is never exactly reproducible); spot-check the linked run.log before treating it as a regression

| Sample | Result | Version | Run |
|---|---|---|---|
| ollama_direct_call | PASS | v1 | 20260813_215105 |
| langchain_ollama | FAIL | all 3 exhausted | 20260813_182028 |
| llm_agent_tools | STOPPED | environment issue (VALIDATE) | 20260813_182223 |
