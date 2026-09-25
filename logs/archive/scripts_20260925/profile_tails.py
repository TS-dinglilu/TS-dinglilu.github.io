# -*- coding: utf-8 -*-
"""梳理 193 份报告的旧尾部形态，辅助确定统一的尾部起始标记。"""
import glob
import os
import re
from collections import Counter

ROOT = r"D:/研二/github.auto/repo"
WIN = 9000

# 广义尾部相关标记（区分大小写不重要，这里用原文）
TOKENS = [
    "<!-- 评论区 -->",
    "<!-- Giscus",
    "<!-- Giscus评论区",
    "<!-- ===== Giscus",
    "<!-- Section 7: Giscus",
    "<!-- ======== Section 8: Giscus",
    "<!-- ===================== SECTION 10",
    "<!-- ==================== 板块",
    'class="giscus-section"',
    'id="comments"',
    'class="comments-section"',
    'class="report-footer"',
    'class="footer-info"',
    '<div class="footer"',
    "<footer",
    "<div class=\"comments-section\"",
    "评论区",
]

files = sorted(glob.glob(os.path.join(ROOT, "*", "report_*.html")))
shape = Counter()
rows = []
for f in files:
    s = open(f, encoding="utf-8").read()
    rel = os.path.relpath(f, ROOT).replace("\\", "/")
    body = s.rfind("</body>")
    ws = max(0, body - WIN)
    win = s[ws:body]
    hits = []
    for mk in TOKENS:
        i = win.find(mk)
        if i != -1:
            hits.append((i, mk))
    hits.sort()
    if not hits:
        rows.append((rel, None, None))
        continue
    off, mk = hits[0]
    ctx = win[max(0, off - 40):off + 60].replace("\n", "\\n")
    rows.append((rel, mk, ctx))

print("=== 无任何尾部标记的文件 ===")
for rel, mk, ctx in rows:
    if mk is None:
        print("  ", rel)
print("\n=== 最早命中标记分布 ===")
for rel, mk, ctx in rows:
    if mk:
        shape[mk] += 1
for k, v in shape.most_common():
    print("  %-45r %d" % (k, v))
print("\n=== 明细（最早标记 + 上下文）===")
for rel, mk, ctx in rows:
    if mk:
        print("  %-46s [%s] %s" % (rel, mk, ctx))
