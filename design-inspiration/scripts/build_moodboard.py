#!/usr/bin/env python3
"""Build a self-contained HTML moodboard of UI/UX design inspirations.

The caller (the model running the design-inspiration skill) supplies only a
manifest of *choices* — which designs to show, where they live, and why each
one is a functional match. This script owns the entire fragile part: for every
entry it runs a download cascade to obtain a real image, base64-embeds it, and
emits one portable HTML file. Keeping the cascade here (not spread across ad-hoc
curl calls) means it is written once, tested once, and reused on every run.

Capture cascade, per inspiration (highest fidelity first):
  1. explicit `image_url`            -> download it directly
  2. Playwright live capture of `page_url` (real Chromium screenshot -> JPEG);
     the primary screenshotter. Skipped for `needs_login` entries unless a
     `user_data_dir` with an established session is configured.
  3. `page_url` -> parse og:image / twitter:image -> download that
  4. thum.io screenshot service on `page_url` (fallback if Playwright is absent)
  5. all failed -> a labelled placeholder card (never crashes the build)

Playwright is optional: if Node or the capture helper is unavailable the cascade
degrades to og:image / thum.io, so the skill still works everywhere.

Manifest schema (JSON):
  {
    "target": "what is being designed, e.g. 'analysis History page'",
    "mode": "web" | "mobile",
    "full_page": false,                 # OPTIONAL: full-page vs viewport capture
    "user_data_dir": null,              # OPTIONAL: a Chromium profile you logged
                                        #   into (see capture.js --login) so authed
                                        #   inner screens can be captured
    "inspirations": [
      {
        "title": "Linear — Issues list",
        "source": "Linear",                 # short site/product name
        "page_url": "https://linear.app",    # the live page (captured by Playwright)
        "image_url": "https://.../shot.jpg", # OPTIONAL direct image (store CDN, thumbnail)
        "needs_login": false,                # OPTIONAL: relevant screen is behind auth
        "functional_match": "reverse-chron list, each row expands to a detail view",
        "notes": "Borrow: calm row rhythm; status pill left; hover reveals actions."
      }
    ]
  }

Usage:
  py build_moodboard.py --manifest manifest.json --out moodboard.html
  # optional overrides: --title "..."  --mode web|mobile  --today 2026-07-18

Stdlib only — no pip install needed. Runs on `py` (Windows) or `python3`.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from urllib.parse import urljoin

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURE_JS = os.path.join(HERE, "capture.js")
NODE_MODULES = os.path.join(HERE, "node_modules", "playwright")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
# Images smaller than this are almost always tracking pixels / error blobs, not
# real screenshots. og:images and real captures comfortably clear it.
MIN_IMAGE_BYTES = 2500
TIMEOUT = 30

try:
    _SSL_CTX = ssl.create_default_context()
except Exception:  # pragma: no cover - environments without a cert store
    _SSL_CTX = ssl._create_unverified_context()


def _get(url: str, timeout: int = TIMEOUT) -> tuple[bytes, str]:
    """Fetch a URL, following redirects. Returns (body, content_type)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
        return resp.read(), resp.headers.get("Content-Type", "").lower()


def _download_image(url: str, retries: int = 2) -> tuple[bytes, str] | None:
    """Download `url` if it is a real image. Returns (bytes, mime) or None."""
    last = ""
    for attempt in range(retries + 1):
        try:
            body, ctype = _get(url)
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(1.0 * (attempt + 1))
            continue
        if not ctype.startswith("image/"):
            last = f"non-image content-type: {ctype or '?'}"
            break
        if len(body) < MIN_IMAGE_BYTES:
            last = f"too small ({len(body)} bytes)"
            time.sleep(1.0 * (attempt + 1))  # may be an async placeholder; retry
            continue
        mime = ctype.split(";")[0].strip()
        return body, mime
    if last:
        print(f"      · {last}", file=sys.stderr)
    return None


_OG_RE = re.compile(
    r'<meta[^>]+(?:property|name)\s*=\s*["\'](?:og:image(?::secure_url)?|twitter:image(?::src)?)["\']'
    r'[^>]*\bcontent\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)
# Same, but with content= before the property= (order varies across sites).
_OG_RE_REV = re.compile(
    r'<meta[^>]+\bcontent\s*=\s*["\']([^"\']+)["\'][^>]*'
    r'(?:property|name)\s*=\s*["\'](?:og:image(?::secure_url)?|twitter:image(?::src)?)["\']',
    re.IGNORECASE,
)


def _extract_og_image(page_url: str) -> str | None:
    try:
        body, ctype = _get(page_url)
    except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as e:
        print(f"      · page fetch failed: {type(e).__name__}: {e}", file=sys.stderr)
        return None
    if "html" not in ctype and ctype:
        return None
    text = body.decode("utf-8", "ignore")
    for rx in (_OG_RE, _OG_RE_REV):
        m = rx.search(text)
        if m:
            return urljoin(page_url, html.unescape(m.group(1)))
    return None


def _thumio_url(page_url: str, mode: str) -> str:
    """A synchronous screenshot-service URL that renders `page_url` to a PNG.

    Verified working format: /get/width/<W>/wait/<sec>/<url>. thum.io captures a
    desktop viewport, so it is a genuine last resort for `mobile` mode — prefer
    real App Store / Play Store screenshots there.
    """
    width = 1200 if mode == "web" else 900
    return f"https://image.thum.io/get/width/{width}/wait/4/{page_url}"


def detect_node() -> str | None:
    """Return the `node` executable iff the Playwright capture helper is usable."""
    node = shutil.which("node")
    if node and os.path.isfile(CAPTURE_JS) and os.path.isdir(NODE_MODULES):
        return node
    return None


def _unlink(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


def playwright_capture(page_url: str, cfg: dict) -> tuple[bytes, str] | None:
    """Screenshot `page_url` with Playwright (via capture.js) to a JPEG."""
    node = cfg["node"]
    if not node:
        return None
    fd, tmp = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    cmd = [node, CAPTURE_JS, "--url", page_url, "--out", tmp,
           "--mode", cfg["mode"], "--timeout", "45000"]
    if cfg["full_page"]:
        cmd.append("--full-page")
    if cfg["user_data_dir"]:
        cmd += ["--user-data-dir", cfg["user_data_dir"]]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=cfg["timeout_s"])
    except subprocess.TimeoutExpired:
        print("      · playwright timed out", file=sys.stderr)
        _unlink(tmp)
        return None
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip().splitlines()
        print(f"      · playwright: {tail[-1] if tail else 'failed'}", file=sys.stderr)
        _unlink(tmp)
        return None
    try:
        with open(tmp, "rb") as f:
            body = f.read()
    except OSError:
        return None
    finally:
        _unlink(tmp)
    if len(body) < MIN_IMAGE_BYTES:
        print("      · playwright produced a tiny/blank image", file=sys.stderr)
        return None
    return body, "image/jpeg"


def resolve_image(entry: dict, cfg: dict) -> tuple[bytes, str, str] | None:
    """Run the capture cascade for one inspiration. Returns (bytes, mime, how)."""
    title = entry.get("title", "?")
    mode = cfg["mode"]

    # 1. explicit image_url — best for store screenshots & gallery shots of the
    #    actual inner screen (especially native-only mobile apps).
    if entry.get("image_url"):
        print(f"  [{title}] trying direct image_url …", file=sys.stderr)
        got = _download_image(entry["image_url"])
        if got:
            return got[0], got[1], "direct image_url"

    page_url = entry.get("page_url")
    needs_login = bool(entry.get("needs_login"))

    # 2. Playwright live capture — the primary screenshotter. Skipped for
    #    login-gated screens unless a logged-in profile is configured (else it
    #    would just shoot the login wall).
    if page_url and cfg["node"] and not (needs_login and not cfg["user_data_dir"]):
        prof = ", profile" if cfg["user_data_dir"] else ""
        print(f"  [{title}] capturing with Playwright ({mode}{prof}) …", file=sys.stderr)
        got = playwright_capture(page_url, cfg)
        if got:
            return got[0], got[1], f"playwright ({mode}{prof})"

    if page_url:
        # 3. og:image — banner-free curated hero; fallback when capture is off/failed.
        print(f"  [{title}] trying og:image on page …", file=sys.stderr)
        og = _extract_og_image(page_url)
        if og:
            got = _download_image(og)
            if got:
                return got[0], got[1], "og:image"

        # 4. thum.io — last-resort third-party screenshot (mainly for when
        #    Playwright is unavailable).
        print(f"  [{title}] falling back to screenshot service …", file=sys.stderr)
        got = _download_image(_thumio_url(page_url, mode), retries=3)
        if got:
            return got[0], got[1], "screenshot service (thum.io)"

    return None


def _data_uri(body: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(body).decode('ascii')}"


# ---------------------------------------------------------------- HTML render

def _placeholder_svg() -> str:
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 260'>"
        "<rect width='400' height='260' fill='#e9e9ee'/>"
        "<text x='200' y='130' font-family='sans-serif' font-size='15' fill='#9a9aa8' "
        "text-anchor='middle'>image unavailable — see source link</text></svg>"
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode("ascii")


def _card(entry: dict, img_src: str, how: str, mode: str) -> str:
    esc = lambda s: html.escape(str(s or ""))
    title = esc(entry.get("title", "Untitled"))
    source = esc(entry.get("source", ""))
    page_url = entry.get("page_url", "")
    match = esc(entry.get("functional_match", ""))
    notes = esc(entry.get("notes", ""))
    link = (
        f'<a class="src" href="{esc(page_url)}" target="_blank" rel="noopener">{source or "source"} ↗</a>'
        if page_url else f'<span class="src">{source}</span>'
    )
    how_badge = f'<span class="how" title="how this image was captured">{esc(how)}</span>'
    shot = "shot--mobile" if mode == "mobile" else "shot--web"
    frame = "" if mode == "mobile" else (
        '<div class="chrome"><span></span><span></span><span></span></div>'
    )
    # No loading="lazy": images are inline data URIs (nothing to defer), and with
    # height:auto cards a lazy image whose card starts at 0 height never enters the
    # viewport, so it never loads. Load eagerly.
    img = (f'<a class="zoom" href="{img_src}" target="_blank" rel="noopener" '
           f'title="Open full size"><img src="{img_src}" alt="{title}"></a>')
    return f"""    <figure class="card">
      <div class="{shot}">{frame}{img}</div>
      <figcaption>
        <div class="row"><h3>{title}</h3>{link}</div>
        <p class="match"><b>Functional match:</b> {match}</p>
        <p class="notes">{notes}</p>
        {how_badge}
      </figcaption>
    </figure>"""


def render_html(target: str, mode: str, today: str, cards: list[str], stats: dict) -> str:
    esc = html.escape
    mode_label = "Mobile app" if mode == "mobile" else "Web"
    summary = (
        f'{stats["ok"]} of {stats["total"]} images captured'
        + (f' · {stats["missing"]} unavailable' if stats["missing"] else "")
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Design inspiration · {esc(target)}</title>
<style>
  :root {{
    --bg:#f6f6f8; --card:#ffffff; --ink:#1c1c22; --muted:#6a6a78;
    --line:#e7e7ee; --accent:#4f46e5; --chip:#eef0f6;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#0f0f14; --card:#191921; --ink:#ececf2; --muted:#9a9aa8;
             --line:#26262f; --accent:#a5a0ff; --chip:#22222c; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
  header {{ max-width:1240px; margin:0 auto; padding:40px 24px 8px; }}
  .kicker {{ color:var(--accent); font-weight:600; letter-spacing:.04em;
    text-transform:uppercase; font-size:12px; }}
  h1 {{ margin:.15em 0 .1em; font-size:clamp(24px,4vw,34px); letter-spacing:-.02em; }}
  .meta {{ color:var(--muted); font-size:13px; }}
  .grid {{ max-width:1360px; margin:0 auto; padding:20px 24px 64px;
    display:grid; gap:26px; align-items:start;
    grid-template-columns:repeat(auto-fill,minmax(min(460px,100%),1fr)); }}
  .card {{ margin:0; background:var(--card); border:1px solid var(--line);
    border-radius:16px; overflow:hidden; display:flex; flex-direction:column; }}
  .zoom {{ display:block; cursor:zoom-in; line-height:0; }}
  .shot--web {{ background:#0c0c10; }}
  .shot--web .chrome {{ display:flex; gap:6px; padding:9px 12px; background:#1b1b22; }}
  .shot--web .chrome span {{ width:10px; height:10px; border-radius:50%; background:#3a3a44; }}
  /* full screenshot, uncropped: natural aspect at the card's width */
  .shot--web img {{ display:block; width:100%; height:auto; }}
  .shot--mobile {{ background:linear-gradient(160deg,#e9e9f2,#d7d7e6);
    padding:24px 0; display:flex; justify-content:center; }}
  @media (prefers-color-scheme: dark) {{
    .shot--mobile {{ background:linear-gradient(160deg,#20202b,#16161e); }}
  }}
  /* full phone screenshot, uncropped */
  .shot--mobile img {{ display:block; width:300px; max-width:90%; height:auto;
    border-radius:26px; border:5px solid #111; box-shadow:0 10px 30px rgba(0,0,0,.28); }}
  figcaption {{ padding:15px 17px 17px; display:flex; flex-direction:column; gap:8px; }}
  .row {{ display:flex; align-items:baseline; justify-content:space-between; gap:10px; }}
  h3 {{ margin:0; font-size:16px; letter-spacing:-.01em; }}
  .src {{ color:var(--accent); text-decoration:none; font-size:12.5px;
    font-weight:600; white-space:nowrap; }}
  .match {{ margin:0; font-size:13.5px; }}
  .match b {{ font-weight:600; }}
  .notes {{ margin:0; color:var(--muted); font-size:13.5px; }}
  .how {{ align-self:flex-start; margin-top:2px; font-size:11px; color:var(--muted);
    background:var(--chip); border-radius:999px; padding:2px 9px; }}
  footer {{ max-width:1240px; margin:0 auto; padding:0 24px 48px;
    color:var(--muted); font-size:12.5px; }}
</style>
</head>
<body>
<header>
  <div class="kicker">Design inspiration · {esc(mode_label)}</div>
  <h1>{esc(target)}</h1>
  <div class="meta">{esc(today)} · {esc(summary)} · sorted by relevance</div>
</header>
<main class="grid">
{chr(10).join(cards)}
</main>
<footer>
  Each card names its <b>functional match</b> to the target and what to borrow.
  <b>Click any screenshot to open it full-size.</b>
  Screenshots belong to their respective owners; links go to the live source.
</footer>
</body>
</html>
"""


# ------------------------------------------------------------------- driver

def main() -> int:
    ap = argparse.ArgumentParser(description="Build a design-inspiration moodboard HTML.")
    ap.add_argument("--manifest", required=True, help="path to manifest JSON")
    ap.add_argument("--out", required=True, help="output .html path")
    ap.add_argument("--title", help="override target title")
    ap.add_argument("--mode", choices=["web", "mobile"], help="override mode")
    ap.add_argument("--user-data-dir", dest="user_data_dir",
                    help="Chromium profile dir with an established login session")
    ap.add_argument("--today", default="", help="date string for the header")
    args = ap.parse_args()

    with open(args.manifest, encoding="utf-8") as f:
        data = json.load(f)

    target = args.title or data.get("target", "UI design references")
    mode = args.mode or data.get("mode", "web")
    inspirations = data.get("inspirations", [])
    if not inspirations:
        print("manifest has no 'inspirations'", file=sys.stderr)
        return 2
    if len(inspirations) < 5:
        print(f"WARNING: only {len(inspirations)} inspirations (skill asks for >=5).",
              file=sys.stderr)

    cfg = {
        "mode": mode,
        "full_page": bool(data.get("full_page", False)),
        "user_data_dir": args.user_data_dir or data.get("user_data_dir"),
        "node": detect_node(),
        "timeout_s": 100,
    }
    if cfg["node"]:
        print("capture: Playwright available — live screenshots (primary)", file=sys.stderr)
    else:
        print("capture: Playwright unavailable — using og:image / thum.io. "
              "Run `npm install` in the skill's scripts/ to enable it.", file=sys.stderr)

    cards, ok, missing = [], 0, 0
    for entry in inspirations:
        got = resolve_image(entry, cfg)
        if got:
            body, mime, how = got
            cards.append(_card(entry, _data_uri(body, mime), how, mode))
            ok += 1
            print(f"  -> ok via {how} ({len(body)//1024} KB)", file=sys.stderr)
        else:
            cards.append(_card(entry, _placeholder_svg(), "image unavailable", mode))
            missing += 1
            print(f"  -> MISSING image for '{entry.get('title','?')}'", file=sys.stderr)

    stats = {"total": len(inspirations), "ok": ok, "missing": missing}
    html_doc = render_html(target, mode, args.today, cards, stats)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(f"\nWrote {args.out}  ({ok}/{len(inspirations)} images embedded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
