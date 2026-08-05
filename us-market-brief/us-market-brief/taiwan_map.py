# -*- coding: utf-8 -*-
"""已驗證的美股 → 台股連動對應表。

實際內容存在 taiwan_map.json(方便控制台網頁讀寫)。
這裡只負責讀取,並轉成餵給分析 LLM 的文字。
"""

import json
import os

VERIFIED_PATH = "taiwan_map.json"


def load_map():
    if os.path.exists(VERIFIED_PATH):
        try:
            with open(VERIFIED_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[warn] 讀取 taiwan_map.json 失敗: {e}")
    return {}


def as_prompt_text():
    m = load_map()
    if not m:
        return "(尚無已驗證關聯)"
    lines = []
    for key, val in m.items():
        stocks = val.get("stocks", []) if isinstance(val, dict) else val
        lines.append(f"- {key} → {', '.join(stocks)}")
    return "\n".join(lines)
