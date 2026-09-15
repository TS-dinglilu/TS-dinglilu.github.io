#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计：有多少报告的替换区间内包含「信息来源」板块（会被整段替换误删）。"""
import glob
import os
import re

ROOT = r"D:\研二\github.auto\repo"
CATEGORIES = ["car-recruit", "mechanical-recruit", "school-news", "drone-research",
              "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
              "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
              "research-institute", "future-planning"]
MARKERS = ["<!-- 评论区 -->", '<div class="comments-section', '<div style="max-width:860px',
           '<div class="giscus"', '<div class="footer"', "<footer", 'class="report-footer"',
           'class="footer-info"', "<!-- 报告页脚 -->", "<!-- ==================== 报告尾部",
           "<!-- Giscus 评论区 -->", 'class="back-link" style="margin-top']
WINDOW = 9000

risky, safe = [], []
for c in CATEGORIES:
    for f in sorted(glob.glob(os.path.join(ROOT, c, "report_*.html"))):
        s = open(f, encoding="utf-8").read()
        be = s.rfind("</body>")
        ws = max(0, be - WINDOW)
        win = s[ws:be]
        pos = None
        for mk in MARKERS:
            i = win.find(mk)
            if i != -1 and (pos is None or i < pos):
                pos = i
        if pos is None:
            continue
        seg = s[ws + pos:be]
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        nlinks = len(re.findall(r'href="https?://', seg))
        hit = []
        if nlinks > 3:
            hit.append("外链%d条" % nlinks)
        if "<table" in seg:
            hit.append("table")
        if re.search(r"<ol", seg):
            hit.append("ol列表")
        if 'class="sources"' in seg:
            hit.append("sources块")
        if hit:
            risky.append((rel, len(seg), ",".join(hit)))
        else:
            safe.append(rel)

print("安全（可整段替换）: %d 份" % len(safe))
print("有风险（区间含来源/正文特征）: %d 份\n" % len(risky))
for rel, n, hit in risky:
    print("  %-48s 区间%5d 字符  含: %s" % (rel, n, hit))
