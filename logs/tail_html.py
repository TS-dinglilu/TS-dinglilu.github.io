#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取各报告 </style> 之后的真实尾部 HTML（排除 CSS 干扰）。"""
import os
import re

ROOT = r"D:\研二\github.auto\repo"
SAMPLES = [
    ("老", "car-recruit/report_20260726.html"),
    ("老", "school-news/report_20260726.html"),
    ("新", "car-recruit/report_20260914.html"),
    ("新", "drone-research/report_20260914.html"),
]

for tag, rel in SAMPLES:
    f = os.path.join(ROOT, rel)
    s = open(f, encoding="utf-8").read()
    last_style = s.rfind("</style>")
    tail = s[last_style + len("</style>"):] if last_style > 0 else s[-4000:]
    # 再往前找评论区起点，避免输出整个正文
    m = re.search(r'(<div[^>]*class="[^"]*comments-section|<div style="max-width:860px|<!--\s*评论区)', tail)
    if m:
        tail = tail[max(0, m.start() - 400):]
    lines = [l for l in tail.splitlines() if l.strip()]
    print("\n" + "=" * 96)
    print("[%s] %s   —— </style> 之后的尾部（%d 行）" % (tag, rel, len(lines)))
    print("=" * 96)
    for l in lines[:45]:
        print("  " + l.strip()[:190])
    if len(lines) > 45:
        print("  ... 另 %d 行" % (len(lines) - 45))
