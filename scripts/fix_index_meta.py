#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复「归档页 / 主页 / 404 / digest 页」的头部元信息，与 fix_meta.py 互补。

fix_meta.py 只管各分类的 report_*.html；本脚本管站点上其余页面：
  - <分类>/index.html  归档页（og:url 曾因复制母版全指向 traditional-auto/，且缺 canonical）
  - index.html         主页（缺 canonical）
  - 404.html           错误页（不该被收录，只需 noindex，跳过 og:url/canonical）
  - digest/*.html      周记月记年记（缺 description / og:url / canonical）

做法：以各页面自身的 <title> 与 description 为内容源，重建一份规范的
description + og:* + canonical 块，插在 </title> 之后。
幂等：重复运行不会叠加（先按标记剔除旧块）。

用法:
  python scripts/fix_index_meta.py --check      # 只报告不改
  python scripts/fix_index_meta.py              # 实际写入
"""
import argparse
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_BASE = "https://ts-dinglilu.github.io"
SITE_NAME = "TS-dinglilu 自动化日报"

CATEGORIES = ["car-recruit", "mechanical-recruit", "school-news", "drone-research",
              "ahut-campus", "byd-recruit", "chery-recruit", "chery-insider", "geely-recruit",
              "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
              "supply-chain-recruit", "research-institute", "future-planning",
              "xuzhou-news", "nanjing-news", "shanghai-news", "hangzhou-news",
              "jiangzhehu-news", "hefei-news", "anhui-news", "jiangsu-news",
              "shenzhen-news",
              "xuzhou-recruit", "nanjing-recruit", "shanghai-recruit",
              "hangzhou-recruit", "jiangzhehu-recruit", "hefei-recruit",
              "anhui-recruit", "jiangsu-recruit", "shenzhen-recruit",
              "company-reputation"]


def url_of(path):
    r = os.path.relpath(path, ROOT).replace("\\", "/")
    if r == "index.html":
        return SITE_BASE + "/"
    return "%s/%s/" % (SITE_BASE, r.split("/")[0])


def unescape(s):
    return (s.replace("&amp;", "&").replace("&lt;", "<")
             .replace("&gt;", ">").replace("&quot;", '"'))


def esc(s):
    return (s.replace("&", "&amp;").replace('"', "&quot;")
             .replace("<", "&lt;").replace(">", "&gt;"))


# 需要剔除的旧标签（含历史遗留的单行 og 标签）
STRIP = [
    r'\s*<meta\s+name="description"[^>]*>',
    r'\s*<meta\s+property="og:(?:type|site_name|title|description|url|locale|image)"[^>]*>',
    r'\s*<meta\s+name="twitter:(?:card|title|description)"[^>]*>',
    r'\s*<link\s+rel="canonical"[^>]*>',
]


def build_block(title, desc, url):
    return "\n".join([
        '<meta name="description" content="%s">' % esc(desc),
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="%s">' % SITE_NAME,
        '<meta property="og:title" content="%s">' % esc(title),
        '<meta property="og:description" content="%s">' % esc(desc),
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:locale" content="zh_CN">',
        '<meta name="twitter:card" content="summary">',
        '<meta name="twitter:title" content="%s">' % esc(title),
        '<meta name="twitter:description" content="%s">' % esc(desc),
        '<link rel="canonical" href="%s">' % url,
    ])


def page_title(s):
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    return unescape(m.group(1).strip()) if m else ""


def fix(path, dry=True):
    """返回 (changed, note)"""
    if not os.path.exists(path):
        return False, "文件不存在"
    s = open(path, encoding="utf-8").read()
    rel = os.path.relpath(path, ROOT).replace("\\", "/")

    if "</title>" not in s:
        return False, "无 </title>，跳过"

    title = page_title(s)
    if not title:
        return False, "无标题，跳过"

    # 404 页保持 noindex，不做 og/canonical（无索引价值）
    if rel.endswith("404.html"):
        return False, "404 页无需规范元信息"

    # 描述来源：优先复用页面已有的 og:description / description，否则用标题派生
    m = re.search(r'<meta property="og:description" content="([^"]*)"', s)
    if not m:
        m = re.search(r'<meta name="description" content="([^"]*)"', s)
    desc = unescape(m.group(1).strip()) if m else ""
    if not desc:
        desc = "%s —— %s，每日 05:00 自动更新。" % (title, SITE_NAME)

    url = url_of(path)
    head_end = s.find("</head>")
    head = s[:head_end] if head_end != -1 else s
    tail = s[head_end:] if head_end != -1 else ""

    # 幂等：先剔除所有旧元信息标签
    for pat in STRIP:
        head = re.sub(pat, "", head)

    # 归零判断：内容与目标一致就不写
    block = build_block(title, desc, url)
    cur_url = re.search(r'<meta property="og:url" content="([^"]*)"', s)
    cur_can = re.search(r'<link rel="canonical" href="([^"]*)"', s)
    ok = (cur_url and cur_url.group(1).rstrip("/") == url.rstrip("/")
          and cur_can and cur_can.group(1).rstrip("/") == url.rstrip("/"))
    if ok:
        return False, "已合规"

    tpos = head.rfind("</title>")
    head = head[:tpos + len("</title>")] + "\n" + block + head[tpos + len("</title>"):]

    if dry:
        return True, "待修复 → %s / %s" % (url, desc[:36])
    open(path, "w", encoding="utf-8", newline="").write(head + tail)
    return True, "已修复 → %s" % url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只报告，不写入")
    args = ap.parse_args()

    targets = [os.path.join(ROOT, "index.html"), os.path.join(ROOT, "404.html")]
    targets += [os.path.join(ROOT, c, "index.html") for c in CATEGORIES]
    targets += sorted(glob.glob(os.path.join(ROOT, "digest", "*.html")))

    n = 0
    for p in targets:
        changed, note = fix(p, dry=args.check)
        if changed:
            n += 1
        print("%-4s %-40s %s" % ("FIX" if changed else "OK", os.path.relpath(p, ROOT).replace("\\", "/"), note))
    print("\n%s: %d 个页面%s" % ("待修复" if args.check else "已修复", n,
                                "（--check 模式，未写入）" if args.check else ""))


if __name__ == "__main__":
    main()
