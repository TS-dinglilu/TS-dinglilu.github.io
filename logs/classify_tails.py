#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计全站报告的结尾结构类型，确定视觉统一改造的范围。"""
import glob
import os
import re
from collections import Counter, defaultdict

ROOT = r"D:\研二\github.auto\repo"
CATEGORIES = ["car-recruit", "mechanical-recruit", "school-news", "drone-research",
              "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
              "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
              "research-institute", "future-planning"]

reports = []
for c in CATEGORIES:
    reports += sorted(glob.glob(os.path.join(ROOT, c, "report_*.html")))


def classify(s):
    # 评论区形态
    if "giscus.app" not in s:
        comment = "无评论区"
    elif 'style="max-width:860px' in s:
        comment = "A·内联style卡片"
    elif 'class="comments-section' in s:
        comment = "B·comments-section"
    elif 'class="giscus"' in s:
        comment = "C·裸giscus容器"
    else:
        comment = "D·其他"
    # 页脚形态
    if re.search(r"<footer[^>]*class=\"footer\"", s):
        footer = "1·<footer class=footer>"
    elif re.search(r"<div[^>]*class=\"footer\"", s):
        footer = "2·<div class=footer>"
    elif "<footer" in s:
        footer = "3·<footer>无class"
    elif "class=\"footer" in s:
        footer = "4·其他class"
    else:
        footer = "5·无页脚"
    # scroll-top
    scroll = "有" if 'class="scroll-top"' in s else "无"
    # giscus 挂载方式
    if "giscusScript" in s or "appendChild(giscusScript)" in s:
        giscus_js = "动态JS挂载"
    elif re.search(r'<script[^>]*src="https://giscus\.app/client\.js"', s):
        giscus_js = "内联script标签"
    else:
        giscus_js = "无"
    return comment, footer, scroll, giscus_js


cnt = defaultdict(Counter)
detail = defaultdict(list)
for f in reports:
    rel = os.path.relpath(f, ROOT).replace("\\", "/")
    s = open(f, encoding="utf-8").read()
    c, ft, sc, gj = classify(s)
    cnt["评论区"][c] += 1
    cnt["页脚"][ft] += 1
    cnt["返回顶部"][sc] += 1
    cnt["giscus挂载"][gj] += 1
    detail[(c, ft, sc, gj)].append(rel)

print("报告总数: %d\n" % len(reports))
for k in ("评论区", "页脚", "返回顶部", "giscus挂载"):
    print("### %s" % k)
    for v, n in cnt[k].most_common():
        print("   %-24s %3d" % (v, n))
    print()

print("### 组合分布（按数量排序，前 12）")
for combo, files in sorted(detail.items(), key=lambda x: -len(x[1]))[:12]:
    print("   %-58s %3d 份" % (" | ".join(combo), len(files)))
    print("        例: %s" % ", ".join(files[:3]))
