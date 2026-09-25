#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描所有报告与索引里指向 ts-dinglilu.github.io 下不存在路径的链接。"""
import glob
import os
import re
from collections import defaultdict

ROOT = r"D:\研二\github.auto\repo"
VALID = {"car-recruit", "mechanical-recruit", "school-news", "drone-research",
         "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
         "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
         "research-institute", "future-planning"}

bad = defaultdict(list)
files = glob.glob(os.path.join(ROOT, "*", "*.html")) + [os.path.join(ROOT, "index.html"),
                                                        os.path.join(ROOT, "homepage_index.html")]
for f in files:
    if not os.path.exists(f):
        continue
    rel = os.path.relpath(f, ROOT).replace("\\", "/")
    s = open(f, encoding="utf-8").read()
    for m in re.finditer(r"ts-dinglilu\.github\.io/([^\"'\s<>)]*)", s):
        path = m.group(1).strip("/")
        first = path.split("/")[0] if path else ""
        if first and first not in VALID and not first.endswith(".html") and first not in ("", "index.html"):
            bad[first].append(rel)

print("=== 指向不存在的一级路径 ===")
for k in sorted(bad, key=lambda x: -len(bad[x])):
    print("  %-30s 出现在 %d 个文件: %s" % (k, len(bad[k]), ", ".join(sorted(set(bad[k]))[:8])))

print()
print("=== 各错误写法总数 ===")
for k in bad:
    print("  %-30s %d 处" % (k, len(bad[k])))
