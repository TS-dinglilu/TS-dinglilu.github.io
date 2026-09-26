# -*- coding: utf-8 -*-
"""发布前的严格正文校验：篇幅 / 链接格式 / 文档标签 / giscus / 信息来源 / 标签配平。"""
import re
import sys

CATS = [
    "car-recruit", "mechanical-recruit", "school-news", "drone-research",
    "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
    "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
    "supply-chain-recruit", "research-institute", "future-planning",
    "xuzhou-news", "nanjing-news", "shanghai-news", "hangzhou-news",
    "jiangzhehu-news", "hefei-news", "anhui-news", "jiangsu-news",
    "shenzhen-news",
    "xuzhou-recruit", "nanjing-recruit", "shanghai-recruit",
    "hangzhou-recruit", "jiangzhehu-recruit", "hefei-recruit",
    "anhui-recruit", "jiangsu-recruit", "shenzhen-recruit",
]

# 地区类（地区现状 + 地区招聘）篇幅下限 8000，其余 12000
REGION_CATS = {"xuzhou", "nanjing", "shanghai", "hangzhou", "jiangzhehu",
               "hefei", "anhui", "jiangsu", "shenzhen"}

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
    # 分级下限：招聘/资讯类要求更厚（与自动化 prompt 的 12000–19000 一致），地区日报 8000 起
    lo = 8000 if cat.split("-")[0] in REGION_CATS else 12000
    if n < lo or n > 20000:
        issues.append("LEN=%d(下限%d)" % (n, lo))
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
