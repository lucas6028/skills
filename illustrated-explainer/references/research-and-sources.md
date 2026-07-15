# 找資料、找圖、版權

這份文件講「內容從哪來、圖從哪來、什麼能直接用什麼要重畫」。SKILL.md 的研究階段引到這裡。

## 找到權威來源（先做這件事）

不要憑記憶寫。先用 WebSearch 找到主題的**正典來源**，再用 WebFetch 讀它。優先序：

| 主題類型 | 先找什麼 |
|---|---|
| 研究論文 | arXiv 的 **HTML 版**（`ar5iv.org/abs/XXXX` 或 `arxiv.org/abs/XXXX` 的 HTML view）—— 有全文也有圖，比抓 PDF 容易。找不到再找出版社頁面 / Semantic Scholar。 |
| 演算法 | 原始論文 + 一兩篇公認的好教學（distill.pub、Lilian Weng 的 blog、標準教科書章節） |
| 框架 / 函式庫 | **官方文件**優先（quickstart、architecture、design docs）；GitHub README；官方 blog 的發布文 |
| 技術 / 系統 | 原始設計論文（如 MapReduce、Raft）、官方 spec、RFC |

**為什麼 arXiv HTML 而不是 PDF**：WebFetch 對 PDF 很不穩，Zhihu 之類的站會 403。arXiv 的 `ar5iv` HTML 版把公式、章節、圖都攤成乾淨的 HTML，好抓得多。抓論文時先試 `https://ar5iv.org/abs/<arxiv_id>`。

搜尋時實際要挖出來的東西：
- 這東西**解決什麼問題**（沒有它之前大家怎麼做、痛點在哪）
- **核心洞見**是什麼（一句話能講清楚的那個關鍵想法）
- **數學/機制**：關鍵公式、推導、演算法步驟
- **關鍵圖（一定要抓下來）**：論文/教學裡那 1-3 張「看了就懂」的招牌圖——架構圖、機制示意、代表性結果圖。**把它們的圖片 URL 記下來、下載下來**，這篇文章預期會直接嵌入這些原圖（配標來源）。這是文章的重點素材，不是可有可無。
- **實驗結果**：主要數字、比較對象
- **侷限與適用場景**
- **年份、作者、後續發展**（讓文章有時間軸感）

至少交叉看 2 個來源再下筆，避免單一來源的錯誤或偏見。不確定的地方在文中標「（此處為一般性理解，原文未明說）」，不要硬掰。

## 圖從哪來：四個來源，一條管線

四種來源，最後都要變成 `data:` URI 內嵌（`scripts/fig_to_datauri.py`），除了手寫 SVG 直接進 HTML。四種**都要用到**，尤其第 1 種（原圖）常常被漏掉——這是知乎/distill 那種文章的靈魂，一定要主動抓：

### 1. 現成 / 原始圖（預設就要用，別跳過）
論文那張招牌架構圖、官方文件的示意圖、經典教學（如 Illustrated Transformer）裡那張讓你秒懂的圖 —— **這些就是要嵌進文章的重點素材**。一篇好的深度介紹，讀者常常就是靠「啊我看過那張圖」認得這個主題。所以：

- **主動去抓**：研究階段就把 2-4 張招牌圖的 URL 記下來、下載、用 `fig_to_datauri.py` 內嵌。作法：從 arXiv HTML（ar5iv）頁面或教學文章找到 `<figure>/<img>` 的圖片 URL → 下載 → 內嵌。**如果一篇文章一張原圖都沒有，通常是漏做了這步。**
- **一定要標來源**：`figcaption` 用 `--src` 帶上 `來源：作者 年份`（或網站名 + 連結）。這是使用原圖的必要條件，也是學術科普的常規。
- **什麼時候改成重畫**：不是為了避開原圖，而是當(a)原圖太複雜、對這篇的重點來說雜訊多，重畫一張簡化版更清楚；或(b)你想要一張跟著明暗主題變色、跟敘事完全貼合的圖。這時才用第 2 種自己畫。原圖與重畫圖可以並存——原圖給「這是原作長相」，重畫圖給「這是我幫你抓的重點」。
- 別走另一個極端：整篇都在貼別人的圖、自己沒有任何加值敘事也不行。原圖是骨架素材，你的解說與概念圖把它們串成一條理解路徑。

### 2. 概念圖 / 流程圖 / 架構圖（骨幹，自己畫 SVG 或 Mermaid）
深度科普文的骨幹就是這些「看了就懂」的示意圖。免費、離線、無版權問題、還能完全配合你的敘事。

- **手寫 SVG**：直接寫進 HTML（不用 base64）。適合架構圖、資料流、幾何示意、注意力矩陣這種。手繪風 OK（微微不規則的線、手寫感字體），但要乾淨易讀。
- **Mermaid**：流程圖 / 序列圖 / 狀態機用 Mermaid 最快。若用 Mermaid，在 template 的 `<head>` 加 Mermaid CDN 並用 `<pre class="mermaid">`，或先在本機 render 成 SVG 再內嵌。手寫 SVG 可控性更高，優先手寫；圖多才用 Mermaid 省力。
- 用 template 的 CSS 變數（`var(--accent)` 等）著色，讓圖跟著明暗主題走。

### 3. 資料圖表（matplotlib，跑程式畫）
要畫函式曲線、示意數據、演算法收斂、複雜度比較、把抽象的東西可視化時用。

- 寫個小 script，`import matplotlib`，畫完用 `fig_to_datauri(plt.gcf())` 轉成 URI。
- 本機 python：`.venv\Scripts\python.exe`（若在 x-coach）或系統 python。matplotlib 沒裝就 `pip install matplotlib`。
- 中文標籤會缺字 → 設 `matplotlib.rcParams['font.sans-serif']=['Microsoft JhengHei','Noto Sans TC']` 與 `axes.unicode_minus=False`，或標籤直接用英文。
- 深色主題相容：圖用 `figure.bordered`（template 已有這個 class，給圖 Solarized 底色 `#fdf6e3` 加框，在明暗主題下都清楚）。
- **配色跟 Solarized 走**，讓圖表跟文章一致。用 Solarized 底色 `#fdf6e3`（`fig.savefig(..., facecolor="#fdf6e3")`）＋這組線色：blue `#268bd2`、cyan `#2aa198`、green `#859900`、yellow `#b58900`、orange `#cb4b16`、red `#dc322f`、magenta `#d33682`、violet `#6c71c4`。座標軸/文字用 base01 `#586e75`、格線用 base1 `#93a1a1`。手寫 SVG 概念圖照舊用 template 的 `var(--accent)` 等變數即可自動跟著主題。

### 4. AI 生成插圖（選配、裝飾用）
封面圖、章節分隔的情境插圖用。**不要**拿 AI 生圖來畫技術圖 —— FLUX 會生出漂亮但不準確的東西。技術正確性交給前三種。

- **這是選配路徑**（此 skill 全機器通用）。只有偵測到可用的圖片生成 key 才走。x-coach repo 有 `.env` 的 `LLM_API_KEY` 可打 NVIDIA FLUX（見下）；別的 repo 沒有就**直接跳過**，用純色/漸層封面或一張概念 SVG 當頭圖即可。不要因為生不出圖就卡住。
- 偵測：檢查 cwd 是否有 `.env` 且含 `LLM_API_KEY`。有才試。

**NVIDIA FLUX recipe（x-coach，2026 有效）**：
- Endpoint：`POST https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev`
- Payload：`{prompt, mode:"base", width:1024, height:1024, cfg_scale:3.5, steps:30, seed}`
- 回傳：`{"artifacts":[{"base64": ...}]}`
- **prompt 要短**（<600 字元，太長會 504）；504 是常態 → retry 迴圈（6 次、15s·n backoff）+ header `NVCF-POLL-SECONDS: 5`，202 時去 poll `api.nvcf.nvidia.com/v2/nvcf/pexec/status/{NVCF-REQID}`。
- 把 key 送到 ai.api.nvidia.com 這件事，auto-mode classifier 會擋 —— 新 session 要先問過使用者才送。
- 拿到 base64 直接組成 `data:image/png;base64,...` 塞進 `<figure>`。

## 版權與引用（硬規則）

- **嵌入原圖是預期行為，但每張都要標來源**（`figcaption` 的 `來源：作者 年份／網站 + 連結`）。在有明確引用的教育性科普文中嵌入少量招牌圖，是學術科普常規。
- 別走極端：不要整篇都在搬別人的圖而沒有自己的加值解說；也不要為了「保險」而一張原圖都不放（那會讓文章少了靈魂）。抓 2-4 張關鍵原圖 + 自己的概念圖與解說，是對的平衡。
- **文字不要逐字抄**。用自己的話重寫、重新組織，比原文短很多——這是文字的紅線，跟圖不一樣。公式可以照抄（公式無版權），但敘述要自己寫。
- 引用一定給連結，放文末「參考資料」，正文相關處也可帶上 inline 連結。
- 不要從多次回應拼湊還原整份受版權保護的內容。
