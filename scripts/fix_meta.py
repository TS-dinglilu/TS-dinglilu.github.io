#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""历史报告元信息批量修复（description / og / canonical）。

背景：报告页从不同母版复制而来，造成三类历史问题——
  1. og:url 指向错误的分类（大量页面都指向 traditional-auto）；
  2. 缺 og / twitter 标签，分享到微信、微博、QQ 时没有预览卡；
  3. 部分页面完全没有 <meta name="description">。

本脚本把全部历史报告的 <head> 元信息重写为「按各自分类生成的唯一正确版本」，
真源与每日构建共用 tail_template.build_meta()，保证两者永不漂移。

用法：
  python scripts/fix_meta.py            # 修复全部分类的全部报告
  python scripts/fix_meta.py --check    # 只检查、不写盘（报告问题清单）
"""
import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail_template  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CATEGORIES = [c for c in tail_template.CATEGORY_NAMES]

META_PATTERNS = (
    r'<meta name="description"[^>]*>\s*',
    r'<meta property="og:[^"]*"[^>]*>\s*',
    r'<meta name="twitter:[^"]*"[^>]*>\s*',
    r'<link rel="canonical"[^>]*>\s*',
)


def fix_head(html, category):
    """返回 (新 html, 是否改动)。"""
    changed = False

    # 0) 修复「缺 </head>」的结构性问题：geely-recruit 的历史报告从 </style>
    #    直接跳到 <body>，</head> 丢失。浏览器能容忍，但会让后续定位失败。
    if "</head>" not in html:
        se = html.find("</style>")
        b = html.find("<body")
        if 0 < se < b:
            html = html[:se + len("</style>")] + "\n</head>" + html[se + len("</style>"):]
            changed = True

    i, j = html.find("<head"), html.find("</head>")
    if i < 0 or j < 0:
        return html, changed
    head = html[i:j]
    orig = head

    for pat in META_PATTERNS:
        head = re.sub(pat, "", head, flags=re.S)

    # 日期从文件里的报告日期标题取（回退到 title 里的日期）
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", head)
    iso = m.group(0) if m else ""
    name = tail_template.CATEGORY_NAMES.get(category, category)
    block = tail_template.build_meta(category, name, iso)

    mt = re.search(r"</title>", head)
    if mt:
        head = head[:mt.end()] + "\n" + block + head[mt.end():]
    else:
        head = head.rstrip() + "\n" + block + "\n"

    if head != orig:
        changed = True
    return html[:i] + head + html[j:], changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只检查，不写盘")
    ap.add_argument("--category", help="只处理某个分类")
    args = ap.parse_args()

    cats = [args.category] if args.category else CATEGORIES
    total = changed = missing = 0
    bad_url = []
    for c in cats:
        d = os.path.join(ROOT, c)
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "report_*.html"))):
            total += 1
            html = open(f, encoding="utf-8").read()
            if 'og:url" content="%s/%s/"' % (tail_template.SITE_BASE, c) not in html:
                bad_url.append(f)
            if '<meta name="description"' not in html:
                missing += 1
            new, ch = fix_head(html, c)
            if ch:
                changed += 1
                if not args.check:
                    open(f, "w", encoding="utf-8").write(new)

    print("扫描报告: %d 份" % total)
    print("meta 需要修正: %d 份（og:url 错配 %d，缺 description %d）"
          % (changed, len(bad_url), missing))
    if args.check:
        for f in bad_url[:20]:
            print("  [URL ]", os.path.relpath(f, ROOT))
        if len(bad_url) > 20:
            print("  ... 其余 %d 份" % (len(bad_url) - 20))
    else:
        print("[OK] 已写盘修正")


if __name__ == "__main__":
    main()
