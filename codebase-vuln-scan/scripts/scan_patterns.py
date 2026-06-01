#!/usr/bin/env python3
"""Scan source for risky code patterns (regex heuristics).

Usage: python scan_patterns.py <path> [--json]

Heuristic only — every hit needs human confirmation. Prefer semgrep when
available; this is a dependency-free backstop. See references/vuln-patterns.md.
"""
import argparse
import json
import os
import re
import sys

# (id, severity, description, language hint, regex)
RULES = [
    ("py-eval-exec", "high", "Use of eval/exec on dynamic input", ".py",
     re.compile(r"\b(eval|exec)\s*\(")),
    ("py-pickle", "high", "Insecure deserialization via pickle.load", ".py",
     re.compile(r"\bpickle\.(load|loads)\s*\(")),
    ("py-yaml-load", "medium", "yaml.load without SafeLoader", ".py",
     re.compile(r"\byaml\.load\s*\((?![^)]*Safe)")),
    ("py-subprocess-shell", "high", "subprocess with shell=True", ".py",
     re.compile(r"subprocess\.(run|call|Popen|check_output)\s*\([^)]*shell\s*=\s*True")),
    ("py-os-system", "high", "os.system with interpolated input", ".py",
     re.compile(r"os\.system\s*\(")),
    ("py-sql-fstring", "high", "Possible SQL injection (f-string/% in query)", ".py",
     re.compile(r"(?i)(execute|executemany)\s*\(\s*f?['\"].*(SELECT|INSERT|UPDATE|DELETE).*\{|%\s*\(?")),
    ("py-md5-sha1", "low", "Weak hash (md5/sha1)", ".py",
     re.compile(r"hashlib\.(md5|sha1)\s*\(")),
    ("py-requests-noverify", "medium", "TLS verification disabled", ".py",
     re.compile(r"verify\s*=\s*False")),
    ("js-eval", "high", "Use of eval()", ".js",
     re.compile(r"\beval\s*\(")),
    ("js-innerhtml", "medium", "innerHTML assignment (XSS risk)", ".js",
     re.compile(r"\.innerHTML\s*=")),
    ("js-child-process", "high", "child_process.exec with dynamic input", ".js",
     re.compile(r"child_process[\s\S]{0,30}\.exec\s*\(")),
    ("js-sql-concat", "high", "Possible SQL injection (string concat in query)", ".js",
     re.compile(r"(?i)(query|execute)\s*\(\s*[`'\"].*(SELECT|INSERT|UPDATE|DELETE).*[`'\"]\s*\+")),
    ("generic-hardcoded-ip", "low", "Hardcoded private/IP address", "",
     re.compile(r"\b(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)\b")),
    ("php-sql", "high", "Possible SQL injection in PHP query", ".php",
     re.compile(r"(?i)(mysqli_query|->query)\s*\(.*\$_(GET|POST|REQUEST)")),
    ("generic-path-traversal", "medium", "Path built from user input", "",
     re.compile(r"(?i)(open|readfile|sendfile|include)\s*\([^)]*(req\.|request\.|params|\$_(GET|POST))")),
]

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "dist", "build",
             "__pycache__", "vendor", "target", ".next"}
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".php", ".rb", ".go",
            ".java", ".c", ".cpp", ".cs"}
MAX_BYTES = 2_000_000


def applies(rule_ext, file_ext):
    return rule_ext == "" or rule_ext == file_ext or (
        rule_ext == ".js" and file_ext in {".js", ".jsx", ".ts", ".tsx"})


def scan_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in CODE_EXT:
        return []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return []
    out = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith(("#", "//", "*")):
            continue
        for rid, sev, desc, rext, rx in RULES:
            if applies(rext, ext) and rx.search(line):
                out.append({"id": rid, "severity": sev, "description": desc,
                            "file": path, "line": i, "code": stripped[:160]})
    return out


def walk(root):
    findings = []
    if os.path.isfile(root):
        return scan_file(root)
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
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
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: order.get(f["severity"], 9))
    if args.json:
        print(json.dumps(findings, indent=2))
        return
    if not findings:
        print("No risky patterns matched.")
        return
    print(f"{len(findings)} pattern match(es):\n")
    for f in findings:
        print(f"  [{f['severity'].upper()}] {f['description']}")
        print(f"      {f['file']}:{f['line']}: {f['code']}")
    print("\nHeuristic matches — confirm each. Prefer semgrep for deeper analysis.")


if __name__ == "__main__":
    sys.exit(main())
