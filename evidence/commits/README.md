# Commit evidence

> **IN PROGRESS — NOT FINAL SUBMISSION EVIDENCE**

`baseline.json`, `commit_ledger.csv`, and `commit_ledger.jsonl` are generated exclusively from committed Git objects reachable from `feature/m2-b0-provider-critic-inert-core`.

The collector uses committer timestamps for the exact inclusive Build Week window, inspects each candidate diff for changed paths and line counts, and applies one conservative category. Commit messages are recorded but are not the sole classification basis. Every row requires human review.

Re-run the collector after any new in-period commit. Never add uncommitted AOIA-Core bytes to these ledgers.
