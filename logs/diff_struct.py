#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比新老报告的结尾结构与 CSS 支持情况，为视觉统一改造提供依据。"""
import os
import re

ROOT = r"D:\研二\github.auto\repo"

SAMPLES = [
    ("老", "car-recruit/report_20260726.html"),
    ("老", "school-news/report_20260726.html"),
    ("老", "mechanical-recruit/report_20260804.html"),
    ("老", "drone-research/report_20260807.html"),
    ("新", "car-recruit/report_20260914.html"),
    ("新", "drone-research/report_20260914.html"),
]

CLASSES = [".giscus", ".comments-section", ".footer", ".scroll-top",
           ".back-link", "@media print", ".auto-updated"]

print("=" * 100)
print("CSS 支持情况（<style> 中是否出现该选择器）")
print("=" * 100)
print("%-42s %s" % ("文件", "  ".join("%-14s" % c for c in CLASSES)))
for tag, rel in SAMPLES:
    f = os.path.join(ROOT, rel)
    s = open(f, encoding="utf-8").read()
    styles = "".join(re.findall(r"<style[^>]*>(.*?)</style>", s, re.S))
    marks = []
    for c in CLASSES:
        marks.append("%-14s" % ("有" if c in styles else "—"))
    print("%-42s %s" % ("[%s] %s" % (tag, os.path.basename(os.path.dirname(f)) + "/" + os.path.basename(f)),
                        "  ".join(marks)))

print()
print("=" * 100)
print("结尾结构（从最后一个内容块到 </html>）")
print("=" * 100)
for tag, rel in SAMPLES:
    f = os.path.join(ROOT, rel)
    s = open(f, encoding="utf-8").read()
    lines = s.splitlines()
    # 从「评论区」或最后一个 </main>/footer 开始截取
    idx = None
    for i, l in enumerate(lines):
        if "评论区" in l or "giscus" in l.lower():
            idx = i
            break
    if idx is None:
        idx = max(0, len(lines) - 30)
    tail = [l for l in lines[idx:] if l.strip()]
    print("\n--- [%s] %s  (共 %d 行尾部) ---" % (tag, rel, len(tail)))
    for l in tail[:26]:
        print("   " + l.strip()[:170])
    if len(tail) > 26:
        print("   ... 另 %d 行" % (len(tail) - 26))
