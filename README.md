# AOIA-Core — OpenAI Build Week 2026 Extension

> **IN PROGRESS — NOT FINAL SUBMISSION EVIDENCE**

AOIA-Core is a pre-existing local-first safety and epistemic-control project. It was **meaningfully extended during OpenAI Build Week 2026 using GPT-5.6 and Codex**. This repository packages committed evidence of that bounded extension; it does not claim that the complete AOIA-Core project was built during Build Week.

## Official submission period

- Start: 2026-07-13 09:00 PDT / 2026-07-13 16:00 UTC / 2026-07-13 18:00 Europe/Berlin.
- End: 2026-07-21 17:00 PDT / 2026-07-22 00:00 UTC / 2026-07-22 02:00 Europe/Berlin.

The committed-history baseline immediately before the period is `4c72724d94c71a9933f70839e07c0bcbe0e0606d`. The exact in-period commit ledger is generated from the committed `feature/m2-b0-provider-critic-inert-core` history and must be reviewed before any final submission claim.

## Current status

**IN PROGRESS.** Build Week implementation reports through the official deadline are now published here, but the competition submission, video, and final human review remain open.

- The single-window AOIA operator cockpit is committed, pushed, and CI-verified in the source repository; application code is not duplicated here.
- Demo recording and final presentation review remain pending.
- The German Employment Law independent Codex audit remains pending acceptance/import here; no German Law Hat is active.
- The Web Engineering master-library build remains pending; no full Web Engineering Hat is active.
- The committed UNIX evidence is non-authoritative and its competition-demo use remains human-review-gated.
- Repository visibility remains a separate human decision.

## Build Week extension

Committed diffs inside the official period show bounded work in seven areas:

1. a large implementation checkpoint containing deterministic UNIX corpus evidence workflows, local retrieval, a zero-capability/non-authoritative UNIX Hat descriptor and routing metadata, durable audit evidence, a visible review prototype, validation/freeze tooling, and tests;
2. expanded static capability-boundary validation and adversarial tests; and
3. production safety hardening that made a global write kill-switch mandatory across controlled write paths, with regressions.
4. workspace-root, parent, target, symlink, temporary-file, and controlled-placement TOCTOU hardening;
5. a deterministic public-surface integration suite proving the provider-to-workspace control chain fails closed;
6. CI bytecode isolation outside the checkout while preserving strict repository-freeze verification; and
7. a responsive, single-window operator cockpit with one conversation, three non-authoritative observer cards, explicit manual send, inert Add API UX, and read-only audit/evidence access.

These statements describe the inspected diffs, not the whole AOIA-Core history. Uncommitted AOIA-Core work is excluded.

## Human and model roles

- **GPT-5.6 / ChatGPT** supported system architecture, security-invariant reasoning, roadmap decisions, synthesis of model audits, review of Codex execution reports, bounded prompt design, and competition planning.
- **Codex** inspected repositories, implemented bounded changes, wrote and ran tests, reproduced defects, prepared minimal production fixes, performed deterministic validation, prepared checkpoints, and initialized this competition repository.
- **Other models** acted as independent critics, research assistants, alternative analysts, or audit-suggestion sources.
- **Łukasz Żuchowski** chose direction, accepted or rejected recommendations, authorized production changes, and remained the final human decision-maker.

GPT-5.6, Codex, other model output, critic reports, knowledge records, tests, manifests, previews, and demo artifacts are not authority. None may approve, execute, write, or make consequential decisions merely because it exists or passes validation.

## What this repository is not

This repository is not evidence that AOIA-Core was created in one week. It is not a final demo, a completed German Law Hat, a completed Web Engineering Hat, an autonomous production agent, a legal-decision system, or permission to execute model proposals.

Start with [BUILD_WEEK_SCOPE.md](BUILD_WEEK_SCOPE.md), [PRE_EXISTING_FOUNDATION.md](PRE_EXISTING_FOUNDATION.md), and [evidence/commits/README.md](evidence/commits/README.md).

Reviewer navigation:

- [Production report index](indexes/REPORT_INDEX.md)
- [Verified implementation timeline](indexes/IMPLEMENTATION_TIMELINE.md)
- [Incremental import manifest and exact source cutoff](manifests/REPORT_IMPORT_MANIFEST.json)
- [Next 14 days — plan only](roadmaps/14_DAY_ROADMAP.md)
- [Next 60 days — plan only](roadmaps/60_DAY_ROADMAP.md)

## Run AOIA locally

From the AOIA-Core source repository root:

```bash
PYTHONPYCACHEPREFIX=/tmp/aoia-core-pycache PYTHONPATH=runtime:. python3 -m runtime.webapp
```

Open `http://127.0.0.1:4311`. The operator cockpit preserves explicit manual send and labels provider output as untrusted/non-authoritative.

The roadmaps describe proposed work only. They are deliberately separated from the committed implementation reports above.
