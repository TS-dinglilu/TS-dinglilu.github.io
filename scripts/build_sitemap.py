#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 sitemap.xml（搜索引擎收录用）。

收录对象：主页、各分类归档页、各分类下全部报告页、digest 汇总页。
lastmod 取各文件自身的修改时间；报告页的 priority 略低于分类归档页。

用法：
  python scripts/build_sitemap.py
"""
import datetime
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail_template  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = tail_template.SITE_BASE
OUT = os.path.join(ROOT, "sitemap.xml")
SKIP_DIRS = {"assets", "scripts", "content", "logs", ".git", ".workbuddy", "__pycache__"}


def iso(path):
    ts = os.path.getmtime(path)
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def main():
    urls = []

    idx = os.path.join(ROOT, "index.html")
    if os.path.exists(idx):
        urls.append((BASE + "/", iso(idx), "1.0", "daily"))

    for d in sorted(os.listdir(ROOT)):
        full = os.path.join(ROOT, d)
        if not os.path.isdir(full) or d in SKIP_DIRS or d.startswith("."):
            continue
        d_idx = os.path.join(full, "index.html")
        if os.path.exists(d_idx):
            urls.append(("%s/%s/" % (BASE, d), iso(d_idx), "0.8", "daily"))
        for f in sorted(glob.glob(os.path.join(full, "*.html"))):
            name = os.path.basename(f)
            if name == "index.html":
                continue
            urls.append(("%s/%s/%s" % (BASE, d, name), iso(f), "0.5", "monthly"))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, prio, freq in urls:
        lines.append("  <url>")
        lines.append("    <loc>%s</loc>" % loc)
        lines.append("    <lastmod>%s</lastmod>" % lastmod)
        lines.append("    <changefreq>%s</changefreq>" % freq)
        lines.append("    <priority>%s</priority>" % prio)
        lines.append("  </url>")
    lines.append("</urlset>")

    open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("[OK] sitemap.xml 已生成：%d 条 URL" % len(urls))


if __name__ == "__main__":
    main()
