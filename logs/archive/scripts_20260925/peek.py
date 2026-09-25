#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""展示待修复文件的问题片段上下文，便于确定精确修复方式。"""
import os
import re

ROOT = r"D:\研二\github.auto\repo"

CASES = [
    ("car-recruit/report_20260725.html", "无 giscus + 错误域名 car-recruit-news"),
    ("car-recruit/report_20260727.html", "缺页脚 + 缺信息来源"),
    ("school-news/report_20260725.html", "无 giscus + 错误域名 school-news"),
    ("drone-research/report_20260807.html", "重复 body"),
]

for rel, why in CASES:
    f = os.path.join(ROOT, rel)
    s = open(f, encoding="utf-8").read()
    print("\n" + "=" * 78)
    print("### %s  —— %s" % (rel, why))
    print("=" * 78)
    lines = s.splitlines()
    print("总行数 %d，字符 %d" % (len(lines), len(s)))
    print("--- 尾部 18 行 ---")
    for ln in lines[-18:]:
        print("  | " + ln[:180])
    # 错误域名上下文
    for m in re.finditer(r"ts-dinglilu\.github\.io/[a-z\-]+-news/?[^\"'\s<]*", s):
        a = max(0, m.start() - 90)
        print("--- 域名片段 ---")
        print("  ..." + s[a:m.end() + 40].replace("\n", " "))
