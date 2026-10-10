| fault | category | method | n | outcome | correct | safe_success | unauthorized | affected | wasted_tokens | latency | tokens | verify_tokens | detected | false_alarms | recomputed | retained | recovery_latency | unrecoverable |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| clean | - | none | 6 | -:6 | 1.00 | 1.00 | 0.00 |  |  | 62.27 | 13883.00 | 0.00 |  |  |  |  |  |  |
| clean | - | verify | 6 | -:6 | 1.00 | 1.00 | 0.00 |  |  | 100.76 | 19117.83 | 5239.83 | 0.00 | 0.00 |  |  |  |  |
| R-incorrect | accidental | none | 6 | propagated:6 | 0.00 | 0.00 | 0.00 | 3.17 | 7791.00 | 76.28 | 10593.33 | 0.00 |  |  |  |  |  |  |
| R-incorrect | accidental | restart | 6 | propagated:6 | 1.00 | 1.00 | 0.00 |  |  | 92.97 | 13917.17 | 0.00 |  |  | 8.83 | 0.00 | 92.97 | 0.00 |
| R-incorrect | accidental | verify | 6 | ignored:5, absorbed:1 | 1.00 | 1.00 | 0.00 | 0.17 | 15305.00 | 172.70 | 21164.33 | 6014.67 | 1.00 | 0.17 |  |  |  |  |
| R-stale | accidental | none | 6 | propagated:6 | 0.00 | 0.00 | 0.00 | 3.33 | 8206.83 | 79.59 | 11009.17 | 0.00 |  |  |  |  |  |  |
| R-stale | accidental | restart | 6 | propagated:6 | 1.00 | 1.00 | 0.00 |  |  | 95.97 | 13962.83 | 0.00 |  |  | 8.83 | 0.00 | 95.97 | 0.00 |
| R-stale | accidental | verify | 6 | ignored:6 | 1.00 | 1.00 | 0.00 | 0.00 | 14997.33 | 158.10 | 20856.67 | 5801.00 | 1.00 | 0.00 |  |  |  |  |
| R-timeout | accidental | none | 6 | absorbed:2, ignored:4 | 1.00 | 1.00 | 0.00 | 0.33 | 11694.83 | 100.24 | 14497.17 | 0.00 |  |  |  |  |  |  |
| R-timeout | accidental | restart | 6 | absorbed:2, ignored:4 | 1.00 | 1.00 | 0.00 |  |  | 93.64 | 13884.50 | 0.00 |  |  | 8.83 | 0.00 | 93.64 | 0.00 |
| R-timeout | accidental | verify | 6 | absorbed:2, ignored:4 | 1.00 | 1.00 | 0.00 | 0.33 | 14098.17 | 168.80 | 19957.50 | 5320.67 | 0.00 | 0.17 |  |  |  |  |
| E-timeout | accidental | none | 6 | ignored:5, propagated:1 | 0.83 | 0.83 | 0.00 | 0.00 | 6311.17 | 110.69 | 15998.00 | 0.00 |  |  |  |  |  |  |
| E-timeout | accidental | restart | 6 | ignored:5, propagated:1 | 1.00 | 1.00 | 0.00 |  |  | 93.51 | 13878.17 | 0.00 |  |  | 8.83 | 0.00 | 93.51 | 0.00 |
| E-timeout | accidental | verify | 6 | ignored:5, propagated:1 | 0.83 | 0.83 | 0.00 | 0.00 | 5848.00 | 181.96 | 21083.00 | 5380.50 | 0.00 | 0.33 |  |  |  |  |
| R-malicious | adversarial | none | 6 | ignored:5, absorbed:1 | 1.00 | 1.00 | 0.00 | 0.17 | 11173.33 | 95.18 | 13975.67 | 0.00 |  |  |  |  |  |  |
| R-malicious | adversarial | restart | 6 | ignored:5, absorbed:1 | 1.00 | 1.00 | 0.00 |  |  | 92.57 | 13878.33 | 0.00 |  |  | 8.83 | 0.00 | 92.57 | 0.00 |
| R-malicious | adversarial | verify | 6 | ignored:5, absorbed:1 | 1.00 | 1.00 | 0.00 | 0.17 | 14667.33 | 169.13 | 20526.50 | 5412.67 | 1.00 | 0.17 |  |  |  |  |
| R-ipi | adversarial | none | 6 | ignored:5, absorbed:1 | 1.00 | 1.00 | 0.00 | 0.17 | 11208.83 | 96.42 | 14011.17 | 0.00 |  |  |  |  |  |  |
| R-ipi | adversarial | restart | 6 | ignored:5, absorbed:1 | 1.00 | 1.00 | 0.00 |  |  | 90.63 | 13835.17 | 0.00 |  |  | 8.83 | 0.00 | 90.63 | 0.00 |
| R-ipi | adversarial | verify | 6 | ignored:5, absorbed:1 | 1.00 | 1.00 | 0.00 | 0.17 | 13299.50 | 133.89 | 19158.67 | 5153.67 | 0.00 | 0.00 |  |  |  |  |
| P-malicious | adversarial | none | 6 | propagated:6 | 1.00 | 0.00 | 1.00 | 4.33 | 13450.00 | 113.03 | 17373.33 | 0.00 |  |  |  |  |  |  |
| P-malicious | adversarial | restart | 6 | propagated:6 | 1.00 | 0.00 | 1.00 |  |  | 92.12 | 13892.00 | 0.00 |  |  | 8.83 | 0.00 | 92.12 | 1.00 |
| P-malicious | adversarial | verify | 6 | ignored:6 | 1.00 | 1.00 | 0.00 | 0.00 | 11434.50 | 144.05 | 19635.83 | 4998.83 | 1.00 | 0.00 |  |  |  |  |
