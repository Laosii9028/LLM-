# -*- coding: utf-8 -*-
"""把每天產生的早報存進 briefs.json,當作控制台的歷史紀錄來源。"""

import json
import os

BRIEFS_PATH = "briefs.json"
MAX_KEEP = 60  # 只保留最近 60 天


def save_brief(date, title, body):
    briefs = []
    if os.path.exists(BRIEFS_PATH):
        try:
            with open(BRIEFS_PATH, encoding="utf-8") as f:
                briefs = json.load(f)
        except Exception:
            briefs = []

    # 同一天重跑就覆蓋
    briefs = [b for b in briefs if b.get("date") != date]
    briefs.insert(0, {"date": date, "title": title, "body": body})
    briefs = briefs[:MAX_KEEP]

    with open(BRIEFS_PATH, "w", encoding="utf-8") as f:
        json.dump(briefs, f, ensure_ascii=False, indent=2)
