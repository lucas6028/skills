# Dependency & CVE Scanning Reference

How to check dependencies per ecosystem, in priority order. Always prefer a real, regularly-updated scanner over manual lookups — advisory databases change daily.

## Tool selection

| Ecosystem | First choice | Command |
|-----------|-------------|---------|
| Node | npm audit | `npm audit --json` (or `pnpm audit` / `yarn npm audit`) |
| Python | pip-audit | `pip-audit -f json` |
| Go | govulncheck | `govulncheck ./...` |
| Rust | cargo-audit | `cargo audit` |
| Ruby | bundler-audit | `bundle audit check --update` |
| PHP | local-php-security-checker / composer | `composer audit` |
| Java | OWASP dep-check | `dependency-check --scan .` |
| Multi-language | osv-scanner / trivy / grype | `osv-scanner -r .` · `trivy fs .` · `grype dir:.` |

If none of the language-native tools are installed, `osv-scanner` (Google OSV) gives the broadest lockfile coverage with one binary and is the best generic fallback.

## When no scanner is available

1. Parse the lockfile to get exact installed versions (`package-lock.json`, `poetry.lock`, `go.sum`, `Cargo.lock`).
2. Query the OSV API for any package without running a local tool:
   ```bash
   curl -s https://api.osv.dev/v1/query -d \
     '{"package":{"name":"<name>","ecosystem":"PyPI"},"version":"<ver>"}'
   ```
   Ecosystem values: `npm`, `PyPI`, `Go`, `crates.io`, `Maven`, `RubyGems`, `Packagist`.
3. If even network access is unavailable, say so explicitly and list the dependency versions you found so the user can scan them elsewhere — don't guess at CVEs from memory, which is stale.

## Reading results

For each advisory report: package name, installed version, vulnerable range, advisory ID (CVE / GHSA), severity (CVSS), and the fixed version. Prioritize ones that are (a) high CVSS, (b) reachable from the app's own code rather than a transitive dev-only dep, and (c) have a fix available. A high-severity CVE in a build-time-only dependency is usually lower real risk than a medium one in a runtime request path.

## Remediation advice

- Bump to the fixed version; if a direct upgrade breaks, check whether an override/resolution can patch a transitive dep.
- Where no fix exists, note the mitigation (disable the vulnerable feature, add input validation, pin and monitor).
- Recommend wiring the chosen scanner into CI so regressions are caught automatically.
