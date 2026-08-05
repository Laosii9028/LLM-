# -*- coding: utf-8 -*-
"""用 Gemini 免費層產生每日早報。核心原則:只根據餵進去的真實數據,不讓它虛構。

台股連動用兩層對應表:
  - 已驗證(taiwan_map.py):你手寫,高信任。
  - 候選(taiwan_map_learned.json):從新聞學習來的,信任度較低,標為候選。
"""

import os

from google import genai

MODEL = os.environ.get("GEMINI_ANALYSIS_MODEL") or "gemini-3.6-flash"
FALLBACK_MODELS = [
    m.strip()
    for m in (
        os.environ.get("GEMINI_ANALYSIS_FALLBACK_MODELS")
        or "gemini-3.5-flash,gemini-2.5-flash"
    ).split(",")
    if m.strip()
]

PROMPT_TEMPLATE = """你是一位專業的美股與台股連動分析師。以下是今天美股收盤的「實際數據與新聞」。
請「只根據我提供的數據」撰寫一份給散戶看的每日早報,用繁體中文。
嚴格要求:不要虛構任何數字、公司或新聞;若某段資料為空,就說明資料不足,不要編。
可以使用量價資料、相對族群強弱、指數表現和新聞來推論原因;若不是新聞直接證實,請明確寫成「量價推論」或「族群推論」。

# 美股指數表現
{indices}

# 重點追蹤美股(台股供應鏈判斷優先參考)
{watchlist}

# 今日漲幅最大
{gainers}

# 今日跌幅最大
{losers}

# 今日重要新聞(含情緒標籤)
{news}

# 台股連動對應表 — 已驗證(高信任,優先採用)
{map_verified}

# 台股連動對應表 — 候選(從新聞學習來的,信任度較低,可參考但需謹慎)
{map_learned}

請依以下結構輸出,精簡、重點式,不要客套:

**一、今日美股怎麼了**
3-5 句話總結大盤方向與主要驅動因素(升息 / 財報 / 總經事件等)。

**二、重點美股為什麼漲跌**
優先從「重點追蹤美股」挑 4-6 檔和台股供應鏈最相關、或量價訊號最明顯的股票。
每檔用 1-2 句說明可能原因,綜合:
- 今日漲跌幅
- 5日 / 20日趨勢
- 成交量是否放大
- 相對 Nasdaq 或 SOX 是否強/弱
- 是否有新聞支持
若沒有公司專屬新聞,不要寫「無法判斷」就結束;請改用量價與族群資料做保守推論,並標明是推論。

**三、全市場異常個股**
從漲跌幅榜挑 2-4 檔最異常的,簡短說明;若資料不足,可只列為高波動個股。

**四、對台股的可能影響**
根據上面兩張對應表判斷,指出哪些台股可能受惠或受壓,標明方向(偏多 / 偏空)與理由。
請優先使用「重點追蹤美股」裡 NVDA、AMD、AVGO、TSM、AAPL、TSLA、SMCI、MU 等實際漲跌資料判斷台股供應鏈方向。
優先採用「已驗證」的關聯;若用到「候選」關聯,請註明信心較低。
明確註明:這是根據連動邏輯的推測,非投資建議。

**五、一句話總結**
今天早上你只需要知道的一件事。
"""

US_MARKET_ANALYSIS_PROMPT = """你是一位專業的美股市場策略分析師。以下是今天美股收盤後可用的「行情、量價訊號、漲跌榜與新聞」。
請用繁體中文寫一份「美股分析」,目標是幫使用者找出可能造成美股動蕩的事件、族群與潛在觀察股票。

重要規則:
- 只根據提供的資料分析,不要虛構新聞、財報或數字。
- 不要給買賣建議、目標價或保證式語氣。
- 可以用量價、相對強弱、族群輪動做推論,但要清楚標示「量價推論」或「族群推論」。
- 如果新聞和量價互相支持,請明確寫出「新聞 + 量價共振」。
- 這份分析是找觀察方向,不是投資建議。

# 美股指數表現
{indices}

# 重點追蹤美股量價訊號
{watchlist}

# 今日漲幅最大
{gainers}

# 今日跌幅最大
{losers}

# 今日重要新聞(含情緒標籤)
{news}

請依以下結構輸出:

**一、今日美股動蕩來源**
列 3-5 個可能造成市場波動的來源,例如利率、AI/半導體、科技巨頭、消費、電動車、避險情緒等。
每一點說明它是「新聞支持」、「量價推論」或「新聞 + 量價共振」。

**二、族群輪動與資金方向**
根據 Nasdaq、SOX、VIX、美債殖利率與重點股相對強弱,判斷資金較可能流向或流出的族群。

**三、潛力觀察名單**
列 5-8 檔美股觀察名單,優先從重點追蹤美股與異常漲跌榜挑選。
每檔格式:
- 代號: 觀察理由; 可能催化因素; 主要風險
只說「值得觀察的條件」,不要說應該買。

**四、明日/短線風險雷達**
列出接下來 1-3 個交易日需要注意的風險或確認訊號。

**五、一句話結論**
用一句話總結今天美股最值得追的主線。
"""


def fmt_indices(indices):
    if not indices:
        return "(無資料)"
    return "\n".join(
        f"- {x['name']}: 收 {x['close']}，{'+' if x['pct'] >= 0 else ''}{x['pct']}%"
        for x in indices
    )


def fmt_movers(movers):
    if not movers:
        return "(無資料)"
    return "\n".join(
        f"- {m.get('ticker', '?')}: 價 {m.get('price', '?')}，"
        f"漲跌 {m.get('change_percentage', '?')}"
        for m in movers
    )


def fmt_watchlist(stocks):
    if not stocks:
        return "(無資料)"
    return "\n".join(
        f"- {s['ticker']} ({s['name']}): 收 {s['close']}，"
        f"1日 {signed_pct(s.get('pct'))}，5日 {signed_pct(s.get('pct_5d'))}，"
        f"20日 {signed_pct(s.get('pct_20d'))}，量 {s['volume']:,}，"
        f"量比 {fmt_num(s.get('volume_ratio'))}x，"
        f"相對 {s.get('benchmark', '?')} {signed_pct(s.get('relative_pct'))}，"
        f"訊號: {', '.join(s.get('signals', []))}"
        for s in stocks
    )


def signed_pct(value):
    if value is None:
        return "無資料"
    return f"{'+' if value >= 0 else ''}{value}%"


def fmt_num(value):
    if value is None:
        return "無資料"
    return value


def fmt_news(news):
    if not news:
        return "(無資料)"
    out = []
    for n in news:
        tick = f" [{', '.join(t for t in n['tickers'] if t)}]" if n["tickers"] else ""
        out.append(f"- ({n['sentiment']}) {n['title']}{tick} — {n['source']}")
    return "\n".join(out)


def _model_candidates():
    seen = set()
    candidates = []
    for model in [MODEL, *FALLBACK_MODELS]:
        if model not in seen:
            seen.add(model)
            candidates.append(model)
    return candidates


def build_analysis(api_key, indices_text, watchlist_text, gainers_text, losers_text,
                   news_text, map_verified_text, map_learned_text):
    client = genai.Client(api_key=api_key)
    prompt = PROMPT_TEMPLATE.format(
        indices=indices_text,
        watchlist=watchlist_text,
        gainers=gainers_text,
        losers=losers_text,
        news=news_text,
        map_verified=map_verified_text,
        map_learned=map_learned_text,
    )
    last_error = None
    for model in _model_candidates():
        try:
            print(f"使用 Gemini 分析模型: {model}")
            resp = client.models.generate_content(model=model, contents=prompt)
            return resp.text
        except Exception as e:
            last_error = e
            print(f"[warn] Gemini 分析模型 {model} 失敗,嘗試下一個: {e}")
    raise last_error


def build_us_market_analysis(api_key, indices_text, watchlist_text, gainers_text, losers_text, news_text):
    client = genai.Client(api_key=api_key)
    prompt = US_MARKET_ANALYSIS_PROMPT.format(
        indices=indices_text,
        watchlist=watchlist_text,
        gainers=gainers_text,
        losers=losers_text,
        news=news_text,
    )
    last_error = None
    for model in _model_candidates():
        try:
            print(f"使用 Gemini 美股分析模型: {model}")
            resp = client.models.generate_content(model=model, contents=prompt)
            return resp.text
        except Exception as e:
            last_error = e
            print(f"[warn] Gemini 美股分析模型 {model} 失敗,嘗試下一個: {e}")
    raise last_error
