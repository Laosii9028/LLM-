# -*- coding: utf-8 -*-
"""抓美股行情:指數表現 + 當日漲跌幅最大個股。"""

import requests
import yfinance as yf

# 要追蹤的指數（yfinance 代號 → 顯示名稱）
INDICES = {
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq",
    "^DJI": "道瓊",
    "^SOX": "費城半導體 (SOX)",
    "^VIX": "VIX 恐慌指數",
    "^TNX": "美債 10 年殖利率",
}

WATCHLIST = {
    "NVDA": "NVIDIA",
    "AMD": "AMD",
    "AVGO": "Broadcom",
    "TSM": "台積電 ADR",
    "ASML": "ASML",
    "MU": "Micron",
    "SMCI": "Supermicro",
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "META": "Meta",
    "ARM": "Arm",
    "QCOM": "Qualcomm",
}


def fetch_indices():
    """回傳每個指數的收盤與當日漲跌幅。"""
    results = []
    for symbol, name in INDICES.items():
        try:
            hist = yf.Ticker(symbol).history(period="5d")
            if len(hist) < 2:
                continue
            last = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2])
            pct = (last - prev) / prev * 100
            results.append(
                {"name": name, "symbol": symbol,
                 "close": round(last, 2), "pct": round(pct, 2)}
            )
        except Exception as e:
            print(f"[warn] 指數 {symbol} 抓取失敗: {e}")
    return results


def fetch_gainers_losers(api_key, top_n=8):
    """
    用 Alpha Vantage TOP_GAINERS_LOSERS，一次呼叫就拿到
    當日漲幅最大 / 跌幅最大 / 最活躍。免費層每天約 25 次呼叫。
    """
    url = "https://www.alphavantage.co/query"
    params = {"function": "TOP_GAINERS_LOSERS", "apikey": api_key}
    try:
        data = requests.get(url, params=params, timeout=30).json()
        if "top_gainers" not in data:
            # 免費層額度用完或金鑰錯誤時，Alpha Vantage 會回一段說明文字
            print(f"[warn] Alpha Vantage 回應異常: {data}")
            return {"gainers": [], "losers": []}
        return {
            "gainers": data.get("top_gainers", [])[:top_n],
            "losers": data.get("top_losers", [])[:top_n],
        }
    except Exception as e:
        print(f"[warn] 漲跌榜抓取失敗: {e}")
        return {"gainers": [], "losers": []}


def fetch_watchlist():
    """固定追蹤台股連動常用的大型美股,避免只看到全市場漲跌榜的小型股。"""
    results = []
    for symbol, name in WATCHLIST.items():
        try:
            hist = yf.Ticker(symbol).history(period="5d")
            if len(hist) < 2:
                continue
            last_row = hist.iloc[-1]
            prev_row = hist.iloc[-2]
            last = float(last_row["Close"])
            prev = float(prev_row["Close"])
            pct = (last - prev) / prev * 100
            results.append({
                "ticker": symbol,
                "name": name,
                "close": round(last, 2),
                "pct": round(pct, 2),
                "volume": int(last_row.get("Volume", 0) or 0),
            })
        except Exception as e:
            print(f"[warn] 追蹤股 {symbol} 抓取失敗: {e}")
    return results
