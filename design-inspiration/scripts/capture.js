#!/usr/bin/env node
/*
 * capture.js — Playwright screenshot helper for the design-inspiration skill.
 *
 * Renders a live page in a real Chromium and writes a JPEG to disk, so the
 * moodboard can embed an actual, up-to-date screenshot (far more faithful than
 * a marketing og:image or a third-party thumbnail service). build_moodboard.py
 * calls this per inspiration; you can also run it by hand.
 *
 * It NEVER clicks anything — no consent, no login, no forms — so it can't take a
 * side-effectful action on a page. It only navigates and screenshots. Cookie/
 * consent banners are hidden with injected CSS (cosmetic, best-effort), not
 * clicked away.
 *
 * Usage:
 *   node capture.js --url <url> --out <file.jpg> [--mode web|mobile]
 *        [--device "iPhone 13"] [--full-page] [--wait <ms>] [--timeout <ms>]
 *        [--user-data-dir <dir>]
 *
 *   # Log in yourself once, so authed inner screens can be captured later.
 *   # Opens a real window; you sign in; close it; the session persists on disk.
 *   # This script never sees or types your credentials.
 *   node capture.js --login --url <login-url> --user-data-dir <dir> [--mode web|mobile]
 *
 * Requires: `npm install` in this folder (installs playwright; browser is the
 * shared ms-playwright cache). Exit 0 + "OK <out>" on success; non-zero on failure.
 */
const { chromium, devices } = require('playwright');

function parseArgs(argv) {
  const a = { mode: 'web', device: 'iPhone 13', wait: 2500, timeout: 45000,
              fullPage: false, login: false, url: null, out: null, userDataDir: null };
  for (let i = 2; i < argv.length; i++) {
    const t = argv[i];
    const next = () => argv[++i];
    switch (t) {
      case '--url': a.url = next(); break;
      case '--out': a.out = next(); break;
      case '--mode': a.mode = next(); break;
      case '--device': a.device = next(); break;
      case '--wait': a.wait = parseInt(next(), 10); break;
      case '--timeout': a.timeout = parseInt(next(), 10); break;
      case '--user-data-dir': a.userDataDir = next(); break;
      case '--full-page': a.fullPage = true; break;
      case '--login': a.login = true; break;
      default: /* ignore unknown */ break;
    }
  }
  return a;
}

// Common cookie/consent frameworks — hidden, not clicked, so a full-screen
// banner doesn't cover the design. Best-effort; missing one just means the
// banner stays in the shot (documented limitation).
const HIDE_CSS = `
  #onetrust-banner-sdk, #onetrust-consent-sdk, .onetrust-pc-dark-filter,
  #CybotCookiebotDialog, #cookiescript_injected, #usercentrics-root,
  [id*="cookie" i][class*="banner" i], [class*="cookie-consent" i],
  [class*="cookie-banner" i], [id*="cookie-notice" i], [aria-label*="cookie" i],
  [id*="gdpr" i], [class*="gdpr" i], .cc-window, #cookie-law-info-bar {
    display: none !important; visibility: hidden !important;
  }
`;

function contextOptions(a) {
  if (a.mode === 'mobile') {
    const dev = devices[a.device] || devices['iPhone 13']; // real device DPR (2–3x)
    return { ...dev };
  }
  // 2x device scale => a 1280x900 viewport renders at 2560x1800, so text stays
  // sharp when the moodboard scales the image down into a card.
  return { viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2 };
}

async function runLogin(a) {
  if (!a.userDataDir) throw new Error('--login requires --user-data-dir');
  const ctx = await chromium.launchPersistentContext(a.userDataDir, {
    headless: false, ...contextOptions(a),
  });
  const page = ctx.pages()[0] || (await ctx.newPage());
  if (a.url) await page.goto(a.url, { waitUntil: 'load', timeout: a.timeout }).catch(() => {});
  process.stderr.write(
    'A browser window is open. Log in, then CLOSE the window to save the session.\n'
  );
  // Wait for the human to finish and close the window (cap at 10 minutes).
  await Promise.race([
    new Promise((res) => ctx.on('close', res)),
    new Promise((res) => setTimeout(res, 10 * 60 * 1000)),
  ]);
  await ctx.close().catch(() => {});
  process.stdout.write(`OK session saved to ${a.userDataDir}\n`);
}

async function runCapture(a) {
  if (!a.url || !a.out) throw new Error('capture needs --url and --out');
  let ctx, browser;
  if (a.userDataDir) {
    ctx = await chromium.launchPersistentContext(a.userDataDir, {
      headless: true, ...contextOptions(a),
    });
  } else {
    browser = await chromium.launch({ headless: true });
    ctx = await browser.newContext(contextOptions(a));
  }
  try {
    const page = ctx.pages()[0] || (await ctx.newPage());
    await page.goto(a.url, { waitUntil: 'load', timeout: a.timeout });
    // give late content/animations a moment; networkidle is best-effort
    await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
    await page.addStyleTag({ content: HIDE_CSS }).catch(() => {});
    await page.waitForTimeout(a.wait);
    await page.screenshot({ path: a.out, type: 'jpeg', quality: 88, fullPage: a.fullPage });
    process.stdout.write(`OK ${a.out}\n`);
  } finally {
    if (ctx) await ctx.close().catch(() => {});
    if (browser) await browser.close().catch(() => {});
  }
}

(async () => {
  const a = parseArgs(process.argv);
  if (a.login) await runLogin(a);
  else await runCapture(a);
})().catch((e) => {
  process.stderr.write(`capture failed: ${e.message}\n`);
  process.exit(1);
});
