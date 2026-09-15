#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断待修文件的真实结构特征。"""
import os
import re

ROOT = r"D:\研二\github.auto\repo"

TARGETS = {
    "缺信息来源": ["car-recruit/report_20260727.html", "car-recruit/report_20260728.html",
                   "mechanical-recruit/report_20260727.html", "mechanical-recruit/report_20260728.html",
                   "school-news/report_20260726.html", "school-news/report_20260727.html",
                   "school-news/report_20260728.html", "school-news/report_20260729.html",
                   "drone-research/report_20260726.html", "drone-research/report_20260727.html",
                   "drone-research/report_20260728.html"],
    "缺页脚": ["car-recruit/report_20260727.html", "mechanical-recruit/report_20260726.html",
               "mechanical-recruit/report_20260728.html", "mechanical-recruit/report_20260804.html",
               "mechanical-recruit/report_20260806.html", "school-news/report_20260805.html",
               "school-news/report_20260806.html", "ahut-campus/report_20260726.html",
               "ahut-campus/report_20260727.html", "ahut-campus/report_20260728.html",
               "byd-recruit/report_20260807.html", "geely-recruit/report_20260803.html",
               "xiaomi-recruit/report_20260727.html", "future-planning/report_20260806.html"],
    "无评论区": ["car-recruit/report_20260725.html", "school-news/report_20260725.html",
                 "drone-research/report_20260725.html"],
}

seen = set()
for kind, files in TARGETS.items():
    print("\n" + "#" * 78)
    print("# " + kind)
    print("#" * 78)
    for rel in files:
        if rel in seen:
            print("\n[%s] （已在其他组诊断过，跳过）" % rel)
            continue
        seen.add(rel)
        f = os.path.join(ROOT, rel)
        s = open(f, encoding="utf-8").read()
        print("\n--- %s (%d 字符) ---" % (rel, len(s)))
        print("  含 giscus.app: %s | 含 <footer: %s | 含 '信息来源': %s | 外链数: %d | cite 列表: %s"
              % ("是" if "giscus.app" in s else "否",
                 "是" if re.search(r"<footer|class=\"footer\"", s) else "否",
                 "是" if "信息来源" in s else "否",
                 len(re.findall(r'href="https?://', s)),
                 "有" if re.search(r'class="cite|id="cite-|<ol', s) else "无"))
        tail = [l for l in s.splitlines()[-16:] if l.strip()]
        print("  尾部非空行:")
        for l in tail[-7:]:
            print("    > " + l.strip()[:150])
