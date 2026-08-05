# -*- coding: utf-8 -*-
"""從每天的新聞「學習」新的美股→台股關聯,累積進 taiwan_map_learned.json。

用的是免費的 Gemini(和主分析同一把金鑰),所以這一步不用付費 API。
學到的關聯只是「候選」,信任度低於你手寫的 taiwan_map.py;
之後你可以用付費 Claude 複審、把好的升級成已驗證。
"""

import json
import os
from datetime import datetime, timezone, timedelta

from google import genai

LEARNED_PATH = "taiwan_map_learned.json"
MODEL = os.environ.get("GEMINI_LEARNED_MODEL") or "gemini-3.5-flash-lite"
FALLBACK_MODELS = [
    m.strip()
    for m in (
        os.environ.get("GEMINI_LEARNED_FALLBACK_MODELS")
        or "gemini-2.5-flash-lite,gemini-2.5-flash"
    ).split(",")
    if m.strip()
]

EXTRACT_PROMPT = """根據以下今天的美股新聞與漲跌個股,找出「美股標的 → 台股供應鏈 / 連動股」的關聯。
規則:
- 只輸出你有把握、且新聞內容合理支持的關聯。
- 台股請盡量附上代號(例如「台積電 2330」)。
- 不要輸出你不確定的、或純屬臆測的關聯。
- 嚴格「只」輸出 JSON,不要任何其他文字或說明。

輸出格式:
{{"linkages": [{{"us": "美股代號或主題", "tw": ["台股名稱 代號", ...], "reason": "一句話關聯理由"}}]}}

# 今日新聞
{news}

# 今日漲跌個股
{movers}
"""


def _today():
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d")


def load_learned():
    if os.path.exists(LEARNED_PATH):
        try:
            with open(LEARNED_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[warn] 讀取 learned map 失敗: {e}")
    return {}


def save_learned(data):
    with open(LEARNED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _clean_json(text):
    """Gemini 有時會用 ```json 包起來,清掉。"""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1] if "```" in t[3:] else t[3:]
        t = t.removeprefix("json").strip()
        t = t.rsplit("```", 1)[0].strip()
    return t


def _model_candidates():
    seen = set()
    candidates = []
    for model in [MODEL, *FALLBACK_MODELS]:
        if model not in seen:
            seen.add(model)
            candidates.append(model)
    return candidates


def propose_and_merge(api_key, news_text, movers_text):
    """呼叫 Gemini 抽關聯,合併進既有的 learned map,存檔並回傳。"""
    client = genai.Client(api_key=api_key)
    prompt = EXTRACT_PROMPT.format(news=news_text, movers=movers_text)
    parsed = None
    last_error = None
    for model in _model_candidates():
        try:
            print(f"使用 Gemini 學習模型: {model}")
            resp = client.models.generate_content(model=model, contents=prompt)
            parsed = json.loads(_clean_json(resp.text))
            break
        except Exception as e:
            last_error = e
            print(f"[warn] Gemini 學習模型 {model} 失敗,嘗試下一個: {e}")
    if parsed is None:
        print(f"[warn] 學習新關聯失敗,沿用既有: {last_error}")
        return load_learned()

    learned = load_learned()
    today = _today()
    for item in parsed.get("linkages", []):
        us = (item.get("us") or "").strip()
        tw = [s.strip() for s in item.get("tw", []) if s and s.strip()]
        if not us or not tw:
            continue
        entry = learned.get(us, {
            "stocks": [], "reason": item.get("reason", ""),
            "first_seen": today, "seen_count": 0, "status": "candidate",
        })
        entry["stocks"] = sorted(set(entry["stocks"]) | set(tw))
        entry["last_seen"] = today
        entry["seen_count"] = entry.get("seen_count", 0) + 1
        if item.get("reason"):
            entry["reason"] = item["reason"]
        learned[us] = entry

    save_learned(learned)
    return learned


def as_prompt_text(learned):
    """把 learned map 轉成餵給分析 LLM 的文字。已驗證的會標星號。"""
    if not learned:
        return "(尚無新聞學習到的關聯)"
    lines = []
    for us, e in learned.items():
        if e.get("status") == "trusted":
            tag = "★已驗證"
        else:
            tag = f"(候選,累計出現 {e.get('seen_count', 1)} 次)"
        lines.append(f"- {us} → {', '.join(e['stocks'])} {tag}")
    return "\n".join(lines)
