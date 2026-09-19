# -*- coding: utf-8 -*-
"""发布前的严格正文校验：篇幅 / 链接格式 / 文档标签 / giscus / 信息来源 / 标签配平。"""
import re
import sys

CATS = [
    "car-recruit", "mechanical-recruit", "school-news", "drone-research",
    "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
    "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
    "research-institute", "future-planning",
]

MD_LINK = re.compile(r"\]\(https?://")
DOC_TAG = re.compile(r"<!DOCTYPE|<html[\s>]|<head[\s>]|<body[\s>]", re.I)
INLINE_STYLE = re.compile(r"""\sstyle\s*=\s*["']""")
GISCUS = '<div class="giscus"></div>'

sys.stdout.reconfigure(encoding="utf-8")
bad = 0
for cat in CATS:
    path = "content/%s.html" % cat
    s = open(path, encoding="utf-8").read()
    n = len(s)
    issues = []
    if n < 8000 or n > 20000:
        issues.append("LEN=%d" % n)
    if MD_LINK.search(s):
        issues.append("MD-LINK")
    if DOC_TAG.search(s):
        issues.append("DOC-TAG")
    if INLINE_STYLE.search(s):
        issues.append("INLINE-STYLE")
    if 'class="giscus"' not in s:
        issues.append("NO-GISCUS")
    if "信息来源" not in s:
        issues.append("NO-SRC")
    if not s.rstrip().endswith(GISCUS):
        issues.append("GISCUS-NOT-LAST")
    if s.count("<div") != s.count("</div>"):
        issues.append("DIV=%d/%d" % (s.count("<div"), s.count("</div>")))
    if s.count("<a ") != s.count("</a>"):
        issues.append("A=%d/%d" % (s.count("<a "), s.count("</a>")))
    secs = len(re.findall(r"section-title", s))
    print(
        ("OK   " if not issues else "FAIL "),
        "%-20s %6d字 %3d链接 %d板块  %s"
        % (cat, n, s.count("source-link"), secs, " | ".join(issues)),
    )
    if issues:
        bad += 1

print("\n不合格文件数: %d" % bad)
sys.exit(1 if bad else 0)
