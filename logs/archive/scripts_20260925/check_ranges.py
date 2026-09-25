#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查替换区间的起点上下文，确认没有把正文当尾部误删。"""
import os
import re

ROOT = r"D:\研二\github.auto\repo"
FILES = [
    "byd-recruit/report_20260803.html", "byd-recruit/report_20260804.html",
    "byd-recruit/report_20260805.html", "byd-recruit/report_20260806.html",
    "byd-recruit/report_20260807.html", "car-recruit/report_20260725.html",
    "car-recruit/report_20260803.html", "car-recruit/report_20260804.html",
    "car-recruit/report_20260805.html", "car-recruit/report_20260807.html",
    "weixiaoli-recruit/report_20260804.html",
]
MARKERS = ["<!-- 评论区 -->", '<div class="comments-section', '<div style="max-width:860px',
           '<div class="giscus"', '<div class="footer"', "<footer", 'class="report-footer"',
           'class="footer-info"', "<!-- 报告页脚 -->", "<!-- ==================== 报告尾部",
           "<!-- Giscus 评论区 -->", 'class="back-link" style="margin-top']
WINDOW = 9000

for rel in FILES:
    p = os.path.join(ROOT, rel)
    s = open(p, encoding="utf-8").read()
    be = s.rfind("</body>")
    ws = max(0, be - WINDOW)
    win = s[ws:be]
    pos, mk_used = None, None
    for mk in MARKERS:
        i = win.find(mk)
        if i != -1 and (pos is None or i < pos):
            pos, mk_used = i, mk
    start = ws + pos
    seg = s[start:be]
    print("\n" + "=" * 92)
    print("%s  区间 %d 字符，命中标记: %s" % (rel, len(seg), mk_used))
    print("-" * 92)
    print("起点前 120 字符: ...%s" % s[max(0, start - 120):start].replace("\n", " ")[-120:])
    print("区间前 160 字符: %s" % seg[:160].replace("\n", " "))
    # 区间里是否混入了正文特征
    warn = []
    for kw in ("section-title", "news-item", "card-title", "<h3", "板块"):
        if kw in seg:
            warn.append(kw)
    if warn:
        print("⚠️ 区间内出现正文特征: %s" % ", ".join(warn))
