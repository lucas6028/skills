---
name: codebase-vuln-scan
description: Scan a project codebase for security vulnerabilities — dependency CVEs, hardcoded secrets, and risky code patterns (SQL injection, command injection, path traversal, insecure deserialization, weak crypto, etc.). Use this skill whenever the user wants a security audit, vulnerability scan, "is my code safe", "check for security issues", "find vulnerabilities", dependency/CVE checks, secret scanning, or any review of a repository's security posture. Trigger even when the user just points at a repo and says "audit this" or names a single concern like "any exposed API keys?"
---

# Codebase Vulnerability Scan

Audit a defensive security posture: find weaknesses so the user can fix them. This is for protecting the user's own code — never use it to help attack systems the user does not own.

## Scope

Cover three layers, in this order:

1. **Dependencies** — known CVEs in third-party packages (npm, pip, Go, Cargo, Maven, etc.)
2. **Secrets** — credentials, API keys, tokens, private keys committed to the repo
3. **Code patterns** — injection, traversal, unsafe deserialization, weak crypto, SSRF, and similar source-level risks

## Workflow

### 1. Map the codebase

Identify languages, package managers, and lockfiles present:

```bash
ls -la
find . -maxdepth 3 -type f \( -name "package.json" -o -name "requirements*.txt" -o -name "Pipfile*" -o -name "pyproject.toml" -o -name "go.mod" -o -name "Cargo.toml" -o -name "pom.xml" -o -name "build.gradle*" -o -name "composer.json" -o -name "Gemfile*" \) -not -path "*/node_modules/*" 2>/dev/null
```

This tells you which dependency scanners and which language rules apply.

### 2. Scan dependencies

Prefer native, offline-capable tools already in the ecosystem. Run whichever apply:

- **Node**: `npm audit --json` (or `pnpm audit` / `yarn audit`)
- **Python**: `pip-audit -f json` if available; otherwise check installed versions against `references/known-cves.md` and advise installing `pip-audit`
- **Go**: `govulncheck ./...`
- **Rust**: `cargo audit`
- **Generic / multi-language**: if `osv-scanner`, `trivy`, or `grype` is installed, run it against the repo root for broad lockfile coverage

If a scanner isn't installed and can't be installed in this environment, say so clearly and fall back to manual lockfile inspection. Don't silently skip a layer.

### 3. Scan for secrets

Run the bundled scanner, which uses high-signal regexes (AWS keys, Google API keys, GitHub tokens, private keys, JWTs, generic high-entropy assignments):

```bash
python scripts/scan_secrets.py <path>
```

Treat findings as candidates, not confirmed leaks — flag the file and line, and let the user confirm. Note that a secret in git history persists even after deletion; recommend rotation, not just removal.

### 4. Scan code patterns

Run the bundled pattern scanner for source-level risks across common languages:

```bash
python scripts/scan_patterns.py <path>
```

For deeper, language-specific analysis, also run a real SAST tool when available: `semgrep --config auto --json` is the best general option. If installed, prefer its results over the regex scanner and use the regex scanner only as a backstop.

See `references/vuln-patterns.md` for the catalog of patterns, why each matters, and what a real exploit looks like — read it when you need to explain a finding or judge whether a match is a true positive.

### 5. Triage and report

Rank by severity (Critical / High / Medium / Low). A finding's severity depends on exploitability and reachability, not just the rule that fired — a SQL injection in an auth endpoint outranks one in a dev-only script. Down-rank matches that are clearly test fixtures, comments, or examples, but still list them.

## Report format

Always use this structure:

```
# Security Scan: <project>

## Summary
<one paragraph: what was scanned, counts by severity, overall risk read>

## Critical & High findings
For each:
- **[SEVERITY] Title** — file:line
- What it is and why it's exploitable
- Suggested fix (concrete, with code where short)

## Medium & Low findings
<table: severity | type | location | note>

## Dependency advisories
<package | installed version | vulnerable range | CVE/advisory | fixed version>

## Recommendations
<prioritized next steps>

## Coverage & caveats
<what was and wasn't scanned; tools used; false-positive caveats>
```

Lead with the worst issues. Don't bury a hardcoded production key under twenty low-severity style nits.

## Boundaries

- This is defensive auditing only. Report and explain weaknesses; help fix them. Do not write exploit code, weaponize a finding, or assist scanning of a codebase the user has no legitimate relationship to.
- Never print full secret values in the report — mask them (e.g. `AKIA****…****`). Showing enough to locate the line is enough.
- You are not a substitute for a professional pentest or a complete SAST/DAST pipeline; state this in the caveats.
