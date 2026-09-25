#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精确审计 v2：以真实渲染需求为准，区分「真问题」与「历史风格差异」。"""
import glob
import os
import re
from collections import defaultdict

ROOT = r"D:\研二\github.auto\repo"
CATEGORIES = ["car-recruit", "mechanical-recruit", "school-news", "drone-research",
              "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
              "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
              "research-institute", "future-planning"]

P = defaultdict(list)


def note(k, w, m):
    P[k].append("%-52s %s" % (w, m))


reports = []
for c in CATEGORIES:
    reports += sorted(glob.glob(os.path.join(ROOT, c, "report_*.html")))

for f in reports:
    rel = os.path.relpath(f, ROOT).replace("\\", "/")
    s = open(f, encoding="utf-8").read()

    # 真实渲染要素
    if "giscus.app" not in s:
        note("未接评论区", rel, "全文无 giscus.app")
    if not re.search(r"<footer|class=\"footer\"", s):
        note("缺页脚", rel, "无 footer 元素")
    if "信息来源" not in s:
        note("缺信息来源", rel, "无『信息来源』字样")
    if not s.rstrip().endswith("</html>"):
        note("疑似截断", rel, "结尾=%r" % s.rstrip()[-50:])
    if re.search(r"<body[^>]*>\s*<body", s):
        note("重复body", rel, "存在重复 <body>")

    # 品牌/域名历史遗留
    if "TRAE Automation" in s or "TraeWork Automation" in s:
        note("旧品牌", rel, "残留 TRAE Automation")
    for m in re.finditer(r"ts-dinglilu\.github\.io/([a-z\-]+-news)/", s):
        note("错误域名", rel, "指向不存在的子路径 %s" % m.group(1))
    if "homepage_index.html" in s:
        note("指向废弃页", rel, "引用 homepage_index.html")

    # back-link 目标统计
    for m in re.finditer(r'href="([^"]+)"[^>]*>\s*🏠', s):
        note("返回链接", rel, m.group(1))

# 汇总
for k in sorted(P, key=lambda x: -len(P[x])):
    print("\n### %s（%d）" % (k, len(P[k])))
    for it in P[k][:200]:
        print("  " + it)
if not P:
    print("无问题")
