# -*- coding: utf-8 -*-
"""把每天產生的早報存進 briefs.json,當作控制台的歷史紀錄來源。"""

import json
import os

BRIEFS_PATH = "briefs.json"
MARKET_ANALYSIS_PATH = "market_analysis.json"
TAIWAN_ANALYSIS_PATH = "taiwan_analysis.json"
MAX_KEEP = 60  # 只保留最近 60 天


def _save_history(path, date, title, body):
    briefs = []
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                briefs = json.load(f)
        except Exception:
            briefs = []

    # 同一天重跑就覆蓋
    briefs = [b for b in briefs if b.get("date") != date]
    briefs.insert(0, {"date": date, "title": title, "body": body})
    briefs = briefs[:MAX_KEEP]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(briefs, f, ensure_ascii=False, indent=2)


def save_brief(date, title, body):
    _save_history(BRIEFS_PATH, date, title, body)


def save_market_analysis(date, title, body):
    _save_history(MARKET_ANALYSIS_PATH, date, title, body)


def save_taiwan_analysis(date, title, body):
    _save_history(TAIWAN_ANALYSIS_PATH, date, title, body)
