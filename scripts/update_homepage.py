#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主页更新器：把 13 个分类的最新日期 / 累计期数写回 index.html 卡片和统计区。

用法: python scripts/update_homepage.py
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORIES = ["car-recruit", "mechanical-recruit", "school-news", "drone-research",
              "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
              "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
              "research-institute", "future-planning"]

STATS_CSS = """/* === auto-updated (generated) === */
.auto-updated {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  color: var(--text-faint);
  letter-spacing: 0.02em;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px dashed var(--border);
}
.auto-updated b { color: var(--accent-green); font-weight: 600; }
"""


def scan_categories():
    info = {}
    for c in CATEGORIES:
        files = glob.glob(os.path.join(ROOT, c, "report_*.html"))
        if not files:
            info[c] = (None, 0)
            continue
        latest = max(re.search(r"report_(\d{8})", f).group(1) for f in files)
        iso = "%s-%s-%s" % (latest[:4], latest[4:6], latest[6:8])
        info[c] = (iso, len(files))
    return info


def main():
    idx_path = os.path.join(ROOT, "index.html")
    html = open(idx_path, encoding="utf-8").read()
    info = scan_categories()
    changed = 0

    # 1) 每张分类卡片: 插入/更新 "最新日期 · 累计期数"
    for cat, (iso, n) in info.items():
        href = 'href="https://ts-dinglilu.github.io/%s/"' % cat
        pos = html.find(href)
        if pos == -1:
            print("[WARN] 主页未找到分类卡片: " + cat)
            continue
        card_end = html.find("</a>", pos)
        card = html[pos:card_end]
        meta_pos = card.find('<div class="auto-meta">')
        if meta_pos == -1:
            print("[WARN] 卡片缺少 auto-meta: " + cat)
            continue
        if iso is None:
            line = '<div class="auto-updated">⚠️ 暂无报告</div>'
        else:
            short = iso[5:]
            line = '<div class="auto-updated">最新 <b>%s</b> · 累计 %d 期</div>' % (short, n)
        if '<div class="auto-updated">' in card:
            new_card = re.sub(r'<div class="auto-updated">.*?</div>', line, card, count=1, flags=re.S)
        else:
            new_card = card[:meta_pos] + line + "\n        " + card[meta_pos:]
        if new_card != card:
            html = html[:pos] + new_card + html[card_end:]
            changed += 1

    # 2) 统计区: 已生成日报总数
    total = sum(n for _, n in info.values())
    html = re.sub(r'(<div class="stat-num">)\d+\+(</div>\s*<div class="stat-label">已生成日报</div>)',
                  lambda m: m.group(1) + "%d+" % total + m.group(2), html, count=1)

    # 3) 注入 .auto-updated 样式（幂等）
    if ".auto-updated {" not in html:
        html = html.replace("</style>", STATS_CSS + "</style>", 1)

    open(idx_path, "w", encoding="utf-8").write(html)
    print("[OK] 主页已更新: %d 张卡片刷新, 报告总数 %d+" % (changed, total))


if __name__ == "__main__":
    sys.exit(main())
