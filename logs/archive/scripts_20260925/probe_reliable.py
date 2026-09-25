# -*- coding: utf-8 -*-
"""用可靠标记集定位每份报告的尾部起点，输出上下文供人工核对。"""
import glob
import os
import re

ROOT = r"D:/研二/github.auto/repo"
WIN = 9000

RELIABLE = [
    "<!-- 评论区 -->",
    "<!-- Giscus",
    "<!-- ===== Giscus",
    "<!-- ====== Giscus",
    "<!-- Section 7: Giscus",
    "<!-- Section 11",
    "<!-- ======== Section 8: Giscus",
    'class="giscus-section"',
    'class="comments-section"',
    'id="comments"',
    'id="section7"',
    'id="section11"',
    'id="sec11"',
    '<div class="footer"',
    'class="footer-info"',
    'class="report-footer"',
    "<footer",
]
CMT_RE = re.compile(r"<!--[^>]*(?:Giscus|giscus|评论区|Comments)[^>]*-->")

files = sorted(glob.glob(os.path.join(ROOT, "*", "report_*.html")))
nomatch = []
rows = []
for f in files:
    s = open(f, encoding="utf-8").read()
    rel = os.path.relpath(f, ROOT).replace("\\", "/")
    body = s.rfind("</body>")
    ws = max(0, body - WIN)
    win = s[ws:body]
    cands = []
    for mk in RELIABLE:
        i = win.find(mk)
        if i != -1:
            cands.append((i, mk))
    for m in CMT_RE.finditer(win):
        cands.append((m.start(), m.group(0)[:60]))
    if not cands:
        nomatch.append(rel)
        continue
    cands.sort()
    off, mk = cands[0]
    ctx = win[max(0, off - 45):off + 70].replace("\n", "\\n")
    rows.append((rel, mk, ctx))

print("=== 无可信标记（%d）===" % len(nomatch))
for r in nomatch:
    print("  ", r)
print("\n=== 明细（%d）===" % len(rows))
for rel, mk, ctx in rows:
    print("  %-46s [%s]" % (rel, mk))
    print("      %s" % ctx)
