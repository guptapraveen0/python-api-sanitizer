| # | Scenario | Expected/observed result | Status |
|---|---|---|---|
| 1 | Live API, `_limit=3` | HTTP 200; 3 valid records (run on network-enabled machine) | Not executed here |
| 2 | `--mock` | 3 deterministic valid fixture records; sanitized report | Passed locally |
| 3 | Wrong path | HTTP 404 recorded; no traceback; empty records | Expected transcript; not executed here |
| 4 | Invalid host, 2s timeout | Timeout or connection/DNS error recorded; no traceback | Expected transcript; not executed here |
| 5 | Missing field fixture | 1 valid + 1 invalid record; processing continues | Passed locally |
| 6 | Non-list JSON fixture | Clear top-level shape error; no crash | Passed locally |
