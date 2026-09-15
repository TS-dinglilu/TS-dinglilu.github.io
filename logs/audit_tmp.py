#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站审计（只读）：结构完整性 / 链接有效性 / 索引与首页一致性。"""
import glob
import os
import re
import sys
from collections import defaultdict

ROOT = r"D:\研二\github.auto\repo"
CATEGORIES = ["car-recruit", "mechanical-recruit", "school-news", "drone-research",
              "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
              "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
              "research-institute", "future-planning"]

problems = defaultdict(list)


def note(kind, where, msg):
    problems[kind].append("%s :: %s" % (where, msg))


# ---------- 1) 报告结构完整性 ----------
all_reports = []
for c in CATEGORIES:
    all_reports += sorted(glob.glob(os.path.join(ROOT, c, "report_*.html")))
other = sorted(glob.glob(os.path.join(ROOT, "*", "report_*.html")))
extra = set(other) - set(all_reports)
for f in extra:
    note("游离报告", os.path.relpath(f, ROOT), "不在 13 分类名单内的 report 文件")

for f in all_reports:
    rel = os.path.relpath(f, ROOT).replace("\\", "/")
    s = open(f, encoding="utf-8").read()
    if not s.rstrip().endswith("</html>"):
        note("结构", rel, "结尾不是 </html>（可能被截断），结尾片段: %r" % s.rstrip()[-60:])
    if 'class="giscus"' not in s:
        note("结构", rel, "缺少 giscus 评论区容器")
    if "</footer>" not in s and "class=\"footer\"" not in s:
        note("结构", rel, "缺少 footer")
    if "返回首页" not in s and "back-link" not in s:
        note("结构", rel, "缺少返回首页链接")
    if "信息来源" not in s:
        note("结构", rel, "缺少信息来源板块")
    o, c_ = s.count("<div"), s.count("</div>")
    if o != c_:
        note("结构", rel, "div 不平衡: <div>=%d </div>=%d (差 %+d)" % (o, c_, o - c_))
    if "<main" in s and "</main>" not in s:
        note("结构", rel, "<main> 未闭合")
    # 返回首页链接目标
    for m in re.finditer(r'href="([^"]*)"[^>]*class="back-link"', s):
        note("链接", rel, "back-link 目标 %s" % m.group(1))
    for m in re.finditer(r'class="back-link"[^>]*href="([^"]*)"', s):
        note("链接", rel, "back-link 目标 %s" % m.group(1))

# ---------- 2) 内部链接有效性 ----------
for f in all_reports + [os.path.join(ROOT, "index.html")] + \
        [os.path.join(ROOT, c, "index.html") for c in CATEGORIES]:
    if not os.path.exists(f):
        continue
    rel = os.path.relpath(f, ROOT).replace("\\", "/")
    base = os.path.dirname(f)
    s = open(f, encoding="utf-8").read()
    for m in re.finditer(r'href="([^"#]+\.html)(?:#[^"]*)?"', s):
        href = m.group(1)
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        target = os.path.normpath(os.path.join(base, href))
        if not os.path.exists(target):
            note("死链", rel, "指向不存在的文件: %s" % href)

# ---------- 3) 分类索引 vs 磁盘 ----------
for c in CATEGORIES:
    idx = os.path.join(ROOT, c, "index.html")
    if not os.path.exists(idx):
        note("索引", c, "缺少 index.html")
        continue
    s = open(idx, encoding="utf-8").read()
    listed = set(re.findall(r'href="(report_\d{8}\.html)"', s))
    on_disk = set(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, c, "report_*.html")))
    miss = on_disk - listed
    ghost = listed - on_disk
    if miss:
        note("索引", c, "磁盘有但索引未列出 %d 个: %s" % (len(miss), ", ".join(sorted(miss)[:5])))
    if ghost:
        note("索引", c, "索引列出但磁盘不存在 %d 个: %s" % (len(ghost), ", ".join(sorted(ghost)[:5])))
    m = re.search(r'<div class="stat-num"[^>]*>(\d+)<', s)
    if m and int(m.group(1)) != len(on_disk):
        note("索引", c, "统计数字 %s 与实际 %d 不符" % (m.group(1), len(on_disk)))
    if "最后更新" in s:
        lu = re.search(r"最后更新[:：]\s*(\d{4}-\d{2}-\d{2})", s)
        latest = max((os.path.basename(p)[7:15] for p in on_disk), default=None)
        if lu and latest:
            exp = "%s-%s-%s" % (latest[:4], latest[4:6], latest[6:8])
            if lu.group(1) != exp:
                note("索引", c, "最后更新 %s 应为 %s" % (lu.group(1), exp))

# ---------- 4) 主页一致性 ----------
home = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
total_real = 0
for c in CATEGORIES:
    n = len(glob.glob(os.path.join(ROOT, c, "report_*.html")))
    total_real += n
    href = 'href="https://ts-dinglilu.github.io/%s/"' % c
    pos = home.find(href)
    if pos == -1:
        note("主页", c, "主页无该分类卡片")
        continue
    card = home[pos:home.find("</a>", pos)]
    au = re.search(r'<div class="auto-updated"[^>]*>(.*?)</div>', card, re.S)
    if not au:
        note("主页", c, "卡片缺少 auto-updated")
        continue
    txt = re.sub(r"<[^>]+>", "", au.group(1)).strip()
    latest = max((os.path.basename(p)[7:15] for p in glob.glob(os.path.join(ROOT, c, "report_*.html"))), default="")
    exp_iso = "%s-%s-%s" % (latest[:4], latest[4:6], latest[6:8])
    if exp_iso[5:] not in txt:
        note("主页", c, "卡片显示 '%s'，实际最新 %s" % (txt, exp_iso))
    if ("累计 %d 期" % n) not in txt:
        note("主页", c, "卡片期数不符: '%s'，实际 %d" % (txt, n))
m = re.search(r'<div class="stat-num"[^>]*>(\d+)\+</div>\s*<div class="stat-label"[^>]*>已生成日报</div>', home)
if m and int(m.group(1)) != total_real:
    note("主页", "全局", "已生成日报统计 %s+ 与实际 %d 不符" % (m.group(1), total_real))
elif not m:
    note("主页", "全局", "找不到『已生成日报』统计元素")

# ---------- 5) 主页残留模板文件 ----------
for stray in ("homepage_index.html",):
    p = os.path.join(ROOT, stray)
    if os.path.exists(p):
        note("冗余", stray, "疑似废弃的旧主页，仅被 2 个老报告引用")

# ---------- 输出 ----------
order = ["结构", "死链", "索引", "主页", "游离报告", "冗余"]
print("=" * 70)
print("报告总数: %d  分类数: %d  磁盘报告合计: %d" % (len(all_reports), len(CATEGORIES), total_real))
print("=" * 70)
for k in order + [k for k in problems if k not in order]:
    if k not in problems or not problems[k]:
        continue
    items = problems[k]
    print("\n### %s（%d）" % (k, len(items)))
    for it in items[:60]:
        print("  - " + it)
    if len(items) > 60:
        print("  ... 另有 %d 条" % (len(items) - 60))
if not problems:
    print("\n未发现问题。")
