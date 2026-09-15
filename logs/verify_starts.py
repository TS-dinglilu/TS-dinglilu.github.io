# -*- coding: utf-8 -*-
"""打印每份报告尾部起点的上下文，人工核对是否误切正文。"""
import glob
import os
import sys

ROOT = r"D:/研二/github.auto/repo"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import unify_style as U  # noqa: E402

files = sorted(glob.glob(os.path.join(ROOT, "*", "report_*.html")))
for f in files:
    cat = os.path.basename(os.path.dirname(f))
    if cat not in U.NAMES:
        continue
    s = open(f, encoding="utf-8").read()
    b = s.rfind("</body>")
    ws = max(0, b - U.SEARCH_WINDOW)
    start = U.locate_start(s, ws, b)
    rel = os.path.relpath(f, ROOT).replace("\\", "/")
    if start is None:
        print("%-46s  *** 无起点 ***" % rel)
        continue
    seg = s[start:b]
    head = s[max(0, start - 70):start].replace("\n", "\\n")
    print("%-46s seg=%5d" % (rel, len(seg)))
    print("      起点前: %s" % head)
    print("      起点起: %s" % seg[:70].replace("\n", "\\n"))
