#!/usr/bin/env python3
"""Verify the private Build Week evidence repository fail-closed."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse


START = "2026-07-13T16:00:00Z"
END = "2026-07-22T00:00:00Z"
SOURCE_REPO = Path("/home/l/AOIA_PRODUCTION/repos/AOIA-Core")
BRANCH = "feature/m2-b0-provider-critic-inert-core"
CHECKSUM_RELATIVE = "evidence/hashes/SHA256SUMS"
ALLOWED_CLASSES = {
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

REQUIRED = [
    "README.md", "LICENSE", ".gitignore", "BUILD_WEEK_SCOPE.md",
    "PRE_EXISTING_FOUNDATION.md", "BUILD_WEEK_TIMELINE.md", "PROJECT_STATUS.md",
    "CODEX_AND_GPT56_USAGE.md", "SECURITY_BOUNDARY.md", "THIRD_PARTY_AND_LICENSES.md",
    "SUBMISSION_CHECKLIST.md", "evidence/commits/baseline.json",
    "evidence/commits/commit_ledger.csv", "evidence/commits/commit_ledger.jsonl",
    "evidence/commits/README.md", "evidence/reports/README.md",
    "evidence/tests/README.md", "evidence/codex_sessions/README.md", CHECKSUM_RELATIVE,
    "knowledge/unix/STATUS.md", "knowledge/german-employment-law/STATUS.md",
    "knowledge/web-engineering/STATUS.md", "demo/README.md", "demo/DEMO_FLOW.md",
    "demo/VIDEO_SCRIPT_PLACEHOLDER.md", "app/README.md",
    "submission/PROJECT_DESCRIPTION_DRAFT.md", "submission/DEVPOST_CHECKLIST.md",
    "scripts/collect_build_week_commits.py", "scripts/verify_submission_repo.py",
    "scripts/secret_scan.py", "scripts/sync_incremental_production_reports.py",
    "roadmaps/14_DAY_ROADMAP.md", "roadmaps/60_DAY_ROADMAP.md",
    "manifests/REPORT_IMPORT_MANIFEST.json",
]


def parse_time(value: str) -> dt.datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    result = dt.datetime.fromisoformat(text)
    if result.tzinfo is None:
        raise ValueError(f"timestamp lacks timezone: {value}")
    return result.astimezone(dt.timezone.utc)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_files(root: Path) -> list[Path]:
    result = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(name for name in dirnames if name != ".git")
        for name in sorted(filenames):
            path = Path(dirpath) / name
            relative = path.relative_to(root).as_posix()
            if relative == CHECKSUM_RELATIVE:
                continue
            if path.is_file() and not path.is_symlink():
                result.append(path)
    return sorted(result, key=lambda path: path.relative_to(root).as_posix())


def checksum_bytes(root: Path) -> bytes:
    lines = [f"{sha256_file(path)}  {path.relative_to(root).as_posix()}\n" for path in repository_files(root)]
    return "".join(lines).encode("utf-8")


def write_checksums(root: Path) -> None:
    target = root / CHECKSUM_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    data = checksum_bytes(root)
    with tempfile.NamedTemporaryFile("wb", dir=target.parent, delete=False) as handle:
        handle.write(data)
        temp = Path(handle.name)
    os.replace(temp, target)


def git(repo: Path, *args: str, check: bool = True) -> str:
    env = os.environ.copy()
    env.update({"GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C", "LANG": "C"})
    proc = subprocess.run(["git", *args], cwd=repo, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def git_object_exists(repo: Path, sha: str) -> bool:
    proc = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=repo,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def reachable(repo: Path, sha: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, BRANCH],
        cwd=repo,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def verify_json_files(root: Path, errors: list[str]) -> None:
    for path in sorted(root.rglob("*.json")):
        if ".git" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"invalid JSON {path.relative_to(root)}: {exc}")
    for path in sorted(root.rglob("*.jsonl")):
        if ".git" in path.parts:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                json.loads(line)
            except Exception as exc:
                fail(errors, f"invalid JSONL {path.relative_to(root)}:{lineno}: {exc}")
    for path in sorted(root.rglob("*.csv")):
        if ".git" in path.parts:
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        if not rows or not rows[0] or len(rows[0]) != len(set(rows[0])):
            fail(errors, f"invalid CSV header {path.relative_to(root)}")
            continue
        for lineno, row in enumerate(rows[1:], 2):
            if len(row) != len(rows[0]):
                fail(errors, f"non-rectangular CSV {path.relative_to(root)}:{lineno}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--generate-checksums", action="store_true")
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve(strict=True)
    if args.generate_checksums:
        write_checksums(root)
        print(f"SHA256SUMS GENERATED files={len(repository_files(root))}")
        return 0

    errors: list[str] = []
    for relative in REQUIRED:
        if not (root / relative).is_file():
            fail(errors, f"missing required file: {relative}")

    verify_json_files(root, errors)
    if errors:
        for item in errors:
            print(f"VERIFY FAIL: {item}")
        return 1

    import_manifest = json.loads((root / "manifests/REPORT_IMPORT_MANIFEST.json").read_text(encoding="utf-8"))
    incremental_sync = import_manifest.get("incremental_sync", {})
    expected_sync = {
        "mode": "INCREMENTAL",
        "frozen_at_europe_berlin": "2026-07-22T22:33:48+02:00",
        "previous_source_head": "5b66890a5bed6976e7733a0f696f307a7436b678",
        "previous_target_head": "6e99c68df211496a8d499e5176d375abe639a317",
        "source_head": "7f61a3b167a028d7e34b852cca4ade809ceec571",
        "copied_snapshot_count": 10,
        "generated_report_count": 4,
    }
    for key, expected in expected_sync.items():
        if incremental_sync.get(key) != expected:
            fail(errors, f"incremental sync metadata mismatch: {key}")
    if import_manifest.get("source_head") != expected_sync["source_head"]:
        fail(errors, "report import manifest source head mismatch")
    if import_manifest.get("record_count") != len(import_manifest.get("records", [])):
        fail(errors, "report import manifest record count mismatch")

    baseline = json.loads((root / "evidence/commits/baseline.json").read_text(encoding="utf-8"))
    ledger_json = [json.loads(line) for line in (root / "evidence/commits/commit_ledger.jsonl").read_text(encoding="utf-8").splitlines() if line]
    with (root / "evidence/commits/commit_ledger.csv").open("r", encoding="utf-8", newline="") as handle:
        ledger_csv = list(csv.DictReader(handle))
    if len(ledger_json) != len(ledger_csv):
        fail(errors, "CSV/JSONL commit ledger row counts differ")
    if baseline.get("window_start_utc") != START or baseline.get("window_end_utc") != END:
        fail(errors, "baseline window differs from official UTC window")
    if baseline.get("source_branch") != BRANCH or Path(baseline.get("source_repository", "")).resolve() != SOURCE_REPO.resolve():
        fail(errors, "baseline source repository/branch mismatch")
    baseline_sha = baseline.get("full_sha", "")
    if not git_object_exists(SOURCE_REPO, baseline_sha) or not reachable(SOURCE_REPO, baseline_sha):
        fail(errors, "baseline commit missing or unreachable")
    else:
        baseline_time = parse_time(git(SOURCE_REPO, "show", "-s", "--format=%cI", baseline_sha).strip())
        if not baseline_time < parse_time(START):
            fail(errors, "baseline is not strictly before official start")

    start = parse_time(START)
    end = parse_time(END)
    seen: set[str] = set()
    for index, row in enumerate(ledger_json):
        sha = row.get("full_sha", "")
        if sha in seen:
            fail(errors, f"duplicate ledger commit {sha}")
        seen.add(sha)
        if not git_object_exists(SOURCE_REPO, sha) or not reachable(SOURCE_REPO, sha):
            fail(errors, f"ledger commit missing or unreachable: {sha}")
            continue
        when = parse_time(row["committer_timestamp"])
        if not start <= when <= end:
            fail(errors, f"ledger commit outside official period: {sha}")
        actual = git(SOURCE_REPO, "show", "-s", "--format=%H%x00%P%x00%an%x00%aI%x00%cI%x00%s", sha).rstrip("\n").split("\x00")
        if len(actual) != 6:
            fail(errors, f"malformed source metadata for {sha}")
        else:
            expected = [sha, " ".join(row["parent_shas"]), row["author_name"], row["author_timestamp"], row["committer_timestamp"], row["subject"]]
            if actual != expected:
                fail(errors, f"ledger metadata differs from Git object: {sha}")
        if row.get("classification") not in ALLOWED_CLASSES:
            fail(errors, f"invalid classification: {sha}")
        if row.get("human_review_required") is not True or row.get("branch_reachability") is not True:
            fail(errors, f"unsafe review/reachability flags: {sha}")
        if row.get("github_url") != f"https://github.com/luciferprosun/AOIA-Core/commit/{sha}":
            fail(errors, f"incorrect GitHub URL: {sha}")
        csv_row = ledger_csv[index]
        if csv_row.get("full_sha") != sha or csv_row.get("classification") != row.get("classification"):
            fail(errors, f"CSV/JSONL ledger mismatch: {sha}")

    # Deterministically regenerate all committed-history outputs in a temporary
    # directory and require exact bytes.
    with tempfile.TemporaryDirectory() as temp_dir:
        command = [
            sys.executable, str(root / "scripts/collect_build_week_commits.py"),
            "--repo", str(SOURCE_REPO), "--branch", BRANCH,
            "--start", START, "--end", END, "--output", temp_dir,
        ]
        proc = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode:
            fail(errors, f"deterministic collector rerun failed: {proc.stdout.strip()}")
        else:
            for name in ("baseline.json", "commit_ledger.csv", "commit_ledger.jsonl"):
                if (root / "evidence/commits" / name).read_bytes() != (Path(temp_dir) / name).read_bytes():
                    fail(errors, f"collector output is not deterministic/current: {name}")

    # Accepted reports must be exact committed bytes with adjacent provenance.
    accepted = root / "evidence/reports/accepted"
    for report in sorted(path for path in accepted.iterdir() if path.is_file() and not path.name.endswith(".provenance.json")):
        provenance_path = report.with_name(report.name + ".provenance.json")
        if not provenance_path.is_file():
            fail(errors, f"accepted report lacks provenance: {report.name}")
            continue
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        if provenance.get("source_repository") != "https://github.com/luciferprosun/AOIA-Core" or provenance.get("source_branch") != BRANCH:
            fail(errors, f"accepted report source identity mismatch: {report.name}")
        sha = provenance.get("source_sha", "")
        source_path = provenance.get("source_path", "")
        if not git_object_exists(SOURCE_REPO, sha):
            fail(errors, f"accepted report source commit missing: {report.name}")
            continue
        proc = subprocess.run(["git", "show", f"{sha}:{source_path}"], cwd=SOURCE_REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode:
            fail(errors, f"accepted report source path missing: {report.name}")
            continue
        source_hash = hashlib.sha256(proc.stdout).hexdigest()
        copy_hash = sha256_file(report)
        if proc.stdout != report.read_bytes() or provenance.get("original_sha256") != source_hash or provenance.get("copied_sha256") != copy_hash:
            fail(errors, f"accepted report bytes/hash mismatch: {report.name}")
        if provenance.get("classification") != "ACCEPTED_COMMITTED_BUILD_WEEK_TEXT_EVIDENCE" or provenance.get("redaction_status") != "NOT_REQUIRED_NO_REDACTION":
            fail(errors, f"accepted report classification/redaction mismatch: {report.name}")

    # Checksums must exactly cover every non-.git file except the checksum file.
    checksum_path = root / CHECKSUM_RELATIVE
    if checksum_path.is_file() and checksum_path.read_bytes() != checksum_bytes(root):
        fail(errors, "SHA256SUMS is incomplete, stale, or non-deterministic")

    all_files = repository_files(root)
    total_size = sum(path.stat().st_size for path in all_files)
    archive_suffixes = (".zip", ".7z", ".tar", ".tar.gz", ".tar.zst", ".tgz")
    for path in all_files:
        relative = path.relative_to(root).as_posix()
        if any(relative.casefold().endswith(suffix) for suffix in archive_suffixes):
            fail(errors, f"raw archive prohibited: {relative}")
        if path.stat().st_size > 5_000_000:
            fail(errors, f"large file prohibited without explicit review: {relative}")
    if total_size > 25_000_000:
        fail(errors, f"repository content too large for bounded evidence repo: {total_size}")
    for forbidden in ("raw_corpora", "downloads", "secrets", "recordings/raw"):
        if (root / forbidden).exists():
            fail(errors, f"forbidden raw/sensitive directory exists: {forbidden}")
    if (root / ".gitmodules").exists():
        fail(errors, "submodules are prohibited")
    nested_git = [path for path in root.rglob(".git") if path.resolve() != (root / ".git").resolve()]
    if nested_git:
        fail(errors, f"nested Git repository detected: {nested_git}")

    readme = (root / "README.md").read_text(encoding="utf-8")
    scope = (root / "BUILD_WEEK_SCOPE.md").read_text(encoding="utf-8")
    combined = readme + "\n" + scope
    for required_text in (
        "AOIA-Core is a pre-existing",
        "IN PROGRESS",
        "2026-07-13 09:00 PDT",
        "2026-07-22 00:00 UTC",
        "Łukasz Żuchowski",
    ):
        if required_text not in combined:
            fail(errors, f"required fair-play disclosure missing: {required_text}")
    status_expectations = {
        "knowledge/german-employment-law/STATUS.md": "Status: `INDEPENDENT_CODEX_AUDIT_IN_PROGRESS`",
        "knowledge/web-engineering/STATUS.md": "Status: `MASTER_LIBRARY_BUILD_IN_PROGRESS`",
        "app/README.md": "Status: `PENDING_IMPORT`",
    }
    for relative, expected in status_expectations.items():
        if expected not in (root / relative).read_text(encoding="utf-8"):
            fail(errors, f"pending status missing: {relative}")
    prohibited_claims = (
        "AOIA-Core was created during OpenAI Build Week",
        "AOIA-Core was built entirely during OpenAI Build Week",
        "German Law Hat is complete",
        "Web Engineering Hat is complete",
        "desktop demo is ready",
        "production-ready autonomous agent",
    )
    text_files = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in all_files if path.suffix in {".md", ".txt"})
    for claim in prohibited_claims:
        if claim in text_files:
            fail(errors, f"prohibited completion/fair-play claim found: {claim}")
    if any(path.name in {"FINAL_REPORT.md", "FINAL_VIDEO_SCRIPT.md"} for path in all_files):
        fail(errors, "final report or final video script created prematurely")

    secret_proc = subprocess.run(
        [sys.executable, str(root / "scripts/secret_scan.py"), "--root", str(root), "--quiet"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if secret_proc.returncode:
        fail(errors, f"secret scan failed: {secret_proc.stdout.strip()}")

    if args.require_clean:
        status = git(root, "status", "--porcelain=v1").strip()
        if status:
            fail(errors, f"competition worktree is not clean: {status}")

    if errors:
        print(f"VERIFY_SUBMISSION_REPO FAIL checks_failed={len(errors)}")
        for item in errors:
            print(f"- {item}")
        return 1
    print(
        "VERIFY_SUBMISSION_REPO PASS "
        f"commits={len(ledger_json)} accepted_reports={len(list(accepted.glob('*.json'))) // 2} "
        f"files={len(all_files)} bytes={total_size} secret_scan=PASS checksums=PASS"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"VERIFY_SUBMISSION_REPO FAIL: {exc}")
        raise SystemExit(1)
