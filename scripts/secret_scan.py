#!/usr/bin/env python3
"""Heuristic secret and inappropriate personal-data scan without value output."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


MAX_TEXT_BYTES = 5_000_000
ARCHIVE_SUFFIXES = (".zip", ".7z", ".tar", ".tar.gz", ".tar.zst", ".tgz")

RULES = [
    ("openai-key", re.compile("sk" + r"-(?:proj-)?[A-Za-z0-9_-]{20,}")),
    ("openrouter-key", re.compile("sk" + r"-or-v1-[A-Za-z0-9]{20,}")),
    ("github-token", re.compile("(?:gh" + r"[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("private-key", re.compile("-----BEGIN " + r"(?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("password-assignment", re.compile(r"(?i)\b(?:password|passwd|pwd)\s*[:=]\s*['\"]?(?!<|REDACTED|PLACEHOLDER|NOT_SET)[^\s'\"]{8,}")),
    ("bearer-token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~-]{24,}")),
    ("personal-case-id", re.compile(r"(?i)\b(?:BG-Nummer|Kundennummer|Aktenzeichen)\s*[:=]\s*[A-Z0-9][A-Z0-9./-]{5,}")),
]
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
ALLOWED_EMAIL_SUFFIXES = ("@users.noreply.github.com", "@example.com", "@example.invalid")


def all_files(root: Path) -> list[Path]:
    result = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(name for name in dirnames if name != ".git")
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if path.is_symlink():
                result.append(path)
            elif path.is_file():
                result.append(path)
    return sorted(result, key=lambda path: path.relative_to(root).as_posix())


def tracked_files(root: Path) -> set[str]:
    if not (root / ".git").is_dir():
        return set()
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode:
        return set()
    return {value.decode("utf-8", errors="surrogateescape") for value in proc.stdout.split(b"\x00") if value}


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve(strict=True)
    tracked = tracked_files(root)
    findings: list[tuple[str, str, int]] = []
    scanned = 0

    for path in all_files(root):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            findings.append(("symlink-file", relative, 0))
            continue
        lower = relative.casefold()
        if Path(relative).name == ".env" or Path(relative).name.startswith(".env."):
            findings.append(("environment-file", relative, 0))
        if any(lower.endswith(suffix) for suffix in ARCHIVE_SUFFIXES):
            findings.append(("raw-archive", relative, 0))
        data = path.read_bytes()
        scanned += 1
        if len(data) > MAX_TEXT_BYTES or b"\x00" in data:
            continue
        text = data.decode("utf-8", errors="replace")
        for rule, pattern in RULES:
            for match in pattern.finditer(text):
                findings.append((rule, relative, line_number(text, match.start())))
        for match in EMAIL.finditer(text):
            email = match.group(0).casefold()
            if not email.endswith(ALLOWED_EMAIL_SUFFIXES):
                findings.append(("personal-email", relative, line_number(text, match.start())))

    # Once committed/staged, ensure the scan covered every tracked file. Extra
    # untracked files are also scanned so ignored secrets cannot hide locally.
    missing_tracked = sorted(tracked - {p.relative_to(root).as_posix() for p in all_files(root)})
    for relative in missing_tracked:
        findings.append(("missing-tracked-file", relative, 0))

    findings = sorted(set(findings))
    if findings:
        print(f"SECRET_SCAN FAIL files={scanned} findings={len(findings)}")
        for rule, relative, lineno in findings:
            location = f"{relative}:{lineno}" if lineno else relative
            print(f"{rule}: {location}")
        return 1
    if not args.quiet:
        print(f"SECRET_SCAN PASS files={scanned} findings=0 tracked={len(tracked)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
