# CI Bytecode Isolation Repair 1A

Title: CI Bytecode Isolation Repair 1A

Production date: 2026-07-21

Report generated date: 2026-07-22

Project: AOIA-Core

Repository: https://github.com/luciferprosun/AOIA-Core

Branch: `feature/m2-b0-provider-critic-inert-core`

Starting commit: `849b4e820ab9619d5417acd246b7d16d8e1b5890`

Intermediate commit: `fd548b10c348b7b097bcd602b14278662fb8325f`

Ending commit: `708d7b65a3e07e019c22702f44de03ab32d2cb92`

Commit subject: `ci: isolate Python bytecode outside repository`

Push status: PUSHED — the final repair is a verified ancestor of current remote head `7f61a3b167a028d7e34b852cca4ade809ceec571`.

Implementation status: **IMPLEMENTED, COMMITTED, PUSHED, AND CI-VERIFIED**. Test totals below are recorded by the committed source evidence and were not rerun during this reviewer-repository synchronization.

Root cause: GitHub Actions imported or compiled repository Python before strict freeze verification and created `build_support/__pycache__/aoia_build_backend.cpython-312.pyc` inside the checkout. The freeze verifier correctly rejected the generated path.

Repair: The `test` job now writes `PYTHONPYCACHEPREFIX=${RUNNER_TEMP}/aoia-core-pycache` to `GITHUB_ENV` in an `Isolate Python bytecode` step before checkout and before every Python setup, compile, build-backend, editable-install, or test operation.

Files changed across the repair: `.github/workflows/ci.yml` and two canonical manifests; net five insertions and two deletions relative to the Step 17 commit. No runtime module changed.

Validation: Focused compile/import reproduction produced bytecode only below the external cache prefix and none in the repository. Repository scans, strict freeze verification, manifest verification, 30 focused integrity tests, compile validation, diff checks, and the full suite passed.

Test results: canonical freeze records 3,325 passed, four skipped, zero failures, and zero errors. GitHub Actions run [29860392624](https://github.com/luciferprosun/AOIA-Core/actions/runs/29860392624) completed successfully for `708d7b65...`; every job step, including strict tests after build-backend loading, passed.

Canonical evidence: architect handoff manifest hash `174e696e285b93a7ba96bf00ff0728ebf6a7b099a89565d9fdf45ca48d5577a9`; freeze manifest hash `7f545da5160a4501ae89ef2d216d547f5cfddfdc4e4f9bb04595b678f7b0e0f4`.

Freeze integrity: No freeze exclusion, bytecode ignore rule, cleanup-before-verification workaround, skipped check, or changed success condition was added. Forbidden generated files remain forbidden.

Authority impact: None. CI environment configuration is non-authoritative and grants no approval, write, execution, provider, browser, Git-runtime, dispatcher, or package-install authority.

Source paths across the intermediate and ending commits:

- `.github/workflows/ci.yml`
- `data/architect_handoff_manifest_1a.json`
- `data/final_repository_freeze_1a/freeze_manifest.json`

Evidence sources:

- [Intermediate AOIA-Core commit `fd548b10`](https://github.com/luciferprosun/AOIA-Core/commit/fd548b10c348b7b097bcd602b14278662fb8325f)
- [Final AOIA-Core commit `708d7b65`](https://github.com/luciferprosun/AOIA-Core/commit/708d7b65a3e07e019c22702f44de03ab32d2cb92)
- [Successful GitHub Actions run 29860392624](https://github.com/luciferprosun/AOIA-Core/actions/runs/29860392624)
