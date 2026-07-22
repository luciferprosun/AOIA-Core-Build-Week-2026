#!/usr/bin/env python3
"""Copy the bounded post-baseline AOIA evidence snapshots into this reviewer repo."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


SOURCE_URL = "https://github.com/luciferprosun/AOIA-Core"
SOURCE_BRANCH = "feature/m2-b0-provider-critic-inert-core"
PREVIOUS_SOURCE_HEAD = "5b66890a5bed6976e7733a0f696f307a7436b678"
SOURCE_HEAD = "7f61a3b167a028d7e34b852cca4ade809ceec571"
PREVIOUS_TARGET_HEAD = "6e99c68df211496a8d499e5176d375abe639a317"
FROZEN_AT = "2026-07-22T22:33:48+02:00"
MANIFEST_PATH = "manifests/REPORT_IMPORT_MANIFEST.json"

COMMITS = (
    ("ba9d00e41bfa3c871b37742ddb81f2fae8bbe903", "2026-07-21"),
    ("849b4e820ab9619d5417acd246b7d16d8e1b5890", "2026-07-21"),
    ("fd548b10c348b7b097bcd602b14278662fb8325f", "2026-07-21"),
    ("708d7b65a3e07e019c22702f44de03ab32d2cb92", "2026-07-21"),
    ("7f61a3b167a028d7e34b852cca4ade809ceec571", "2026-07-22"),
)

SOURCE_PATHS = (
    "data/architect_handoff_manifest_1a.json",
    "data/final_repository_freeze_1a/freeze_manifest.json",
)

GENERATED_REPORTS = (
    "reports/2026-07-21/CI_BYTECODE_ISOLATION_REPAIR_1A.md",
    "reports/2026-07-21/FULL_CHAIN_FAIL_CLOSED_INTEGRATION_1A.md",
    "reports/2026-07-21/WORKSPACE_GUARD_TOCTOU_HARDENING_1A.md",
    "reports/2026-07-22/SINGLE_WINDOW_OPERATOR_CONSOLE_1A.md",
)


def git_bytes(repo: Path, object_name: str) -> bytes:
    result = subprocess.run(
        ["git", "show", object_name],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def destination_for(commit: str, work_date: str, source_path: str) -> str:
    suffix = source_path.removeprefix("data/")
    return f"evidence/manifests/{work_date}/{commit[:8]}/{suffix}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", required=True)
    parser.add_argument("--target-repo", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()

    source = Path(args.source_repo).resolve(strict=True)
    target = Path(args.target_repo).resolve(strict=True)
    if git_bytes(source, f"{SOURCE_HEAD}^{{commit}}") == b"":
        raise RuntimeError("source HEAD is unavailable")

    additions: list[dict[str, object]] = []
    for commit, work_date in COMMITS:
        for source_path in SOURCE_PATHS:
            data = git_bytes(source, f"{commit}:{source_path}")
            destination_path = destination_for(commit, work_date, source_path)
            destination = target / destination_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and destination.read_bytes() != data:
                raise RuntimeError(f"refusing to overwrite differing evidence: {destination_path}")
            destination.write_bytes(data)
            digest = sha256(data)
            additions.append(
                {
                    "copy_status": "COPIED",
                    "destination_path": destination_path,
                    "destination_sha256": digest,
                    "notes": "Exact committed manifest evidence added incrementally; filename preserved; authority_for_aioa=false.",
                    "rename_reason": None,
                    "source_path": f"git:{SOURCE_URL}@{commit}:{source_path}",
                    "source_sha256": digest,
                    "supporting_commits": [commit],
                    "work_date": work_date,
                }
            )

    manifest_file = target / MANIFEST_PATH
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    destinations = {entry["destination_path"] for entry in additions}
    records = [
        record
        for record in manifest["records"]
        if record.get("destination_path") not in destinations
    ]
    records.extend(additions)
    records_by_destination = {
        record.get("destination_path"): record
        for record in records
        if record.get("destination_path")
    }
    for report_path in GENERATED_REPORTS:
        report_record = records_by_destination.get(report_path)
        if report_record is None:
            raise RuntimeError(f"generated report missing from manifest: {report_path}")
        report_record["destination_sha256"] = sha256((target / report_path).read_bytes())
    records.sort(
        key=lambda record: (
            record.get("destination_path") is None,
            record.get("destination_path") or record.get("source_path") or "",
        )
    )
    manifest["records"] = records
    manifest["record_count"] = len(records)
    manifest["record_counts"] = {
        status: sum(record.get("copy_status") == status for record in records)
        for status in ("COPIED", "GENERATED", "SKIPPED")
    }
    manifest["source_head"] = SOURCE_HEAD
    manifest["incremental_sync"] = {
        "mode": "INCREMENTAL",
        "frozen_at_europe_berlin": FROZEN_AT,
        "previous_source_head": PREVIOUS_SOURCE_HEAD,
        "previous_target_head": PREVIOUS_TARGET_HEAD,
        "source_head": SOURCE_HEAD,
        "delta_commits": [commit for commit, _ in COMMITS],
        "copied_snapshot_count": len(additions),
        "generated_report_count": 4,
        "uncommitted_source_paths_excluded": ["web/app.js", "web/operator_config.js"],
        "duplicate_policy": "Preserve the verified baseline; replace records only by exact destination path; never recopy the baseline batch.",
    }
    manifest_file.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "INCREMENTAL_SYNC_COMPLETE "
        f"source_head={SOURCE_HEAD} snapshots={len(additions)} records={len(records)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
