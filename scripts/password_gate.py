#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站密码守卫注入（幂等）：
- 守卫脚本 guard.js 放在仓库根（站点根路径 /guard.js）
- 本模块把 <script src="/guard.js" charset="utf-8"></script> 注入每个页面 <head> 开头
- build_report.py 构建新报告时也会调用，保证每日自动化生成的新报告自动带门
"""
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SNIPPET = '<script src="/guard.js" charset="utf-8"></script>'

# 只处理站点页面；content/ 是草稿、logs/ 是日志、.workbuddy 是记忆
SITE_DIRS = [
    "",  # 根目录（index.html）
    "car-recruit", "mechanical-recruit", "school-news", "drone-research",
    "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
    "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
    "supply-chain-recruit", "research-institute", "future-planning",
]


def inject(html):
    """往 <head> 的 <meta charset> 之后注入守卫脚本。返回 (html, 是否改动)。"""
    if "/guard.js" in html:
        return html, False
    m = html.find('<meta charset')
    if m == -1:
        i = html.find('<head>')
        if i == -1:
            return html, False
        j = i + len('<head>')
    else:
        j = html.find('>', m) + 1
    return html[:j] + "\n" + SNIPPET + html[j:], True


def inject_all(verbose=True):
    total = changed = 0
    for d in SITE_DIRS:
        pattern = os.path.join(ROOT, d, "*.html") if d else os.path.join(ROOT, "*.html")
        for p in sorted(glob.glob(pattern)):
            total += 1
            try:
                with open(p, encoding="utf-8") as f:
                    html = f.read()
            except UnicodeDecodeError:
                continue
            new, did = inject(html)
            if did:
                with open(p, "w", encoding="utf-8", newline="\n") as f:
                    f.write(new)
                changed += 1
    if verbose:
        print("[OK] 密码守卫注入: 共 %d 个页面, 本次注入 %d 个" % (total, changed))
    return total, changed


if __name__ == "__main__":
    inject_all()
