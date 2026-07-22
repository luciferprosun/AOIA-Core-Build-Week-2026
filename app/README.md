# Application staging

> **IN PROGRESS — NOT FINAL SUBMISSION EVIDENCE**

Status: `PENDING_IMPORT`

Application source is intentionally not duplicated in this evidence repository. The served single-window cockpit is committed and CI-verified in AOIA-Core at `7f61a3b167a028d7e34b852cca4ade809ceec571`; its normalized production report is available at [Single-Window AOIA Operator Cockpit 1A](../reports/2026-07-22/SINGLE_WINDOW_OPERATOR_CONSOLE_1A.md).

Run it from the AOIA-Core repository root:

```bash
PYTHONPYCACHEPREFIX=/tmp/aoia-core-pycache PYTHONPATH=runtime:. python3 -m runtime.webapp
```

Then open `http://127.0.0.1:4311`. A future source-code import here would still require separate licensing, secret, provenance, and size review.
