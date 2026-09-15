#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整性检查：所有 HTML 结尾闭合、div 平衡、评论区挂载正常。"""
import glob
import os
import re

ROOT = r"D:\研二\github.auto\repo"
files = sorted(set(glob.glob(os.path.join(ROOT, "*", "*.html")) + glob.glob(os.path.join(ROOT, "*.html"))))

bad = 0
for f in files:
    rel = os.path.relpath(f, ROOT).replace("\\", "/")
    s = open(f, encoding="utf-8").read()
    msgs = []
    if not s.rstrip().endswith("</html>"):
        msgs.append("结尾非 </html>: %r" % s.rstrip()[-40:])
    if s.count("<html") != 1:
        msgs.append("<html> 出现 %d 次" % s.count("<html"))
    if s.count("<body") != 1:
        msgs.append("<body> 出现 %d 次" % s.count("<body"))
    if s.count("</body>") != 1:
        msgs.append("</body> 出现 %d 次" % s.count("</body>"))
    o, c = s.count("<div"), s.count("</div>")
    if o != c:
        msgs.append("div 不平衡 %+d" % (o - c))
    if "giscus.app" not in s and "report_" in rel:
        msgs.append("无评论区")
    if msgs:
        bad += 1
        print("[!] %-52s %s" % (rel, "; ".join(msgs)))

print("\n检查 %d 个 HTML，%d 个有问题" % (len(files), bad))
