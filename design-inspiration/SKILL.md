---
name: design-inspiration
description: >-
  Gather real-world UI/UX design inspiration before designing a page, screen, or
  component. Finds 5+ shipped products/apps whose interface solves a FUNCTIONALLY
  similar problem, captures a real screenshot of each, and assembles them into one
  self-contained HTML moodboard with source links and concrete "what to borrow"
  notes. Use this whenever the user is about to design or redesign any UI —
  phrasings like "design the X page", "let's build the X screen/component",
  "I need inspiration/references for X", "make a moodboard for X", "how should
  the X page look", or invoking the skill with a `web` / `mobile` argument
  (default `web`). Reach for it even when the user just says "design X" without
  saying "inspiration" — surfacing how others solved the same problem is almost
  always the right first move before committing to a layout.
---

# Design Inspiration

Before designing a UI, look at how good products already solved the **same problem**.
This skill collects 5+ real examples that share the target's *function*, captures a real
screenshot of each, and builds a single portable HTML moodboard the user can browse to
pick a direction — with per-example notes on what specifically to borrow.

The output is **one `.html` file** with every screenshot base64-embedded, so it's
double-click-to-view and needs no server or assets folder.

## Modes

An optional argument selects the source pool and how pages are captured (default **web**):
- **`web`** — landing pages, dashboards, web apps. Captured by rendering the live page
  in a real browser (Playwright), so the shot shows the actual current UI.
- **`mobile`** — app screens. For **mobile web**, Playwright emulates a phone (real
  device viewport). For **native-only apps** (no usable web version), use **App Store /
  Play Store screenshots** via a direct `image_url` — those are the real in-app screens.

The mode also styles the moodboard: `web` frames shots in browser chrome, `mobile` in a phone.

## How images are captured

The build script (`scripts/build_moodboard.py`) owns the capture cascade, so you never
screenshot or curl images by hand — you just choose designs and supply URLs. Per entry:

1. **`image_url`** you provide → downloaded (store screenshots, gallery shots).
2. **Playwright live capture** of `page_url` → a real browser renders the page to a JPEG.
   This is the primary path and shows the actual UI, not a marketing hero.
3. **`og:image`** of `page_url` → fallback (also handy when a capture is occluded).
4. **thum.io** screenshot service → last resort (mainly if Playwright isn't installed).

Playwright is optional — without Node/Playwright the cascade still works via og/thum.
**Known limitation:** a live capture can catch a cookie/consent banner over the design
(the capturer hides common banners but won't click "Accept"); if a shot looks occluded,
prefer that entry's `og:image` or a gallery `image_url`.

## The one thing that makes this useful: functional match

It is easy to return "5 pretty pages" and useless. The value is examples that solve the
**same functional problem** as the target. So the workflow leads with the *function*, and
every pick must justify itself against it. If you can't say in one line why an example is
functionally relevant, drop it.

## Workflow

### 1. Name the target and its functional archetype
Identify what's being designed. Infer it from the current project and conversation —
read the relevant component/route if it exists (e.g. the History page, the chat panel).
Then state the **functional archetype** in one concrete line, because that's what you
search for. Examples:
- History page → "reverse-chronological list of past records, each row opening a detail view"
- Chat panel → "streaming assistant conversation grounded in a document, with input states"
- Upload+analyze → "drop a file, watch progress, then land on a results dashboard"

Only ask the user a question if the target or mode is genuinely unclear — one question,
not a barrage. Otherwise proceed.

### 2. Find 5+ examples that actually SHOW the screen

**The golden rule — label, image, and link must all point at the same screen.** Each
card's image must show the screen its title claims, and its `page_url` must lead
somewhere that genuinely displays that screen (to a logged-out visitor). A card titled
"Linear — Issues" that shows or links Linear's *marketing homepage* is wrong and makes
the moodboard useless — the reader can't find the screen you promised. This is the single
most important thing in this skill; it is easy to get wrong.

Pick the source by the **type of screen** — this bright line removes the guesswork:

- **App-internal screens** — anything you'd only see after signing in: lists, feeds,
  history, dashboards, inboxes, detail views, settings, profiles. Real products keep
  these behind login, and their public homepage is just *marketing*, so **do not capture
  the homepage.** Instead use a **design-gallery shot that depicts the screen** — Dribbble
  is public and ideal — or a public **app-store screenshot** (mobile). Set `image_url` to
  the direct shot/screenshot image and `page_url` to the shot's own page (which shows the
  design). Follow the **Dribbble recipe in `references/sources.md`** — it yields an
  uncropped image URL plus the shot link.
- **Inherently-public pages** — landing, pricing, onboarding-marketing, docs, blog. Here
  the live page *is* the screen, so a Playwright capture of that exact URL is correct and
  the link is genuinely useful. Give just the `page_url`.

If the only thing you can get for an inner screen is the homepage, **relabel the card
honestly** ("Linear — product overview") or pick a different source that shows the real
screen — never label a homepage as an inner screen.

For each pick, capture: `title`, `source` (product/designer name), `page_url` (a page
that shows the screen), `image_url` (the gallery/store image, for internal screens), a
one-line **`functional_match`**, and **`notes`** on what to borrow. Aim for 5–7 strong,
distinct picks. **Then look at every image you chose** and confirm it really shows the
archetype before building — a shot's title can promise more than the picture delivers.

### 3. Handle login-gated screens — ask first
If the actual screen you want to reference sits behind a login (many great inner
screens do), **stop and ask the user before capturing it.** You must never enter or
handle anyone's credentials. When a pick needs auth, either:
- use a **public alternative** that shows the same pattern (a marketing page whose hero
  is the real screen, a gallery/store screenshot via `image_url`), or
- if the user wants that specific authed screen, have **them** log in once themselves:
  ```bash
  node C:/Users/ttsh1/.claude/skills/design-inspiration/scripts/capture.js \
    --login --url <site-login-url> --user-data-dir <profile-dir>
  ```
  This opens a real browser window; the user signs in and closes it; the session is
  saved to `<profile-dir>` — the skill never sees the password. Then pass that dir via
  `--user-data-dir` (below) and mark those entries `"needs_login": true`, so captures
  reuse the session. Default to public sources; treat authed capture as opt-in.

### 4. Build the moodboard
Write a manifest JSON (schema below), then run the build script — it owns the entire
capture cascade (`image_url` → Playwright live capture → `og:image` → thum.io →
placeholder), so you never screenshot or curl images yourself:

```bash
py C:/Users/ttsh1/.claude/skills/design-inspiration/scripts/build_moodboard.py \
  --manifest manifest.json --out <YYYY-MM-DD>-<slug>-inspiration.html \
  --today <YYYY-MM-DD>            # add: --user-data-dir <dir> only for authed captures
```
Use `py` on Windows, `python3` on macOS/Linux. **One-time setup:** Playwright capture
needs `npm install` run once in the skill's `scripts/` folder (it reuses the shared
browser cache — no large download). If Node/Playwright isn't present the build still
works via og:image/thum.io. Put the output outside the project's version control (e.g.
the scratchpad dir), with a date-prefixed filename so files stay time-sorted.

Manifest schema:
```json
{
  "target": "analysis History page",
  "mode": "web",
  "full_page": false,
  "user_data_dir": null,
  "inspirations": [
    {
      "title": "Linear — Issues",
      "source": "Linear",
      "page_url": "https://linear.app",
      "image_url": null,
      "needs_login": false,
      "functional_match": "reverse-chron list; each row expands to a detail pane",
      "notes": "Borrow: calm row rhythm, status pill on the left, hover-reveal quick actions."
    }
  ]
}
```

### 5. Verify, then hand off
Read the script's stderr summary: it prints how each image was captured and flags any
that fell through to a placeholder. If more than one is missing, find a better `page_url`
or a direct `image_url` for those and rebuild — a moodboard of placeholders is worthless.
Open the file to eyeball it, then tell the user where it is and give a short synthesis:
the 2–3 patterns that recur across the examples and your recommended direction for the
target. The moodboard is the artifact; your synthesis is the point.

## Quality bar
- **≥5 examples**, each with a genuine one-line functional match — not just nice visuals.
- **Real screenshots**, embedded and visible (not broken/placeholder cards).
- **Diverse**: don't return five near-identical takes; span the design space of the pattern.
- **Actionable notes**: "borrow the left-rail status pills", not "clean and modern".
- **Working links** back to each live source.
