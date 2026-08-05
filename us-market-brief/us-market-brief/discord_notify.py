# -*- coding: utf-8 -*-
"""把日報推送到 Discord。用 webhook,不需要架 bot。"""

import requests

MAX_DESC = 4000  # Discord embed description 上限約 4096，留點餘裕


def _split(text, size):
    """太長就依段落切成多則,避免超過 Discord 上限。"""
    chunks, cur = [], ""
    for para in text.split("\n"):
        if len(cur) + len(para) + 1 > size:
            chunks.append(cur)
            cur = para
        else:
            cur = f"{cur}\n{para}" if cur else para
    if cur:
        chunks.append(cur)
    return chunks or [text]


def push(webhook_url, title, body):
    for i, chunk in enumerate(_split(body, MAX_DESC)):
        embed = {
            "title": title if i == 0 else f"{title}(續 {i + 1})",
            "description": chunk,
            "color": 0x1D9E75,
        }
        r = requests.post(webhook_url, json={"embeds": [embed]}, timeout=30)
        r.raise_for_status()
