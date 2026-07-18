# UNIX Corpus Ingestion 1B

Title: UNIX Corpus Ingestion 1B

Production date: 2026-07-15

Report generated date: 2026-07-18

Project: AOIA-Core

Repository: https://github.com/luciferprosun/AOIA-Core

Branch: `feature/m2-b0-provider-critic-inert-core`

Starting commit: `4c72724d94c71a9933f70839e07c0bcbe0e0606d`

Ending commit: `b7a3a1481ce382e516ed0d39e5ac334f3240c727`

Commit subject: `chore(release): checkpoint complete architect handoff`

Push status: PUSHED — ending commit verified on the configured remote branch; exact push timestamp is not available.

Scope: Deterministic ingestion, inventory, normalization, resume validation, and non-authoritative corpus-boundary evidence for the local UNIX source.

Files changed: `runtime/knowledge/unix_corpus_ingestion.py`, `data/unix_corpus_ingestion_1b/*` evidence and manifests, `tests/test_unix_corpus_ingestion_1a.py`, and `tests/test_unix_full_corpus_materialization_1a.py`.

Tests executed: Exact command is not separately recorded. The committed validation artifact records changed-source fixture validation and deterministic replay checks.

Test results: 103 discovered corpus files, 80 supported files, 13 normalized records, zero unsafe archive members, deterministic replay match, and no corpus command text executed. These values are copied evidence, not a rerun.

Authority impact: None. The corpus and normalized records are explicitly non-authoritative and cannot approve, dispatch, execute, or write.

Known limitations: One approved extracted source; raw normalized records are intentionally excluded from this reporting repository; human review is required.

Work date: 2026-07-15, based on the supporting commit because the report carries no stronger internal timestamp.

Commit date: 2026-07-15T03:59:22+02:00.

Push date: not available.

Report generated: 2026-07-18.

Evidence sources:

- [ingestion validation report](../../evidence/tests/2026-07-15/unix_corpus_ingestion_1b/validation_report.json)
- [approved source inventory](../../evidence/manifests/2026-07-15/unix_corpus_ingestion_1b/approved_source_inventory.json)
- [ingestion state](../../evidence/manifests/2026-07-15/unix_corpus_ingestion_1b/ingestion_state.json)
- [source inventory](../../evidence/manifests/2026-07-15/unix_corpus_ingestion_1b/source_inventory.json)
- Git commit `b7a3a1481ce382e516ed0d39e5ac334f3240c727`
