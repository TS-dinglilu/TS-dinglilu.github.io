#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把报告页里的巨型内联 CSS 抽成共享外部文件引用。

背景：390 份报告每份都内联了同一份 50,277 字符的 CSS（= 每份 49KB、全站约 19MB
纯重复）。浏览器对每份报告都要重新下载一遍，无法跨页缓存。

做法：只把「与 scripts/report_css_v9.css 完全相同」的那个 <style> 块替换为
<link rel="stylesheet" href="/assets/report.css">；**其余 <style> 块原样保留**
（部分页面有 2KB 的 custom overrides，如 .nav-toc / .summary-table，不能动）。

幂等：已经是 <link> 或没有匹配块的文件会被跳过。

用法：
  python scripts/extract_css.py           # 全部分类
  python scripts/extract_css.py --check   # 只统计
"""
import argparse
import glob
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail_template  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS_FILE = os.path.join(ROOT, "assets", "report.css")
LINK_TAG = '<link rel="stylesheet" href="/assets/report.css">'

STYLE_RE = re.compile(r'<style[^>]*>(.*?)</style>', re.S)


def target_hash():
    css = open(CSS_FILE, encoding="utf-8").read()
    return hashlib.md5(css.strip().encode()).hexdigest()


def process(html, want):
    """返回 (新 html, 替换了几块)。"""
    n = 0

    def repl(m):
        nonlocal n
        if hashlib.md5(m.group(1).strip().encode()).hexdigest() == want:
            n += 1
            return LINK_TAG if n == 1 else ""  # 理论上只有一个匹配块
        return m.group(0)

    return STYLE_RE.sub(repl, html), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    want = target_hash()
    files = sorted(glob.glob(os.path.join(ROOT, "*", "report_*.html")))
    files += sorted(glob.glob(os.path.join(ROOT, "*", "index.html")))

    changed = already = 0
    for f in files:
        rel = os.path.relpath(f, ROOT)
        if rel.split(os.sep)[0] in ("assets", "scripts", "content", "logs",
                                    ".workbuddy", "digest"):
            if rel.split(os.sep)[0] != "digest":
                continue
        html = open(f, encoding="utf-8").read()
        new, n = process(html, want)
        if n:
            changed += 1
            if not args.check:
                open(f, "w", encoding="utf-8").write(new)
        elif "/assets/report.css" in html:
            already += 1

    print("目标 CSS 指纹: %s" % want[:10])
    print("扫描文件: %d" % len(files))
    print("本轮抽离: %d 份；已是外链: %d 份" % (changed, already))
    if not args.check:
        print("[OK] 已写盘")


if __name__ == "__main__":
    main()
