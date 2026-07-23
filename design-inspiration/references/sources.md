# Inspiration sources & capture cascade

Where to find real UI/UX examples, and how to turn each into an embeddable image.
Everything here was verified working from this machine (Windows, `curl`/`urllib`).

## Contents
- [The capture cascade](#the-capture-cascade) — how `build_moodboard.py` gets each image
- [Web sources](#web-sources-mode-web)
- [Mobile sources](#mobile-sources-mode-mobile)
- [Verified URL formats](#verified-url-formats)

---

## The capture cascade

You (the model) do **not** screenshot or download images by hand. You choose designs and
write a manifest of *choices*; `scripts/build_moodboard.py` runs this cascade per entry:

1. **`image_url`** (if you provide one) → downloaded directly. Use for App/Play Store
   screenshot CDN links and gallery thumbnail URLs — the real inner screen, most stable.
2. **Playwright live capture** of `page_url` → a real Chromium renders the page to a JPEG
   (web viewport, or phone emulation in `mobile` mode). Primary path: shows the actual
   current UI, not a marketing hero. Skipped for `needs_login` entries unless a
   `user_data_dir` session is set. Needs Node + `npm install` in `scripts/` (browser is
   the shared cache — no big download); degrades to og/thum if absent.
3. **`og:image` / `twitter:image`** of `page_url` → curated hero. Good fallback, and
   useful when a live capture is occluded by a cookie banner.
4. **thum.io screenshot service** on `page_url` → third-party render, last resort.
5. If all fail → a labelled placeholder card (the build never crashes).

So your job is to supply, per inspiration, a good `page_url` and — when you can grab
one — a direct `image_url`. Order entries best-match-first; the moodboard preserves order.

**Fidelity order = source order.** A live Playwright shot of the real page beats a
marketing `og:image`; a direct store/gallery `image_url` of the actual inner screen
beats both. thum.io renders a *desktop* viewport, so it's a poor `mobile` fallback — use
real store screenshots there. For **native-only apps** (no web version), skip Playwright
and give a store-screenshot `image_url`.

**Never enter credentials.** For a screen behind login, ask the user first; the user can
log in themselves via `capture.js --login --user-data-dir <dir>` (opens a window; the
skill never sees the password), then captures reuse that profile. Note: only sessions
backed by persistent cookies survive reuse — pure session-cookie logins won't.

---

## Web sources (`mode: web`)

Two kinds of screen, two strategies (see the bright line in SKILL.md step 2):
- **App-internal screens** (lists, feeds, history, dashboards, detail views, settings) →
  use a **Dribbble shot** that shows the screen (recipe below). Do *not* capture a
  product homepage for these.
- **Inherently-public pages** (landing, pricing, docs) → give the live `page_url`; the
  build script's Playwright capture / og:image handles it.

### Dribbble recipe (public — primary for internal screens)

Dribbble is JS-rendered, so drive it in the **in-app browser**, not curl:

1. Navigate to `https://dribbble.com/search/shots/popular/?q=<archetype>` (e.g.
   `activity feed dashboard`, `transactions history table`, `workout history app`).
2. Extract shot links + image URLs from the loaded grid:
   ```js
   [...document.querySelectorAll('a[href*="/shots/"]')].flatMap(el => {
     const m = (el.getAttribute('href')||'').match(/\/shots\/(\d+-[^/?#]+)/);
     if (!m) return [];
     const img = el.querySelector('img') || el.parentElement?.querySelector('img');
     const base = img && (img.currentSrc||img.src)?.replace(/\?.*$/, '');   // strip query
     return [{ shot: 'https://dribbble.com/shots/'+m[1], base }];
   }).slice(0, 8)
   ```
3. For each shot you keep:
   - `image_url` = `<base>?resize=1400x&format=webp` — **width-only `resize=Wx` (no
     height) preserves aspect and does NOT crop.** (A `WxH` box like `1200x1200` *crops*;
     verified. Never add a height or `vertical=center`.)
   - `page_url` = the shot page (`https://dribbble.com/shots/<id-slug>`) — the link that
     shows the design.
   - `source` = `Dribbble` (or the design's name); `title` = what the screen is.
4. **Look at each `image_url` before using it** — a shot titled "…Dashboard" may be a
   logo wall or a phone-mockup collage, not the screen. Keep only ones that clearly show
   the archetype.

Because `image_url` is the first step of the capture cascade, gallery shots are embedded
directly — Playwright never captures Dribbble's own chrome.

### Other galleries to browse (public)
- **Refero** `https://refero.design` — real shipped product screens, searchable by screen type.
- **Land-book** / **Godly** / **Awwwards** / **SaaS Landing Page** — mostly landing pages.
- **Mobbin** `https://mobbin.com` — the best for real product flows, but **login-gated**;
  use it to *spot* which apps nail a pattern, then pull the imagery from Dribbble (public)
  or the app stores. Per the login policy, don't sign in unless the user asks.

## Mobile sources (`mode: mobile`)

The single best source of **real, downloadable mobile screenshots** is the app stores —
every listing publishes device screenshots on a public CDN.

- **Apple App Store** — open `https://apps.apple.com/us/app/<slug>/id<APPID>`, extract
  the `mzstatic.com` screenshot URLs (see format below). These are the actual in-app
  screens the developer submitted. Verified: real 600×1300 portrait PNGs.
- **Google Play** — `https://play.google.com/store/apps/details?id=<pkg>`; screenshot
  images are on `play-lh.googleusercontent.com` (resize by appending `=w<width>`).
- **Mobbin (mobile)** `https://mobbin.com/browse/ios` — the gold standard for mobile
  flows, but **login-gated**. Use to identify which apps nail the pattern, then pull
  those apps' real screenshots from the App Store.
- **Dribbble / Pttrns / UI Sources** — concept & pattern galleries for ideas.

To find an app's App Store id, WebSearch `"<app name>" site:apps.apple.com`, or browse
the store. Prefer 2–3 well-known apps that genuinely share the target's function over
five obscure ones.

---

## Verified URL formats

Copy these exactly — they were tested live and work; a wrong format fails silently.

**App Store screenshot CDN** (put as `image_url`). Extract from an App Store page's
HTML, then resize by editing the trailing `WIDTHxHEIGHTbb.EXT` segment:
```
https://is1-ssl.mzstatic.com/image/thumb/.../<name>.jpg/600x1300bb.png
                                                        ^^^^^^^^ set your own size
```
Grep an App Store page for screenshot URLs:
```
curl -sL -A "<browser UA>" "https://apps.apple.com/us/app/<slug>/id<APPID>" \
  | grep -oE 'https://[a-z0-9.-]*mzstatic\.com/image/thumb/[^" ]+/[0-9]+x[0-9]+bb\.(png|jpg|webp)'
```
Skip the `1200x630wa.png` result (that's the share image); the portrait `NNNxNNNbb`
entries are the real app screens.

**Google Play screenshot** (put as `image_url`): the `play-lh.googleusercontent.com`
URLs on a details page; append `=w1000` for size.

**Open Graph image** — no format needed; just give the product's `page_url` and the
build script extracts `og:image` itself. (Verified: `https://linear.app`.)

**thum.io screenshot service** — the script builds this automatically from `page_url`.
Format, for reference: `https://image.thum.io/get/width/<W>/wait/<sec>/<full_url>`.

**Do NOT use WordPress mShots** (`s.wordpress.com/mshots/...`) — it returns HTTP 403
from this machine. thum.io is the working screenshot service.
