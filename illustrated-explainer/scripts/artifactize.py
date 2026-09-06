#!/usr/bin/env python3
"""Turn the standalone article .html into an Artifact-ready body file.

Why this exists: the article ships twice — as a portable local .html (double-click,
CDN is fine) and as a published Artifact. The Artifact runtime is stricter:

  * the page is wrapped in <!doctype>…<head>…</head><body> at publish time, so the
    file must contain no <!DOCTYPE>/<html>/<head>/<body> tags of its own;
  * a CSP blocks every external stylesheet except fonts.googleapis.com — so the
    KaTeX and highlight.js CSS (and KaTeX's own woff2 faces) must be inlined;
  * scripts load only from cdnjs.cloudflare.com, cdn.jsdelivr.net/npm/,
    cdn.tailwindcss.com and code.jquery.com — jsdelivr's /gh/ path is NOT allowed.

This script does that mechanical conversion so each run doesn't redo it by hand.

Usage
-----
    python artifactize.py transformer-explained.html
    python artifactize.py article.html -o article.artifact.html
    python artifactize.py article.html --offline   # don't fetch; just unwrap + rewrite

Then publish the result with the Artifact tool (file_path = the output file).
"""
import argparse
import base64
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (artifactize)"}

# Scripts on hosts the Artifact CSP blocks -> allowlisted cdnjs equivalents.
SCRIPT_REWRITES = {
    "cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js":
        "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js",
    "cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js":
        "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.11/katex.min.js",
    "cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js":
        "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.11/contrib/auto-render.min.js",
}
ALLOWED_SCRIPT_HOSTS = ("cdnjs.cloudflare.com", "cdn.tailwindcss.com", "code.jquery.com")


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()


def inline_font_faces(css: str, base_url: str) -> str:
    """Replace url(...) inside @font-face src lists with base64 data URIs.

    Keeps only the woff2 entry of each src list (ttf/woff are redundant fallbacks
    and would triple the page weight), and inlines it.
    """
    cache: dict[str, str] = {}

    def do_src(m: re.Match) -> str:
        body = m.group(1)
        entries = [e.strip() for e in body.split(",")]
        woff2 = [e for e in entries if ".woff2" in e] or entries
        out = []
        for entry in woff2:
            um = re.search(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", entry)
            if not um:
                out.append(entry)
                continue
            ref = um.group(1)
            if ref.startswith("data:"):
                out.append(entry)
                continue
            abs_url = urllib.parse.urljoin(base_url, ref)
            if abs_url not in cache:
                mime = "font/woff2" if ".woff2" in ref else "application/octet-stream"
                cache[abs_url] = f"data:{mime};base64," + base64.b64encode(fetch(abs_url)).decode()
                print(f"    inlined font {ref}", file=sys.stderr)
            out.append(entry[:um.start()] + f"url({cache[abs_url]})" + entry[um.end():])
        return "src:" + ",".join(out)

    # minified CSS ends the last declaration with "}" rather than ";"
    return re.sub(r"src\s*:\s*([^;}]+)(?=[;}])", do_src, css)


def inline_stylesheets(head: str, offline: bool) -> str:
    """Turn every <link rel=stylesheet href=…> into an inline <style> block."""
    def repl(m: re.Match) -> str:
        tag = m.group(0)
        href_m = re.search(r'href=["\']([^"\']+)["\']', tag)
        if not href_m:
            return tag
        href = href_m.group(1)
        if href.startswith("https://fonts.googleapis.com"):
            return tag  # the one stylesheet host the CSP allows
        if offline:
            print(f"  !! --offline: dropped stylesheet {href} (page will be unstyled there)", file=sys.stderr)
            return f"<!-- artifactize: dropped external stylesheet {href} -->"
        print(f"  fetching stylesheet {href}", file=sys.stderr)
        css = fetch(href).decode("utf-8", "replace")
        css = inline_font_faces(css, href)
        return f"<style>/* inlined from {href} */\n{css}\n</style>"

    return re.sub(r'<link\b[^>]*rel=["\']stylesheet["\'][^>]*>', repl, head, flags=re.I)


def rewrite_scripts(html: str) -> str:
    def repl(m: re.Match) -> str:
        tag, url = m.group(0), m.group(1)
        for blocked, allowed in SCRIPT_REWRITES.items():
            if blocked in url:
                print(f"  script {url}\n      -> {allowed}", file=sys.stderr)
                return tag.replace(url, allowed)
        host = urllib.parse.urlparse(url).netloc
        ok = host in ALLOWED_SCRIPT_HOSTS or (host == "cdn.jsdelivr.net" and "/npm/" in url)
        if not ok:
            print(f"  !! script from a blocked host, fix by hand: {url}", file=sys.stderr)
        return tag

    return re.sub(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>', repl, html, flags=re.I)


def unwrap(html: str) -> str:
    """Strip the document skeleton; the Artifact runtime supplies its own."""
    head_m = re.search(r"<head\b[^>]*>(.*?)</head>", html, re.S | re.I)
    body_m = re.search(r"<body\b[^>]*>(.*?)</body>", html, re.S | re.I)
    if not head_m or not body_m:
        # Already unwrapped, or an unusual document — pass through untouched.
        return html
    head = head_m.group(1)
    # charset + viewport come from the runtime's own <head>.
    head = re.sub(r'<meta\b[^>]*\b(charset|name=["\']viewport["\'])[^>]*>', "", head, flags=re.I)
    return head.strip() + "\n\n" + body_m.group(1).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="the standalone article .html")
    ap.add_argument("-o", "--output", type=Path, help="default: <input>.artifact.html")
    ap.add_argument("--offline", action="store_true", help="skip network fetches (drops external CSS)")
    a = ap.parse_args()

    html = a.input.read_text(encoding="utf-8")
    head_m = re.search(r"<head\b[^>]*>(.*?)</head>", html, re.S | re.I)
    if head_m:
        html = html[:head_m.start(1)] + inline_stylesheets(head_m.group(1), a.offline) + html[head_m.end(1):]
    html = rewrite_scripts(html)
    out_html = unwrap(html)

    if not re.search(r"<title>", out_html, re.I):
        print("  !! no <title> — the Artifact needs one at the top of the file", file=sys.stderr)

    out = a.output or a.input.with_suffix(".artifact.html")
    out.write_text(out_html, encoding="utf-8")
    print(f"\nwrote {out}  ({len(out_html.encode()) / 1024:.0f} KB; Artifact limit is 16 MB)")
    print("publish it with the Artifact tool: file_path=%s, plus favicon + description." % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
