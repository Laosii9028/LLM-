# 美股每日早報 → Discord

每天台灣早上,自動把美股收盤動態、漲跌榜、新聞,加上「為什麼會這樣」的分析,
以及「可能影響哪些台股」的連動判斷,推送到你的 Discord 頻道。全程免費。

台股對應表會「自己長大」:每天從新聞學習新的美股→台股關聯,累積下來。

---

## 它每天會做什麼

1. 抓美股指數(S&P 500 / Nasdaq / 道瓊 / 費半 / VIX / 美債殖利率)
2. 固定抓重點美股追蹤名單(NVDA / AMD / AVGO / TSM / AAPL / TSLA / SMCI 等),並計算 1 日 / 5 日 / 20 日漲跌、量比、相對 Nasdaq/SOX 強弱
3. 抓當日漲幅最大 / 跌幅最大個股
4. 抓美股重要新聞(含情緒標籤)
5. **從新聞學習**新的「美股→台股」關聯,累積進 `taiwan_map_learned.json`
6. 用 Gemini 分析:美股為什麼漲跌、發生了什麼;若沒有公司專屬新聞,會用量價與族群強弱做保守推論
7. 另外產生「美股分析」:整理新聞、可能造成動蕩的來源、族群輪動與潛力觀察名單
8. 根據「已驗證 + 候選」兩層對應表,判斷可能受影響的台股與方向
9. 推送到 Discord

---

## 兩層對應表(重點觀念)

| 層 | 檔案 | 誰維護 | 信任度 |
|----|------|--------|--------|
| 已驗證 | `taiwan_map.py` | 你手寫 | 高,分析優先採用 |
| 候選 | `taiwan_map_learned.json` | 程式每天從新聞自動累積 | 低,標為候選、供參考 |

分析時兩層都會餵給 LLM,但明確告訴它「已驗證優先、候選需謹慎」。

### 你的付費 Claude 擺在哪?

**付費 Claude 訂閱(Pro/Max)不等於 API,不能接進這個自動排程。**
但它很適合當「人工複審員」:每隔一陣子,你打開 Claude(聊天,或你電腦上的 Claude Code,
兩者都在訂閱範圍內),把 `taiwan_map_learned.json` 貼給它,請它:

- 去掉明顯錯誤或臆測的關聯
- 合併重複的
- 把可靠、反覆出現的關聯,幫你搬進 `taiwan_map.py`(升級為已驗證)

這樣就用到了 Claude 的品質,又不用另外付 API 費。
(若之後想全自動、且指定用 Claude 而非 Gemini,才需要另外開通付費 API,
 對每週一次的維護來說花費很小。)

---

## 三個免費金鑰

| 用途 | 去哪拿 |
|------|--------|
| 美股行情 / 新聞 | Alpha Vantage — https://www.alphavantage.co/support/#api-key |
| LLM 分析 + 學習 | Google Gemini — https://aistudio.google.com/apikey |
| 推送 | Discord 頻道設定 → 整合 → Webhook → 建立 → 複製 URL |

### Gemini 模型選擇

預設模型已改成:

| 用途 | 預設模型 | 理由 |
|------|----------|------|
| 主早報分析 | `gemini-3.6-flash` | 較新的 Flash 主力模型,適合較完整的推理與中文整理 |
| 新關聯抽取 | `gemini-3.5-flash-lite` | 較快、配額較寬,適合把新聞轉成 JSON 候選關聯 |

若某個模型配額不足,程式會自動依序 fallback:

- 主早報分析: `gemini-3.6-flash` → `gemini-3.5-flash` → `gemini-2.5-flash`
- 新關聯抽取: `gemini-3.5-flash-lite` → `gemini-2.5-flash-lite` → `gemini-2.5-flash`

也可以在 GitHub Actions 的 **Variables** 設定:

```text
GEMINI_ANALYSIS_MODEL
GEMINI_LEARNED_MODEL
```

---

## 本地先跑一次試試

```bash
pip install -r requirements.txt

export ALPHA_VANTAGE_API_KEY=你的金鑰
export GEMINI_API_KEY=你的金鑰
export DISCORD_WEBHOOK_URL=你的webhook

python main.py
```

跑成功的話,Discord 會收到早報,`taiwan_map_learned.json` 也會多出今天學到的關聯。

---

## 設定每天自動跑(GitHub Actions,免費)

1. 把這整個資料夾推到一個 GitHub repo。
2. **Settings → Secrets and variables → Actions**,新增三個 secret:
   `ALPHA_VANTAGE_API_KEY`、`GEMINI_API_KEY`、`DISCORD_WEBHOOK_URL`。
3. 完成。`.github/workflows/daily.yml` 已設好台灣週二~週六早上 06:00 自動執行,
   並會把每天學到的對應表 commit 回 repo(所以 learned map 會持續累積)。
4. 想立刻測試:可用控制台的「一鍵直接觸發」,或到 **Actions** 分頁 → 選 workflow → **Run workflow** 手動觸發。

> workflow 已開 `contents: write` 權限,才能把 learned map 寫回 repo。

---

## 架成免費網頁(GitHub Pages)

1. 把這整個資料夾推到一個 GitHub repo。
2. 到 **Settings → Pages**。
3. Source 選 **Deploy from a branch**。
4. Branch 選 `main` / `/root`,儲存後等 GitHub Pages 發布。
5. 發布網址通常是 `https://你的帳號.github.io/repo名稱/`。

`index.html` 會自動導到 `dashboard.html`,所以打開 Pages 網址就是控制台。

---

## 手機 App 版(PWA)

這份控制台已附 `manifest.webmanifest`、`service-worker.js` 和 app icon。架到 GitHub Pages 後:

- iPhone: 用 Safari 開啟 Pages 網址 → 分享 → 加入主畫面。
- Android: 用 Chrome 開啟 Pages 網址 → 安裝應用程式 / 加入主畫面。

這是免費的 PWA,同一份網頁同時支援電腦與手機;不是 App Store / Google Play 上架的原生 App。

---

## 控制台(dashboard.html)

一個單一 HTML 檔的網頁控制台,直接用瀏覽器打開就能用,也能架到 GitHub Pages。三個分頁:

- **日報** — 看每天 / 歷史早報(資料來自 `briefs.json`)。
- **美股分析** — 看美國新聞、量價與族群輪動可能造成的美股動蕩,以及潛力觀察名單(資料來自 `market_analysis.json`)。
- **對應表** — 複審候選關聯,一鍵「升級」進已驗證表;也能刪除、手動新增。
  改完按「下載」把 `taiwan_map.json` / `taiwan_map_learned.json` 覆蓋回 repo 並 push。
- **觸發執行** — 直接呼叫 GitHub Actions API 一鍵跑一次,也保留開啟 Actions 頁和本機執行指令。

**載入資料兩種方式:**
1. 在上方輸入 `你的帳號/repo`(需為公開 repo),按「從 GitHub 載入」——會自動抓控制台需要的 JSON。
2. 或按「選本機 JSON 檔」,直接選你電腦上的 `taiwan_map.json`、`taiwan_map_learned.json`、`briefs.json`、`market_analysis.json`。

> 網頁上的修改只在瀏覽器內;**一定要下載檔案、覆蓋回 repo 並 push,變更才會生效。**
> 顏色用台股慣例:紅=漲、綠=跌。

### 一鍵直接觸發需要的 GitHub token

GitHub Pages 是靜態網頁,不能安全地內建私密金鑰。做法是你自己建立一個 fine-grained personal access token:

1. 到 GitHub **Settings → Developer settings → Personal access tokens → Fine-grained tokens**。
2. Repository access 只選這個 repo。
3. Repository permissions 只開 **Actions: Read and write**。
4. 建立後把 token 貼到控制台的「GitHub token」欄位。

勾「記住在此瀏覽器」時,token 只存在該瀏覽器的 `localStorage`;不要在共用電腦上勾選。

---

## 檔案結構

```
main.py                      # 主流程
market.py                    # 抓指數 + 重點追蹤美股量價訊號 + 漲跌榜
news.py                      # 抓新聞
learned.py                   # ★ 從新聞學習新關聯(免費 Gemini)
analyze.py                   # Gemini 分析(兩層對應表 + prompt)
briefs.py                    # 把每天早報存進 briefs.json
market_analysis.json         # 美股分析歷史(控制台的美股分析資料來源)
discord_notify.py            # Discord webhook 推送
taiwan_map.py                # 讀取已驗證對應表
taiwan_map.json              # ★ 已驗證對應表(手寫 / 從控制台升級)
taiwan_map_learned.json      # 候選對應表(程式自動累積)
briefs.json                  # 早報歷史(控制台的日報資料來源)
dashboard.html               # ★ 網頁控制台(瀏覽器開)
index.html                   # GitHub Pages 入口,自動導到 dashboard.html
manifest.webmanifest         # PWA 安裝資訊
service-worker.js            # PWA 快取外殼
icons/                       # PWA app icon
.github/workflows/daily.yml  # 每日排程 + 把上述 JSON commit 回 repo
```

---

## 之後可以升級的方向

- 想「追問」(例如「NVDA 為什麼跌更多?」)→ 把 webhook 換成 discord.py bot,加 slash command。
- 候選關聯累積多了 → 定期用 Claude 複審、升級進 `taiwan_map.py`。
- 想涵蓋盤中大事件 → 多加一個台灣午間排程,抓美股期貨與亞洲盤反應。

_本工具僅供個人研究參考,非投資建議。_
