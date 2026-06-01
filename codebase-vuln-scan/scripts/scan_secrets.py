#!/usr/bin/env python3
"""Scan a codebase for likely committed secrets.

Usage: python scan_secrets.py <path> [--json]

Findings are candidates, not confirmations. Values are masked in output.
"""
import argparse
import json
import math
import os
import re
import sys

# (name, compiled regex, capture group holding the secret value)
PATTERNS = [
    ("AWS Access Key ID", re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), 1),
    ("AWS Secret Access Key", re.compile(r"(?i)aws.{0,20}?['\"]([0-9a-zA-Z/+]{40})['\"]"), 1),
    ("Google API Key", re.compile(r"\b(AIza[0-9A-Za-z\-_]{35})\b"), 1),
    ("GitHub Token", re.compile(r"\b((?:ghp|gho|ghu|ghs|ghr|github_pat)_[0-9A-Za-z_]{20,255})\b"), 1),
    ("Slack Token", re.compile(r"\b(xox[baprs]-[0-9A-Za-z-]{10,})\b"), 1),
    ("Stripe Key", re.compile(r"\b((?:sk|rk)_(?:live|test)_[0-9A-Za-z]{16,})\b"), 1),
    ("Private Key Block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"), 0),
    ("JWT", re.compile(r"\b(eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b"), 1),
    ("Slack Webhook", re.compile(r"(https://hooks\.slack\.com/services/[A-Za-z0-9/]+)"), 1),
    ("Generic Secret Assignment", re.compile(
        r"(?i)\b(?:password|passwd|secret|api[_-]?key|token|access[_-]?key|auth)\b\s*[:=]\s*['\"]([^'\"]{8,})['\"]"), 1),
]

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "dist", "build",
             "__pycache__", ".mypy_cache", "vendor", "target", ".next"}
SKIP_EXT = {".lock", ".min.js", ".map", ".png", ".jpg", ".jpeg", ".gif",
            ".pdf", ".zip", ".tar", ".gz", ".ico", ".woff", ".woff2", ".ttf"}
MAX_BYTES = 2_000_000


def entropy(s):
    if not s:
        return 0.0
    counts = {c: s.count(c) for c in set(s)}
    return -sum((n / len(s)) * math.log2(n / len(s)) for n in counts.values())


def mask(v):
    v = v.replace("\n", " ").strip()
    if len(v) <= 8:
        return v[0] + "***"
    return f"{v[:4]}{'*' * 6}{v[-4:]}"


def looks_placeholder(v):
    low = v.lower()
    return any(t in low for t in ("example", "changeme", "xxxx", "placeholder",
                                  "your_", "dummy", "<", "fake", "test_test"))


def scan_file(path):
    out = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return out
    for i, line in enumerate(lines, 1):
        for name, rx, grp in PATTERNS:
            m = rx.search(line)
            if not m:
                continue
            val = m.group(grp) if grp else m.group(0)
            if name == "Generic Secret Assignment":
                if looks_placeholder(val) or entropy(val) < 3.0:
                    continue
            out.append({"type": name, "file": path, "line": i,
                        "match": mask(val)})
    return out


def walk(root):
    findings = []
    if os.path.isfile(root):
        return scan_file(root)
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if os.path.splitext(fn)[1].lower() in SKIP_EXT:
                continue
            fp = os.path.join(dp, fn)
            try:
                if os.path.getsize(fp) > MAX_BYTES:
                    continue
            except OSError:
                continue
            findings.extend(scan_file(fp))
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    findings = walk(args.path)
    if args.json:
        print(json.dumps(findings, indent=2))
        return
    if not findings:
        print("No candidate secrets found.")
        return
    print(f"{len(findings)} candidate secret(s) found:\n")
    for f in findings:
        print(f"  [{f['type']}] {f['file']}:{f['line']}  ->  {f['match']}")
    print("\nThese are candidates. Confirm before acting; rotate any real secret "
          "(deletion alone does not remove it from git history).")


if __name__ == "__main__":
    sys.exit(main())
