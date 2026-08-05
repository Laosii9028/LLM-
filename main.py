# -*- coding: utf-8 -*-
"""每日美股 Discord 早報 — 主流程。

流程:
  抓美股行情 + 新聞
  → (免費 Gemini) 從新聞學習新的美股→台股關聯,累積進 taiwan_map_learned.json
  → (免費 Gemini) 用「已驗證 + 候選」兩層對應表做分析
  → 推送到 Discord

本地測試: 先設好環境變數(見 .env.example),再執行 `python main.py`。
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


def get_env(name):
    val = os.environ.get(name)
    if not val:
        raise SystemExit(f"缺少環境變數: {name}(請參考 .env.example 設定)")
    return val


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

    # 先把資料整理成文字,學習步驟和分析步驟共用
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
        verified_map_text(),                 # 已驗證(手寫)
        learned.as_prompt_text(learned_map), # 候選(新聞學習)
    )
    body += "\n\n_本報告由程式自動彙整,僅供參考,非投資建議。_"

    print("存入歷史紀錄...")
    briefs.save_brief(tw_now.strftime("%Y-%m-%d"), title, body)

    print("推送到 Discord...")
    discord_notify.push(webhook, title, body)
    print("完成 ✅")


if __name__ == "__main__":
    main()
