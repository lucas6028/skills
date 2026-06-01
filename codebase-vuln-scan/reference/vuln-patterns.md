# Vulnerability Patterns Reference

Read this when explaining a finding or judging whether a regex match is a true positive. Each entry: what it is, why it matters, how to confirm, and the fix.

## Contents
- Injection (SQL, command, code)
- Cross-site scripting (XSS)
- Path traversal
- Insecure deserialization
- Weak cryptography
- SSRF
- Secrets management
- Transport security

## Injection

### SQL injection
**What**: User input concatenated or interpolated directly into a SQL string. **Why**: Lets an attacker alter query logic — dump tables, bypass auth, drop data. **Confirm**: Trace whether the interpolated value reaches the query from an untrusted source (request params, body, headers) without parameterization. A constant or internal value is a false positive. **Fix**: Use parameterized queries / prepared statements (`cursor.execute("... WHERE id = %s", (id,))`), never string formatting.

### Command injection
**What**: Shell command built from input, or `shell=True` / `os.system` / `child_process.exec` with dynamic parts. **Why**: Arbitrary command execution on the host. **Confirm**: Is any part of the command derived from input? Static commands are fine. **Fix**: Pass args as a list with `shell=False` (`subprocess.run(["ls", path])`), or use `execFile` in Node. Validate/allowlist where a shell is unavoidable.

### Code injection
**What**: `eval`, `exec`, `Function()`, dynamic `require`/`import` on input. **Why**: Full code execution in the app's context. **Fix**: Replace with explicit parsing (`json.loads`, `ast.literal_eval`) or a dispatch table mapping allowed names to functions.

## Cross-site scripting (XSS)
**What**: Untrusted data written into HTML — `innerHTML`, `dangerouslySetInnerHTML`, unescaped template output. **Why**: Runs attacker JS in victims' browsers (session theft, defacement). **Confirm**: Does the assigned value come from user input and is it unescaped? **Fix**: Use `textContent`, framework auto-escaping, and sanitize rich HTML with a vetted library (DOMPurify).

## Path traversal
**What**: File path built from input without normalization, allowing `../` to escape the intended directory. **Why**: Read/write arbitrary files. **Confirm**: Is the path joined from a request value? **Fix**: Resolve to an absolute path and verify it stays within an allowed base dir; reject `..`; prefer an ID-to-path lookup.

## Insecure deserialization
**What**: `pickle.load`, `yaml.load` (non-safe), Java native deserialization, PHP `unserialize` on untrusted bytes. **Why**: Many deserializers can instantiate arbitrary objects → RCE. **Fix**: Use data-only formats (JSON), `yaml.safe_load`, and signed/validated payloads if a rich format is required.

## Weak cryptography
**What**: MD5/SHA1 for security purposes, ECB mode, hardcoded IVs, small/static keys, `Math.random()` for tokens. **Why**: Collisions and predictability undermine integrity and secrecy. **Fix**: SHA-256+ for hashing, bcrypt/scrypt/argon2 for passwords, AES-GCM with random IVs, a CSPRNG (`secrets`, `crypto.randomBytes`) for tokens.

## SSRF (server-side request forgery)
**What**: Server fetches a URL supplied by the user. **Why**: Lets an attacker reach internal services, cloud metadata endpoints (169.254.169.254), etc. **Fix**: Allowlist destinations, block private/link-local ranges, disable redirects to internal hosts.

## Secrets management
**What**: API keys, passwords, private keys, tokens hardcoded in source or committed config. **Why**: Anyone with repo access (or git history) gets them; they leak via forks, backups, CI logs. **Confirm**: Is it a real credential vs. a placeholder/test value? **Fix**: Move to environment variables or a secrets manager; **rotate** any exposed secret — deletion does not purge git history. Add patterns to `.gitignore` and consider history rewriting (BFG/filter-repo) only after rotation.

## Transport security
**What**: `verify=False`, disabled cert checks, `http://` for sensitive traffic, accepting all TLS. **Why**: Enables man-in-the-middle interception. **Fix**: Keep verification on, pin where appropriate, enforce HTTPS/HSTS.

## Severity judgment
Severity = impact × exploitability × reachability. A high-impact rule in dead code, tests, or examples is lower real severity — note it but down-rank. Conversely, a "medium" pattern on an unauthenticated, internet-facing endpoint may warrant High. Always state the reasoning, not just the label.
