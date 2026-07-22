# Workspace Guard / TOCTOU Hardening 1A

Title: Step 16 — Workspace Guard / TOCTOU Hardening 1A closure

Production date: 2026-07-21

Report generated date: 2026-07-22

Project: AOIA-Core

Repository: https://github.com/luciferprosun/AOIA-Core

Branch: `feature/m2-b0-provider-critic-inert-core`

Starting commit: `5b66890a5bed6976e7733a0f696f307a7436b678`

Ending commit: `ba9d00e41bfa3c871b37742ddb81f2fae8bbe903`

Commit subject: `feat(security): harden workspace guard against TOCTOU`

Push status: PUSHED — the ending commit is a verified ancestor of current remote head `7f61a3b167a028d7e34b852cca4ade809ceec571`.

Implementation status: **IMPLEMENTED, COMMITTED, AND PUSHED**. Test totals below are recorded by the committed source evidence and were not rerun during this reviewer-repository synchronization.

Scope: Recovery, inspection, validation, canonical regeneration, commit, and push of the preserved Step 16 package. The implementation binds workspace-root, parent-directory, target, and temporary-file identity to stable filesystem evidence and revalidates immediately before controlled placement.

Security behavior: Workspace-root, parent, and target replacement fail closed. Symlink substitution, traversal, temporary-file takeover, stale or missing identity evidence, device/inode mismatch, lower-writer bypass, and hard-limit violations are rejected. No fallback or retry path is introduced.

Files changed: five files; `runtime/safety/workspace_guard.py`, `runtime/safety/sandbox_artifact_runner.py`, `tests/test_workspace_guard_toctou_1a.py`, and two canonical manifests; 775 insertions and 117 deletions.

Tests executed: 26 focused TOCTOU tests; 138 controlled-write/sandbox tests; authority, forged-gate, preview, static-capability, manifest/freeze, compile, diff, and full-suite validation.

Test results: canonical freeze records 3,309 passed, four skipped, zero failures, and zero errors. Focused and related security groups passed. Manifest generation was deterministic.

Canonical evidence: architect handoff manifest hash `2f92ac8c6491074898250a41f7f31172141e38fd1b8272cbf6d41eeb9bdc2a12`; freeze manifest hash `b7e40816c0a40085c12c2f50ab6c0643150897facb483eb3978651e9abea0deb`.

Authority impact: None. Provider and critic output, `ActionProposal`, `ArtifactPreview`, audit evidence, manifests, hashes, paths, and identity evidence remain non-authoritative. Human approval remains separate, explicit, and hash-bound.

Known limitations: The guard intentionally blocks controlled writes when required identity evidence cannot be safely obtained or revalidated. It does not attempt automatic repair, retry, or weaker-path recovery.

Source paths at ending commit:

- `runtime/safety/workspace_guard.py`
- `runtime/safety/sandbox_artifact_runner.py`
- `tests/test_workspace_guard_toctou_1a.py`
- `data/architect_handoff_manifest_1a.json`
- `data/final_repository_freeze_1a/freeze_manifest.json`

Evidence sources:

- [AOIA-Core commit `ba9d00e4`](https://github.com/luciferprosun/AOIA-Core/commit/ba9d00e41bfa3c871b37742ddb81f2fae8bbe903)
- [Build Week commit ledger](../../evidence/commits/commit_ledger.csv)
