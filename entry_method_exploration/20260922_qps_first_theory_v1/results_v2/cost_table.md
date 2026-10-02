# Derived 90% cost accounting

All times in microseconds/query. Coarse interpolation, not new measurement.

| Dataset | K | Baseline time | Candidate time | Baseline budget credit | Combined same-L penalty | Matched excess | Conditional zero-charge gain | Charge budget for +5% QPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| WebVid | 1 | 2241.515 | 2758.828 | 91.811 | 609.123 | 517.313 | 4.271% | -14.928 |
| WebVid | 100 | 2713.867 | 3301.153 | 45.838 | 633.124 | 587.286 | 1.718% | -83.393 |
| Yandex | 1 | 399.673 | 680.086 | 6.800 | 287.213 | 280.413 | 1.731% | -12.232 |
| Yandex | 100 | 700.666 | 987.544 | 6.100 | 292.978 | 286.878 | 0.878% | -27.265 |

Conditional zero-charge scenario assumes the candidate Recall curve and baseline same-L total cost. It is not measured and is not a general method upper bound.
The combined penalty includes all pipeline differences. No component can be identified from this table.
The +5% column is a sensitivity scenario, not a newly imposed user acceptance gate.
No record125 curve covers 95%; historical scales are stored separately in accounting.json.
