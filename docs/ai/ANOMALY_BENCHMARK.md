# ChhatraLekha — Synthetic Anomaly Benchmark

Generated: `2026-11-21T22:14:33+00:00`

Detector source commit: `f2c4eb4`

This report measures **agreement with constructed labels** on fully synthetic snapshots. It is reproducible offline with `python -m app.scripts.eval_anomaly`. The detector is unchanged by this evaluation.

## Configuration

| Setting | Value |
| :--- | :--- |
| Dataset version | 1.0.0 |
| Ruleset | `CHHATRALEKHA_RULES_2026_V1` |
| Fixture seed | `synthetic-anomaly-benchmark-v1` |
| Unit of evaluation | case student / rule pair |
| Cases | 47 |
| Scored student-rule pairs | 65 |
| Review-only cases (excluded) | 1 |

| Case label | Count |
| :--- | ---: |
| boundary | 13 |
| negative | 10 |
| positive | 23 |
| review_only | 1 |

## Per-rule results

| Rule | Check | Pairs | TP | FP | FN | TN | Precision | Recall | F1 |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R01 | APAAR structural validity | 4 | 2 | 0 | 0 | 2 | 1.000 | 1.000 | 1.000 |
| R02 | Cross-institution duplicate | 5 | 2 | 0 | 0 | 3 | 1.000 | 1.000 | 1.000 |
| R03 | Same-institution duplicate | 7 | 4 | 0 | 0 | 3 | 1.000 | 1.000 | 1.000 |
| R04 | Duplicate institute roll number | 8 | 4 | 0 | 0 | 4 | 1.000 | 1.000 | 1.000 |
| R05 | Sanctioned intake breach | 8 | 2 | 0 | 0 | 6 | 1.000 | 1.000 | 1.000 |
| R06 | Supernumerary quota ceiling | 12 | 5 | 0 | 0 | 7 | 1.000 | 1.000 | 1.000 |
| R07 | Documentary / quota consistency | 6 | 4 | 0 | 0 | 2 | 1.000 | 1.000 | 1.000 |
| R08 | Impossible dates | 7 | 4 | 0 | 0 | 3 | 1.000 | 1.000 | 1.000 |
| R09 | Missing mandatory fields | 4 | 3 | 0 | 0 | 1 | 1.000 | 1.000 | 1.000 |
| R10 | Unsanctioned programme | 4 | 2 | 0 | 0 | 2 | 1.000 | 1.000 | 1.000 |

`N/A` means the metric denominator was zero; it is never silently reported as zero.

## Review-only cases (not scored)

| Case | Rule | Labeled flags | Observed flags |
| :--- | :--- | :--- | :--- |
| R02-REV-01 | R02 | none | S1, S2 |

## Timing (machine-specific)

Each of the 47 case evaluations was timed once with `time.perf_counter()` in this run. p50 = 0.178 ms; p95 = 0.348 ms. These numbers describe this machine only and are not a portable performance guarantee.

## Method

- Each case is an independent, fully synthetic snapshot built from a versioned JSON fixture with one shared student template.
- `case_id` values are unique across the dataset. APAAR IDs are reused across independent snapshots and are artificial.
- Each case declares the exact case students its target rule should flag. Cases for other rules do not enter that rule's confusion counts.
- `positive` cases contribute true positives and false negatives; `negative` and `boundary` cases contribute true negatives and false positives. `boundary` cases probe the edge of a rule.
- A finding is mapped back to a case student by its (APAAR, institution, programme) signature in stable engine order; inactive rows are excluded for rules that inspect only active enrolments.
- `review_only` cases document ambiguous scenarios and are never converted into binary labels.
- Precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2·precision·recall/(precision+recall).

## Limitations

- A curated synthetic set measures agreement with its explicit labels. It does **not** establish detection accuracy on real student records.
- Full agreement here is expected: the labels encode documented rule intent on small, unambiguous snapshots. It is a regression baseline for the rules, not evidence of production readiness.
- A flagged record is a potential inconsistency for authorised human review, not evidence of fraud and not a conclusion about a person.
- These results cannot validate legal compliance, official registry accuracy, or the behaviour of an external government service.
- The separate school rule pack is intentionally excluded from the ten-rule denominator.
