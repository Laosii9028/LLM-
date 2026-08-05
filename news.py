# -*- coding: utf-8 -*-
"""抓美股新聞:用 Alpha Vantage NEWS_SENTIMENT，附帶每則新聞的情緒標籤。"""

import requests


def fetch_news(api_key, limit=15):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "topics": "financial_markets,economy_macro,technology",
        "sort": "LATEST",
        "limit": str(limit),
        "apikey": api_key,
    }
    try:
        data = requests.get(url, params=params, timeout=30).json()
        feed = data.get("feed", [])
        items = []
        for a in feed[:limit]:
            tickers = [t.get("ticker") for t in a.get("ticker_sentiment", [])[:5]]
            items.append({
                "title": a.get("title", ""),
                "summary": a.get("summary", "")[:280],
                "source": a.get("source", ""),
                "sentiment": a.get("overall_sentiment_label", ""),
                "tickers": tickers,
            })
        return items
    except Exception as e:
        print(f"[warn] 新聞抓取失敗: {e}")
        return []
