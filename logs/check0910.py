#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
import os
import re
import sys

sys.path.insert(0, r"D:\研二\github.auto\repo\scripts")
import publish_all  # noqa

d = r"D:\研二\github.auto\content\backfill0910"
print("=== 0910 补做正文校验 ===")
for f in sorted(glob.glob(os.path.join(d, "*.html"))):
    s = open(f, encoding="utf-8").read()
    iss = publish_all.validate_content(f)
    stats = []
    for pat, lab in ((r"9月10|09-10|9/10", "9.10"), (r"9月9|09-09|9/9", "9.9"),
                     (r"9月11|09-11|9/11", "9.11")):
        stats.append("%s:%d" % (lab, len(re.findall(pat, s))))
    print("%-24s %6d 字符  %s  %s" % (
        os.path.basename(f), len(s), " ".join(stats),
        "OK" if not iss else "!! " + "; ".join(iss)))

print()
print("=== 抽查 car-recruit.html 前 25 行 ===")
print("\n".join(open(os.path.join(d, "car-recruit.html"), encoding="utf-8").read().splitlines()[:25]))
