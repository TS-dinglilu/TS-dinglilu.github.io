#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理历史报告里「构建空白行累积」留下的多余空行（幂等）。

背景：build_report.py 拼接头部与正文时是 head_part + "\n" + body，而模板头部
本身带尾随空行，于是每重建一次就多一个空行——实测 company-reputation 重建 7 次
积了 7 个连续空行。2026-10-01 已在 normalize_head() 里修掉根因，
本脚本负责把历史积压的空行一次性收干净。

只压缩「连续 2 行及以上的空行」为 1 个空行，不动其它任何内容。

用法:
  python scripts/fix_blank_lines.py --check
  python scripts/fix_blank_lines.py
"""
import argparse
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NON_SITE = {"content", "logs", ".workbuddy", "scripts", ".git", "backups"}


def targets():
    out = []
    for d in sorted(glob.glob(os.path.join(ROOT, "*"))):
        if not os.path.isdir(d) or os.path.basename(d) in NON_SITE \
                or os.path.basename(d).startswith("."):
            continue
        out += glob.glob(os.path.join(d, "report_*.html"))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    n = 0
    total = 0
    for p in targets():
        s = open(p, encoding="utf-8").read()
        # 连续空行（含只有空格的）→ 单个空行
        new = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", s)
        if new != s:
            n += 1
            total += s.count("\n") - new.count("\n")
            if not args.check:
                open(p, "w", encoding="utf-8", newline="").write(new)
    print("%s：%d 份报告，共清理 %d 个空行"
          % ("待清理" if args.check else "已清理", n, total))


if __name__ == "__main__":
    main()
