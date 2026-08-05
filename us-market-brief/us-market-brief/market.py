# -*- coding: utf-8 -*-
"""抓美股行情:指數表現 + 重點追蹤股 + 當日漲跌幅最大個股。"""

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

SECTOR_BENCHMARK = {
    "NVDA": "^SOX",
    "AMD": "^SOX",
    "AVGO": "^SOX",
    "TSM": "^SOX",
    "ASML": "^SOX",
    "MU": "^SOX",
    "SMCI": "^SOX",
    "ARM": "^SOX",
    "QCOM": "^SOX",
    "AAPL": "^IXIC",
    "TSLA": "^IXIC",
    "MSFT": "^IXIC",
    "GOOGL": "^IXIC",
    "AMZN": "^IXIC",
    "META": "^IXIC",
}


def _pct_change(hist, days):
    if len(hist) <= days:
        return None
    last = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-1 - days])
    if not prev:
        return None
    return round((last - prev) / prev * 100, 2)


def _volume_ratio(hist):
    if "Volume" not in hist or len(hist) < 21:
        return None
    current = float(hist["Volume"].iloc[-1] or 0)
    avg = float(hist["Volume"].iloc[-21:-1].mean() or 0)
    if not avg:
        return None
    return round(current / avg, 2)


def _price_action_tags(pct_1d, pct_5d, pct_20d, volume_ratio, relative_pct):
    tags = []
    if pct_1d is not None:
        if pct_1d >= 3:
            tags.append("單日強漲")
        elif pct_1d <= -3:
            tags.append("單日重挫")
    if pct_5d is not None:
        if pct_5d >= 8:
            tags.append("短線動能強")
        elif pct_5d <= -8:
            tags.append("短線動能弱")
    if pct_20d is not None:
        if pct_20d >= 15:
            tags.append("月線趨勢強")
        elif pct_20d <= -15:
            tags.append("月線趨勢弱")
    if volume_ratio is not None:
        if volume_ratio >= 1.5:
            tags.append("量能放大")
        elif volume_ratio <= 0.7:
            tags.append("量能偏低")
    if relative_pct is not None:
        if relative_pct >= 1.5:
            tags.append("強於族群")
        elif relative_pct <= -1.5:
            tags.append("弱於族群")
    return tags or ["無明顯量價異常"]


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
    benchmark_cache = {}
    for symbol, name in WATCHLIST.items():
        try:
            hist = yf.Ticker(symbol).history(period="3mo")
            if len(hist) < 2:
                continue
            benchmark_symbol = SECTOR_BENCHMARK.get(symbol, "^IXIC")
            if benchmark_symbol not in benchmark_cache:
                benchmark_cache[benchmark_symbol] = yf.Ticker(benchmark_symbol).history(period="3mo")
            benchmark_hist = benchmark_cache[benchmark_symbol]
            last_row = hist.iloc[-1]
            last = float(last_row["Close"])
            pct_1d = _pct_change(hist, 1)
            pct_5d = _pct_change(hist, 5)
            pct_20d = _pct_change(hist, 20)
            volume_ratio = _volume_ratio(hist)
            benchmark_1d = _pct_change(benchmark_hist, 1)
            relative_pct = (
                round(pct_1d - benchmark_1d, 2)
                if pct_1d is not None and benchmark_1d is not None
                else None
            )
            results.append({
                "ticker": symbol,
                "name": name,
                "close": round(last, 2),
                "pct": pct_1d,
                "pct_5d": pct_5d,
                "pct_20d": pct_20d,
                "volume": int(last_row.get("Volume", 0) or 0),
                "volume_ratio": volume_ratio,
                "benchmark": benchmark_symbol,
                "benchmark_pct": benchmark_1d,
                "relative_pct": relative_pct,
                "signals": _price_action_tags(pct_1d, pct_5d, pct_20d, volume_ratio, relative_pct),
            })
        except Exception as e:
            print(f"[warn] 追蹤股 {symbol} 抓取失敗: {e}")
    return results
