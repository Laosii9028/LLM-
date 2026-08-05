# -*- coding: utf-8 -*-
"""每日美股 Discord 早報 — 主流程。

流程:
  抓美股行情 + 新聞
  → (免費 Gemini) 從新聞學習新的美股→台股關聯，累積進 taiwan_map_learned.json
  → (免費 Gemini) 用「已驗證 + 候選」兩層對應表做分析
  → 推送到 Discord

本地測試: 先設好環境變數(見 .env.example)，再執行 `python main.py`。
"""

import os
from datetime import datetime, timezone, timedelta

import market
import news
import analyze
import learned
import briefs
import discord_notify
from taiwan_map import as_prompt_text as verified_map_text


DEFAULT_DASHBOARD_URL = (
    "https://laosii9028.github.io/LLM-finance-agents/dashboard.html"
    "#repo=Laosii9028%2FLLM-finance-agents"
)


def get_env(name):
    val = os.environ.get(name)
    if not val:
        raise SystemExit(f"缺少環境變數: {name}(請參考 .env.example 設定)")
    return val


def dashboard_url(now):
    url = os.environ.get("DASHBOARD_URL", DEFAULT_DASHBOARD_URL).strip()
    if not url:
        return ""

    cache_buster = f"v={now.strftime('%Y%m%d%H%M')}"
    if "#" in url:
        url_without_hash, hash_part = url.split("#", 1)
        separator = "&" if "?" in url_without_hash else "?"
        return f"{url_without_hash}{separator}{cache_buster}#{hash_part}"

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{cache_buster}"


def main():
    av_key = get_env("ALPHA_VANTAGE_API_KEY")
    gemini_key = get_env("GEMINI_API_KEY")
    webhook = get_env("DISCORD_WEBHOOK_URL")

    tw_now = datetime.now(timezone.utc) + timedelta(hours=8)  # 台灣時間 UTC+8
    title = f"📈 美股早報 {tw_now.strftime('%Y/%m/%d')}"

    print("抓取美股指數...")
    indices = market.fetch_indices()

    print("抓取漲跌榜...")
    movers = market.fetch_gainers_losers(av_key)

    print("抓取重點美股追蹤名單...")
    watchlist = market.fetch_watchlist()

    print("抓取新聞...")
    articles = news.fetch_news(av_key)

    news_text = analyze.fmt_news(articles)
    gainers_text = analyze.fmt_movers(movers["gainers"])
    losers_text = analyze.fmt_movers(movers["losers"])
    watchlist_text = analyze.fmt_watchlist(watchlist)
    movers_text = (
        f"重點追蹤美股:\n{watchlist_text}\n\n"
        f"漲幅最大:\n{gainers_text}\n\n"
        f"跌幅最大:\n{losers_text}"
    )

    print("從新聞學習新的台股連動關聯...")
    learned_map = learned.propose_and_merge(gemini_key, news_text, movers_text)

    print("Gemini 分析中...")
    body = analyze.build_analysis(
        gemini_key,
        analyze.fmt_indices(indices),
        watchlist_text,
        gainers_text,
        losers_text,
        news_text,
        verified_map_text(),
        learned.as_prompt_text(learned_map),
    )
    body += "\n\n_本報告由程式自動彙整，僅供參考，非投資建議。_"

    print("Gemini 美股動蕩分析中...")
    market_analysis_body = analyze.build_us_market_analysis(
        gemini_key,
        analyze.fmt_indices(indices),
        watchlist_text,
        gainers_text,
        losers_text,
        news_text,
    )
    market_analysis_body += "\n\n_本分析用於整理市場線索與觀察方向，僅供參考，非投資建議。_"

    print("Gemini 台股分析中...")
    taiwan_analysis_body = analyze.build_taiwan_market_analysis(
        gemini_key,
        analyze.fmt_indices(indices),
        watchlist_text,
        gainers_text,
        losers_text,
        news_text,
        verified_map_text(),
        learned.as_prompt_text(learned_map),
    )
    taiwan_analysis_body += "\n\n_本分析用於整理台股連動線索與觀察方向，僅供參考，非投資建議。_"

    print("存入歷史紀錄...")
    briefs.save_brief(tw_now.strftime("%Y-%m-%d"), title, body)
    briefs.save_market_analysis(
        tw_now.strftime("%Y-%m-%d"),
        f"🔎 美股分析 {tw_now.strftime('%Y/%m/%d')}",
        market_analysis_body,
    )
    briefs.save_taiwan_analysis(
        tw_now.strftime("%Y-%m-%d"),
        f"🇹🇼 台股分析 {tw_now.strftime('%Y/%m/%d')}",
        taiwan_analysis_body,
    )

    print("推送到 Discord...")
    discord_notify.push(webhook, title, body, dashboard_url=dashboard_url(tw_now))
    print("完成 ✅")


if __name__ == "__main__":
    main()
