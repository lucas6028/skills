---
name: illustrated-explainer
description: >-
  Produce a complete, richly illustrated deep-dive article (single self-contained
  HTML file, Traditional Chinese) explaining an algorithm, framework, technology,
  system, or research paper/academic work that the user wants to learn. The output
  is a Zhihu / distill.pub-style explainer: intuition first, then math and diagrams,
  worked examples, code, results, and cited sources — with inlined figures (concept
  SVG/Mermaid diagrams, matplotlib charts, original paper figures, optional AI cover
  art). Use this whenever the user names a technical topic or paper and wants to
  UNDERSTAND it in depth — phrasings like "介紹一下 X", "我想學 X", "幫我把 X 講清楚",
  "做一篇 X 的完整介紹", "explain paper Y", "deep dive on Z", "寫一篇圖文並茂的 X 教學" —
  even if they don't explicitly say "article" or "HTML". Prefer this over a plain
  chat explanation whenever the user wants something complete, illustrated, and
  keepable rather than a quick answer. Do NOT use for quick one-line definitions,
  for interactive tutoring/quizzing (that's a learning-conversation, not an artifact),
  or when the user only wants code written.
---

# Illustrated Explainer

把一個使用者想學的主題（演算法 / 框架 / 技術 / 系統 / 論文），變成一篇**圖文並茂、自成一檔的深度科普文章**（單一 `.html`，繁體中文）。目標讀者體驗像知乎精選、distill.pub、Lilian Weng blog 那種——先給直覺，再上數學與圖解，配實例、程式碼、結果、出處。

輸出是**一個本機 `.html` 檔**：CDN 載 KaTeX（公式）與 highlight.js（程式碼），所有圖以 base64 內嵌，所以整檔可攜、雙擊就能看。

## 核心理念

一篇好的深度介紹**不是把 wikipedia 抄一遍**，而是帶讀者走一條「為什麼→是什麼→怎麼運作→有多好→跟別人比」的理解路徑。三個支柱：

1. **直覺先於形式**。每個數學式子出現前，先用比喻或圖講清楚它在幹嘛。讀者要先「有感覺」，公式才是把感覺精確化。
2. **圖扛重點**。骨幹是概念圖 / 流程圖 / 架構圖。抽象的東西一定配一張「看了就懂」的示意圖。文字解釋不了的，畫出來。
3. **有出處、可信任**。基於真實來源（原始論文、官方文件），引用給連結，不確定就標明，不硬掰。

## 工作流程

### 1. 釐清要做什麼（必要時問一句）
判斷主題類型（演算法 / 框架 / 技術 / 論文）與**深度/讀者**。多數情況直接做即可，但若主題很發散（例如「介紹深度學習」這種大到不像一篇文章）或深度不明，用一個問題確認範圍與假設的先備知識，別問一串。

### 2. 研究（先讀 `references/research-and-sources.md`）
**不要憑記憶寫。** 先 WebSearch 找正典來源，論文優先抓 arXiv 的 HTML 版（`ar5iv.org/abs/<id>`），框架優先官方文件。挖出：解決什麼問題、核心洞見、關鍵公式/機制、實驗結果、侷限、時間軸。至少交叉 2 個來源。

**這一步就要把原圖找出來並下載。** 從論文/教學頁面挑出 2-4 張招牌圖（架構圖、機制示意、代表性結果圖——那種「看過就記得」的圖），記下圖片 URL 並下載到輸出資料夾。這些原圖是文章的核心素材，預期會直接嵌入（配標來源），別漏做。細節見該 reference。

### 3. 規劃文章骨架
用下面的「文章結構」排出這篇的章節與每章要放什麼圖。先想清楚**這篇的招牌圖是哪 2-3 張**（讀者靠它們理解），再動手。

### 4. 產圖（先讀 `references/research-and-sources.md` 的「圖從哪來」）
四種來源**都要用到**，全部走 `scripts/fig_to_datauri.py` 這條管線內嵌：
- **原圖（預設就放，別跳過）**：把步驟 2 抓下來的 2-4 張招牌圖嵌進文章，`figcaption` 用 `--src` 標來源。這是知乎/distill 那種文章的靈魂——讀者常靠「我看過那張圖」認得主題。**一篇文章若一張原圖都沒有，通常是漏做了。** 只有當原圖太雜、重畫更清楚，或想要跟著主題變色時，才改用自己畫的版本（可與原圖並存）。
- **概念圖 / 流程圖 / 架構圖**：你自己的加值，補原圖沒講清楚的。手寫 **SVG**（直接進 HTML）或 Mermaid，用 template 的 CSS 變數著色跟著明暗主題。
- **資料圖表**：跑 matplotlib，`fig_to_datauri(plt.gcf())` 轉 URI。中文字型與深色相容見 reference。
- **AI 封面/插圖**：**選配、只裝飾**。偵測到圖片生成 key（x-coach 的 `.env LLM_API_KEY`）才用；沒有就跳過，用漸層/概念圖當頭圖。絕不用 AI 生圖畫技術圖。

### 5. 組裝 HTML
複製 `assets/template.html`，逐一填 `{{PLACEHOLDER}}`。公式寫 `\( \)` / `$$ $$`（KaTeX 自動 render），程式碼用 `<pre><code class="language-python">`（highlight.js 自動上色）。善用 template 提供的元件：`.tldr`、`.callout`（tip/key/warn）、`figure` + `figcaption`、`.table-scroll`、`nav.toc`。輸出檔名用主題的英文/拼音 slug，例如 `transformer-explained.html`，寫到使用者指定處或當前目錄。

### 6. 驗證
在瀏覽器打開產出的 `.html`（Browser pane），確認：公式有 render（沒有出現生 LaTeX）、程式碼有上色、圖都顯示（沒破圖）、明暗主題都正常、手機寬度不爆版。有問題就修 source 再看。最後跟使用者說檔案在哪、大概多長、放了哪些圖。

## 文章結構

這是深度科普文的預設骨架。**照這個順序，但依主題增減**——論文重「貢獻與實驗」，框架重「設計理念與怎麼用」，演算法重「機制與複雜度」。不是每節都要有，但「動機→直覺→機制→評價」這條主線要在。

```
標題 + kicker（分類，如「深度學習 · Transformer」）
一句話 TL;DR（.tldr）— 用一句白話講清楚這是什麼、為何重要
目錄（nav.toc）

## 為什麼需要它 / 問題背景
   沒有它之前大家怎麼做、痛點在哪。給讀者「動機」。

## 核心直覺
   一句話的關鍵洞見 + 一個好比喻 + 一張概念圖。這節最重要，讀者在這裡「懂」。

## 它怎麼運作（機制 / 數學）
   從直覺推進到形式。關鍵公式（KaTeX），每個式子先講白話再給式子。
   配圖解（示意圖 / 流程圖）。演算法就列步驟 + 流程圖。

## 具體例子 / 走一遍
   拿一個小的具體輸入，手把手走一遍流程。這節讓抽象變具體。

## 程式碼（最小實作）
   一段能抓住精髓的最小實作（不是整包 library）。20-50 行、有註解。

## 效果 / 實驗
   主要結果、跟誰比、贏在哪。可用 matplotlib 畫示意數據或複雜度比較。

## 優缺點 & 適用場景
   什麼時候該用、什麼時候不該用。誠實講侷限。

## 與其他方法的關係 / 延伸
   放進脈絡：前身是什麼、後續怎麼發展、旁邊有哪些替代。

## 參考資料
   真實來源 + 連結。
```

### 寫作風格
- **繁體中文**，科普但不淺薄。專有名詞第一次出現給中英對照，如「注意力機制（attention）」。
- 用「你」跟讀者對話，像在白板前講給一個聰明但沒背景的朋友聽。
- 段落有呼吸感，長解釋拆成幾段。關鍵結論用 `.callout.key`（重點）框起來，補充直覺用 `.callout.tip`，陷阱用 `.callout.warn`。
- 誠實：不確定標明，簡化的地方說「這裡略過細節」，別假裝全知。
- 長度隨主題深淺，但一篇完整介紹通常 1500-4000 字中文 + 3-6 張圖。寧可扎實不要注水。

## 打包元件速查

| 想要 | 怎麼做 |
|---|---|
| 公式 | 文中寫 `\( x^2 \)`（行內）或 `$$ \sum_i x_i $$`（獨立行），KaTeX 自動 render |
| 程式碼上色 | `<pre><code class="language-python">…</code></pre>` |
| 重點框 | `<div class="callout key"><span class="tag">重點</span><p>…</p></div>`（也有 `tip`/`warn`） |
| 圖 + 說明 | `scripts/fig_to_datauri.py fig.png --html --caption "圖 1：…" --src "作者 年份"`，或函式庫用 `figure_html(uri, caption=…)` |
| matplotlib 圖 | `from fig_to_datauri import fig_to_datauri, figure_html` → `figure_html(fig_to_datauri(plt.gcf()), caption=…)` |
| 手寫概念圖 | 直接寫 `<figure><svg …>…</svg><figcaption>…</figcaption></figure>`，著色用 `var(--accent)` 等 |
| 表格 | 包一層 `<div class="table-scroll"><table>…</table></div>`（手機可橫捲） |

參考檔：
- `references/research-and-sources.md` — 找來源（arXiv HTML 優先）、四種圖的來源與畫法、版權規則、FLUX recipe。
- `assets/template.html` — HTML 骨架，填 `{{PLACEHOLDER}}`。
- `scripts/fig_to_datauri.py` — 任何圖 → base64 data URI（CLI 或函式庫）。
