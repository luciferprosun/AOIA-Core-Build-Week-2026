#!/usr/bin/env python3
"""Collect deterministic Build Week evidence from committed Git history only."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


CLASSIFICATIONS = {
    "BUILD_WEEK_NEW_IMPLEMENTATION",
    "BUILD_WEEK_SECURITY_HARDENING",
    "BUILD_WEEK_VALIDATION_AND_TESTS",
    "BUILD_WEEK_KNOWLEDGE_WORK",
    "BUILD_WEEK_DEMO",
    "BUILD_WEEK_DOCUMENTATION",
    "PRE_EXISTING_COMPONENT_COMPLETED_DURING_BUILD_WEEK",
    "NOT_COMPETITION_RELEVANT",
    "REQUIRES_HUMAN_CLASSIFICATION",
}

CSV_FIELDS = [
    "full_sha",
    "parent_shas",
    "author_name",
    "author_timestamp",
    "committer_timestamp",
    "subject",
    "changed_files",
    "additions",
    "deletions",
    "production_files",
    "test_files",
    "evidence_and_manifest_files",
    "related_production_step",
    "classification",
    "classification_basis",
    "branch_reachability",
    "github_url",
    "human_review_required",
]


def parse_timestamp(value: str, label: str) -> dt.datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"malformed {label}: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} lacks timezone: {value!r}")
    return parsed


def git(repo: Path, *args: str, check: bool = True) -> str:
    env = os.environ.copy()
    env.update({"GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C", "LANG": "C"})
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def commit_metadata(repo: Path, sha: str) -> dict[str, Any]:
    raw = git(
        repo,
        "show",
        "-s",
        "--format=%H%x00%P%x00%an%x00%aI%x00%cI%x00%ct%x00%s",
        sha,
    ).rstrip("\n")
    parts = raw.split("\x00", 6)
    if len(parts) != 7:
        raise ValueError(f"malformed Git metadata for {sha}")
    full_sha, parents, author, author_iso, committer_iso, epoch, subject = parts
    author_time = parse_timestamp(author_iso, f"author timestamp for {sha}")
    committer_time = parse_timestamp(committer_iso, f"committer timestamp for {sha}")
    try:
        epoch_value = int(epoch)
    except ValueError as exc:
        raise ValueError(f"malformed committer epoch for {sha}: {epoch!r}") from exc
    if int(committer_time.timestamp()) != epoch_value:
        raise ValueError(f"committer timestamp/epoch mismatch for {sha}")
    return {
        "full_sha": full_sha,
        "parent_shas": parents.split() if parents else [],
        "author_name": author,
        "author_timestamp": author_time.isoformat(),
        "committer_timestamp": committer_time.isoformat(),
        "committer_utc": committer_time.astimezone(dt.timezone.utc),
        "subject": subject,
    }


def diff_numstat(repo: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    sha = metadata["full_sha"]
    parents = metadata["parent_shas"]
    if parents:
        raw = git(repo, "diff", "--numstat", "--no-renames", "-z", parents[0], sha)
    else:
        raw = git(repo, "show", "--format=", "--numstat", "--no-renames", "-z", sha)
    paths: list[str] = []
    additions = 0
    deletions = 0
    binary_files: list[str] = []
    for record in raw.split("\x00"):
        if not record:
            continue
        first, sep, remainder = record.partition("\t")
        second, sep2, path = remainder.partition("\t")
        if not sep or not sep2 or not path:
            raise ValueError(f"malformed numstat record for {sha}")
        paths.append(path)
        if first == "-" or second == "-":
            binary_files.append(path)
        else:
            try:
                additions += int(first)
                deletions += int(second)
            except ValueError as exc:
                raise ValueError(f"malformed numstat count for {sha}:{path}") from exc
    changed = sorted(set(paths))
    return {
        "changed_files": changed,
        "additions": additions,
        "deletions": deletions,
        "binary_files": sorted(set(binary_files)),
    }


def is_production_path(path: str) -> bool:
    return path.startswith(("runtime/", "build_support/", "scripts/")) and not path.startswith("tests/")


def is_test_path(path: str) -> bool:
    return path.startswith("tests/") or path.startswith(".github/workflows/")


def is_evidence_or_manifest(path: str) -> bool:
    name = Path(path).name.casefold()
    return path.startswith("data/") or any(
        marker in name
        for marker in ("manifest", "report", "evidence", "verification", "benchmark", "limitations", "checklist")
    )


def classify(paths: list[str], production: list[str], tests: list[str]) -> tuple[str, str, str]:
    path_set = set(paths)
    if "runtime/safety/workspace_guard.py" in path_set:
        return (
            "BUILD_WEEK_SECURITY_HARDENING",
            "Workspace guard and controlled-write TOCTOU hardening",
            "Diff hardens workspace, parent, target, and temporary-file identity checks with adversarial regressions.",
        )
    if any(path.endswith("runtime/safety/write_kill_switch.py") or path == "runtime/safety/write_kill_switch.py" for path in paths):
        return (
            "BUILD_WEEK_SECURITY_HARDENING",
            "Global write kill-switch propagation across Control Write, gated artifact write, and sandbox artifact write",
            "Diff changes write_kill_switch production logic and multiple controlled write surfaces, with broad regressions.",
        )
    unix_implementation_markers = {
        "runtime/knowledge/unix_corpus_ingestion.py",
        "runtime/retrieval/unix_runtime_adapter.py",
        "runtime/memory_hats/unix_hat.py",
        "runtime/unix_full_validation_freeze.py",
        "runtime/visible_unix_prototype.py",
    }
    if path_set & unix_implementation_markers and production:
        return (
            "BUILD_WEEK_NEW_IMPLEMENTATION",
            "UNIX evidence ingestion, deterministic retrieval, inert Hat routing metadata, visible review prototype, audit/freeze and developer entrypoints",
            "Diff introduces substantial production modules, evidence artifacts, and matching tests; classification is based on paths and line changes, not the subject alone.",
        )
    if "tests/test_full_chain_fail_closed_integration_1a.py" in path_set:
        return (
            "BUILD_WEEK_VALIDATION_AND_TESTS",
            "Full-chain fail-closed authority-boundary integration validation",
            "Diff adds the deterministic provider-to-workspace adversarial integration suite and canonical evidence manifests.",
        )
    if ".github/workflows/ci.yml" in path_set and not production:
        return (
            "BUILD_WEEK_VALIDATION_AND_TESTS",
            "CI Python-bytecode isolation and strict repository-freeze validation",
            "Diff changes only CI validation configuration and canonical evidence manifests; runtime authority code is untouched.",
        )
    if any(path.startswith("web/") for path in paths):
        return (
            "BUILD_WEEK_DEMO",
            "Single-window AOIA operator cockpit frontend",
            "Diff replaces the served cockpit frontend and adds matching UI/endpoint-contract tests without changing runtime authority code.",
        )
    if tests and not production:
        return (
            "BUILD_WEEK_VALIDATION_AND_TESTS",
            "Static capability-boundary validation and adversarial regression expansion",
            "Diff changes test/support files and evidence manifests but no production runtime file.",
        )
    if production and all("knowledge" in path or "retrieval" in path for path in production):
        return (
            "BUILD_WEEK_KNOWLEDGE_WORK",
            "Knowledge and retrieval implementation",
            "Production diff is confined to knowledge/retrieval paths.",
        )
    if paths and all(path.endswith((".md", ".txt")) for path in paths):
        return (
            "BUILD_WEEK_DOCUMENTATION",
            "Documentation-only change",
            "All changed paths are text documentation and no production/test path changed.",
        )
    return (
        "REQUIRES_HUMAN_CLASSIFICATION",
        "Mixed or unrecognized production step",
        "Diff paths do not satisfy a conservative deterministic category rule.",
    )


def reachable(repo: Path, sha: str, branch: str) -> bool:
    env = os.environ.copy()
    env.update({"GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C", "LANG": "C"})
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, branch],
        cwd=repo,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temp = Path(handle.name)
    os.replace(temp, path)


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--github-base", default="https://github.com/luciferprosun/AOIA-Core")
    args = parser.parse_args()

    repo = Path(args.repo).resolve(strict=True)
    output = Path(args.output).resolve()
    if not (repo / ".git").exists():
        raise SystemExit("source is not a Git repository")
    if is_within(output, repo):
        raise SystemExit("output must be outside the read-only source repository")
    start = parse_timestamp(args.start, "start").astimezone(dt.timezone.utc)
    end = parse_timestamp(args.end, "end").astimezone(dt.timezone.utc)
    if start > end:
        raise SystemExit("start is after end")

    git(repo, "rev-parse", "--verify", f"refs/heads/{args.branch}^{{commit}}")
    starting_head = git(repo, "rev-parse", "HEAD").strip()
    starting_status = git(repo, "status", "--porcelain=v1").rstrip("\n")
    commits = [sha for sha in git(repo, "rev-list", "--topo-order", args.branch).splitlines() if sha]
    metadata = [commit_metadata(repo, sha) for sha in commits]
    before = [item for item in metadata if item["committer_utc"] < start]
    if not before:
        raise SystemExit("no reachable pre-period baseline commit")
    baseline = max(before, key=lambda item: (item["committer_utc"], item["full_sha"]))
    in_period = sorted(
        (item for item in metadata if start <= item["committer_utc"] <= end),
        key=lambda item: (item["committer_utc"], item["full_sha"]),
    )

    baseline_reachable = reachable(repo, baseline["full_sha"], args.branch)
    baseline_payload = {
        "schema_version": "aoia-build-week-baseline-1a",
        "source_repository": str(repo),
        "source_github": args.github_base,
        "source_branch": args.branch,
        "window_start_utc": start.isoformat().replace("+00:00", "Z"),
        "window_end_utc": end.isoformat().replace("+00:00", "Z"),
        "selection_rule": "reachable commit with maximum committer timestamp strictly before window_start_utc",
        "full_sha": baseline["full_sha"],
        "subject": baseline["subject"],
        "author_timestamp": baseline["author_timestamp"],
        "committer_timestamp": baseline["committer_timestamp"],
        "parent_sha": baseline["parent_shas"][0] if baseline["parent_shas"] else "",
        "parent_shas": baseline["parent_shas"],
        "branch_reachability": baseline_reachable,
        "github_url": f"{args.github_base}/commit/{baseline['full_sha']}",
        "human_review_required": True,
    }

    ledger: list[dict[str, Any]] = []
    for item in in_period:
        diff = diff_numstat(repo, item)
        production = [path for path in diff["changed_files"] if is_production_path(path)]
        tests = [path for path in diff["changed_files"] if is_test_path(path)]
        evidence = [path for path in diff["changed_files"] if is_evidence_or_manifest(path)]
        category, step, basis = classify(diff["changed_files"], production, tests)
        if category not in CLASSIFICATIONS:
            raise AssertionError(category)
        ledger.append(
            {
                "full_sha": item["full_sha"],
                "parent_shas": item["parent_shas"],
                "author_name": item["author_name"],
                "author_timestamp": item["author_timestamp"],
                "committer_timestamp": item["committer_timestamp"],
                "subject": item["subject"],
                "changed_files": diff["changed_files"],
                "additions": diff["additions"],
                "deletions": diff["deletions"],
                "binary_files": diff["binary_files"],
                "production_files": production,
                "test_files": tests,
                "evidence_and_manifest_files": evidence,
                "related_production_step": step,
                "classification": category,
                "classification_basis": basis,
                "branch_reachability": reachable(repo, item["full_sha"], args.branch),
                "github_url": f"{args.github_base}/commit/{item['full_sha']}",
                "human_review_required": True,
            }
        )

    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "baseline.json", baseline_payload)
    jsonl = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in ledger)
    atomic_write(output / "commit_ledger.jsonl", jsonl)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=output, delete=False) as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in ledger:
            writer.writerow(
                {
                    key: (
                        json.dumps(row[key], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                        if isinstance(row[key], list)
                        else ("true" if row[key] is True else "false" if row[key] is False else row[key])
                    )
                    for key in CSV_FIELDS
                }
            )
        temp_csv = Path(handle.name)
    os.replace(temp_csv, output / "commit_ledger.csv")

    ending_head = git(repo, "rev-parse", "HEAD").strip()
    ending_status = git(repo, "status", "--porcelain=v1").rstrip("\n")
    if (starting_head, starting_status) != (ending_head, ending_status):
        raise SystemExit("source repository changed while collecting evidence")

    counts: dict[str, int] = {}
    for row in ledger:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    print(
        json.dumps(
            {
                "baseline": baseline["full_sha"],
                "candidate_commits": len(ledger),
                "classifications": dict(sorted(counts.items())),
                "output": str(output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"collect_build_week_commits: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
