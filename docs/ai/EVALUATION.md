# ChhatraLekha — RAG Evaluation Report

Generated: `2026-11-21T21:36:55+00:00`

This report measures the **local retrieval layer**, not an external model. It is reproducible offline with `python -m app.scripts.eval_rag`.

## Configuration

| Setting | Value |
| :--- | ---: |
| Corpus passages | 507 |
| Questions | 30 |
| Guidance / record | 24 / 6 |
| top-k | 4 |

## Results

| Metric | Value |
| :--- | ---: |
| Retrieval hit rate | 100% |
| Mean reciprocal rank | 0.9524 |
| Citation coverage | 100% |
| Intent accuracy | 100% |
| Role isolation pass rate | 100% |
| PII leaks | 0 |
| Retrieval latency p50 | 7.364 ms |
| Retrieval latency p95 | 29.211 ms |

All golden questions retrieved their expected passage.
