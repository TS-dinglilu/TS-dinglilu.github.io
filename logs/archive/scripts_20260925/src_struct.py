#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看 13 份风险文件中「信息来源」板块的结构形态。"""
import os

ROOT = r"D:\研二\github.auto\repo"
FILES = [
    "car-recruit/report_20260725.html", "car-recruit/report_20260803.html",
    "car-recruit/report_20260804.html", "car-recruit/report_20260805.html",
    "car-recruit/report_20260807.html", "mechanical-recruit/report_20260805.html",
    "school-news/report_20260725.html", "byd-recruit/report_20260728.html",
    "byd-recruit/report_20260803.html", "byd-recruit/report_20260804.html",
    "byd-recruit/report_20260805.html", "byd-recruit/report_20260806.html",
    "byd-recruit/report_20260807.html",
]
MARKERS = ["<!-- 评论区 -->", '<div class="comments-section', '<div style="max-width:860px',
           '<div class="giscus"', '<div class="footer"', "<footer", 'class="report-footer"',
           'class="footer-info"', "<!-- 报告页脚 -->", "<!-- ==================== 报告尾部",
           "<!-- Giscus 评论区 -->", 'class="back-link" style="margin-top']
WINDOW = 9000

for rel in FILES:
    s = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    be = s.rfind("</body>")
    ws = max(0, be - WINDOW)
    win = s[ws:be]
    pos = None
    for mk in MARKERS:
        i = win.find(mk)
        if i != -1 and (pos is None or i < pos):
            pos = i
    seg = s[ws + pos:be]
    k = seg.find("信息来源")
    print("\n" + "=" * 94)
    print("%s   区间起点标记后 %d 字符处出现「信息来源」" % (rel, k))
    print("-" * 94)
    if k >= 0:
        print("【前】..." + seg[max(0, k - 220):k].replace("\n", " ")[-220:])
        print("【后】" + seg[k:k + 200].replace("\n", " "))
    # 后续是否还有尾部标记
    after = seg[k:] if k >= 0 else ""
    for mk in ("<footer", 'class="footer"', 'class="back-link"', "scroll-top"):
        j = after.find(mk)
        if j != -1:
            print("   来源块之后还有: %s (距来源 +%d)" % (mk, j))
