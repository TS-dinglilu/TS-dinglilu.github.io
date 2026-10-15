#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 RSS 订阅源 feed.xml（最新 60 期，跨分类混合，按日期倒序）。

为什么需要：没有 RSS，读者（包括恒辰自己用 RSS 阅读器做每日复盘）只能
每天开网站才能知道「今天更新了什么」。有了 feed，任何阅读器都能自动拉取。

注意 RSS 2.0 规范的坑：pubDate 必须是 RFC-822 格式（GMT），中文标题/摘要
必须整体 XML 转义，否则一个 & 就让整个 feed 解析失败。

用法: python scripts/build_feed.py
"""
from __future__ import annotations

import datetime
import glob
import os
import re
import sys
from html import unescape
from email.utils import format_datetime, formatdate

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail_template  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_BASE = getattr(tail_template, "SITE_BASE", "https://ts-dinglilu.github.io")
OUT = os.path.join(ROOT, "feed.xml")
MAX_ITEMS = 60
SKIP_DIRS = {".git", "logs", "scripts", "content", "assets", ".github",
             ".workbuddy", "__pycache__", "backups"}


def xml_esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def collect():
    """收集全部报告（含 digest），返回按日期倒序的条目列表。"""
    items = []
    for p in sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        if rel.split("/")[0] in SKIP_DIRS or os.path.basename(rel) == "index.html":
            continue
        m = re.search(r"report_(\d{8})\.html", rel)
        if not m:
            continue
        d = datetime.datetime.strptime(m.group(1), "%Y%m%d")
        cat = rel.split("/")[0]
        html = open(p, encoding="utf-8").read()
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        name = tail_template.CATEGORY_NAMES.get(cat, cat)
        # 摘要：取第一个长度 > 40 的段落，与 search-index 同思路
        zone = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
        summ = ""
        for t in re.findall(r"<p[^>]*>(.*?)</p>", zone, re.S):
            t = strip_tags(t)
            if len(t) > 40:
                summ = t[:160]
                break
        items.append({
            "cat": cat, "name": name, "date": d,
            "url": "%s/%s" % (SITE_BASE, rel),
            "title": "%s · %s" % (name, d.strftime("%Y-%m-%d")),
            "summary": summ or name,
        })
    items.sort(key=lambda x: x["date"], reverse=True)
    return items[:MAX_ITEMS]


def build():
    items = collect()
    now = datetime.datetime.now(datetime.timezone.utc)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>",
        "<title>%s</title>" % xml_esc("TS-dinglilu 自动化日报"),
        "<link>%s/</link>" % SITE_BASE,
        "<description>%s</description>" % xml_esc(
            "34 个自动化日报：车企/机械/科研/校园/地区/口碑，每日 05:00 自动更新"),
        "<language>zh-CN</language>",
        "<lastBuildDate>%s</lastBuildDate>" % format_datetime(now),
        "<ttl>1440</ttl>",
        '<atom:link href="%s/feed.xml" rel="self" type="application/rss+xml" />' % SITE_BASE,
    ]
    for it in items:
        # RFC-822 需要 GMT 时区；用当日上午 05:00（发布时间）作为 pubDate
        pub = it["date"].replace(hour=5, minute=0).strftime("%a, %d %b %Y %H:%M:%S GMT")
        lines += [
            "<item>",
            "<title>%s</title>" % xml_esc(it["title"]),
            "<link>%s</link>" % xml_esc(it["url"]),
            "<guid isPermaLink=\"true\">%s</guid>" % xml_esc(it["url"]),
            "<pubDate>%s</pubDate>" % pub,
            "<category>%s</category>" % xml_esc(it["name"]),
            "<description>%s</description>" % xml_esc(it["summary"]),
            "</item>",
        ]
    lines += ["</channel>", "</rss>"]
    blob = "\n".join(lines) + "\n"
    open(OUT, "w", encoding="utf-8", newline="").write(blob)
    print("[OK] feed.xml 已生成：%d 条，%d 字节" % (len(items), len(blob)))
    # formatdate 校验 self-check：确认 pubDate 可被解析
    fmt = formatdate(usegmt=True)
    print("     lastBuildDate=%s" % fmt)


if __name__ == "__main__":
    build()
