#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
站点健康检查：一次性体检本地仓库的全站一致性，用于每日发布后自查与排障。

检查项
  1. 结构完整性   结尾 </html>、<html>/<body> 唯一、<div> 配平
  2. 评论区       每份报告都能加载 giscus
  3. 链接         站内 .html 链接可达、站点路径拼写正确
  4. 分类索引     报告列表 vs 磁盘、统计数字、"最后更新"日期
  5. 站点主页     分类卡片的"最新日期 / 累计期数"、全局总数
  6. 日期覆盖     各分类缺失的日期（漏跑检测，默认看最近 45 天有报告的日期集合）
  7. 旧品牌       残留的 TRAE / TraeWork Automation

用法:
  python scripts/audit_site.py            # 人类可读报告
  python scripts/audit_site.py --quiet    # 只输出问题，无问题则静默
退出码: 0 = 无 ERROR；1 = 存在 ERROR（可直接用于 CI / 发布后判断）
"""
import argparse
import datetime
import glob
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORIES = ["car-recruit", "mechanical-recruit", "school-news", "drone-research",
              "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
              "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
              "supply-chain-recruit", "research-institute", "future-planning"]
VALID = set(CATEGORIES)

# 分类的「建号日期」：新增分类是从某一天才开始有报告的，此前各天不参与「跨分类漏期」比对，
# 否则新分类会被判定成「自 20260901 起每天都缺」，一次刷出几十条假 ERROR。
# 只登记「中途新增」的分类；老分类默认不设下限（00000000）。
START_DATES = {
    "supply-chain-recruit": "20260924",  # 车企供应链招聘日报，2026-09-24 新增
}

ERRORS = defaultdict(list)
WARNS = defaultdict(list)


def err(kind, where, msg):
    ERRORS[kind].append("%-46s %s" % (where, msg))


def warn(kind, where, msg):
    WARNS[kind].append("%-46s %s" % (where, msg))


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


# 注意：content/、logs/、.workbuddy/ 自 2026-09-15 起已并入仓库，
# 但它们不是站点页面（content/ 存的是只有 <main> 内部内容的正文片段），
# 因此站内文件扫描必须排除这些目录，否则会把正文片段误判成"截断"。
NON_SITE_DIRS = {"content", "logs", ".workbuddy", "scripts", ".git", "backups"}


def site_dirs():
    """仓库内属于站点的一级目录（排除 content/logs/.workbuddy/scripts 等非站点目录）。"""
    out = []
    for d in sorted(glob.glob(os.path.join(ROOT, "*"))):
        if not os.path.isdir(d):
            continue
        name = os.path.basename(d)
        if name in NON_SITE_DIRS or name.startswith("."):
            continue
        out.append(d)
    return out


def html_files():
    files = glob.glob(os.path.join(ROOT, "*.html"))
    for d in site_dirs():
        files += glob.glob(os.path.join(d, "*.html"))
    return sorted(set(files))


def report_files():
    """站点内的日报页面（各分类目录下的 report_*.html），同样排除非站点目录，
    避免 content/ 或 logs/ 里万一出现同名文件被当成站点报告参与统计与检查。"""
    files = []
    for d in site_dirs():
        files += glob.glob(os.path.join(d, "report_*.html"))
    return sorted(files)


def check_structure():
    for f in html_files():
        r = rel(f)
        s = open(f, encoding="utf-8").read()
        if not s.rstrip().endswith("</html>"):
            err("结构", r, "结尾不是 </html>（疑似截断）")
        if s.count("<html") != 1:
            err("结构", r, "<html> 出现 %d 次" % s.count("<html"))
        if s.count("<body") != 1:
            err("结构", r, "<body> 出现 %d 次" % s.count("<body"))
        if s.count("</body>") != 1:
            err("结构", r, "</body> 出现 %d 次" % s.count("</body>"))
        o, c = s.count("<div"), s.count("</div>")
        if o != c:
            err("结构", r, "<div> 配平差 %+d" % (o - c))
        if "TRAE Automation" in s or "TraeWork Automation" in s:
            warn("旧品牌", r, "残留 TRAE Automation")
        if "homepage_index.html" in s:
            err("结构", r, "引用了已归档的 homepage_index.html")


def check_comments():
    for f in report_files():
        if "giscus.app" not in open(f, encoding="utf-8").read():
            err("评论区", rel(f), "未挂载 giscus")


def check_links():
    reports = report_files()
    indexes = [os.path.join(ROOT, c, "index.html") for c in CATEGORIES]
    for f in reports + indexes + [os.path.join(ROOT, "index.html")]:
        if not os.path.exists(f):
            continue
        r = rel(f)
        base = os.path.dirname(f)
        s = open(f, encoding="utf-8").read()
        # 站内相对链接
        for m in re.finditer(r'href="([^"#]+\.html)(?:#[^"]*)?"', s):
            href = m.group(1)
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(base, href))):
                err("死链", r, "站内链接不存在: %s" % href)
        # 站点绝对路径拼写
        for m in re.finditer(r"ts-dinglilu\.github\.io/([a-z\-]+)(?=[/\"'\s<)]|$)", s):
            seg = m.group(1)
            if seg not in VALID and seg not in ("index",):
                err("死链", r, "站点路径拼写错误: /%s/" % seg)


def check_category_index():
    for c in CATEGORIES:
        idx = os.path.join(ROOT, c, "index.html")
        if not os.path.exists(idx):
            err("索引", c, "缺少 index.html")
            continue
        s = open(idx, encoding="utf-8").read()
        listed = set(re.findall(r'href="(report_\d{8}\.html)"', s))
        disk = set(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, c, "report_*.html")))
        for x in sorted(disk - listed):
            err("索引", c, "磁盘有但索引未列出: %s" % x)
        for x in sorted(listed - disk):
            err("索引", c, "索引列出但文件不存在: %s" % x)
        m = re.search(r'<div class="stat-num"[^>]*>(\d+)<', s)
        if m and int(m.group(1)) != len(disk):
            err("索引", c, "统计数字 %s ≠ 实际 %d" % (m.group(1), len(disk)))
        lu = re.search(r"最后更新[:：]\s*(\d{4}-\d{2}-\d{2})", s)
        if lu and disk:
            latest = max(x[7:15] for x in disk)
            exp = "%s-%s-%s" % (latest[:4], latest[4:6], latest[6:8])
            if lu.group(1) != exp:
                err("索引", c, "最后更新 %s 应为 %s" % (lu.group(1), exp))


def check_homepage():
    home = os.path.join(ROOT, "index.html")
    s = open(home, encoding="utf-8").read()
    total = 0
    for c in CATEGORIES:
        disk = glob.glob(os.path.join(ROOT, c, "report_*.html"))
        total += len(disk)
        pos = s.find('href="https://ts-dinglilu.github.io/%s/"' % c)
        if pos == -1:
            err("主页", c, "主页无该分类卡片")
            continue
        card = s[pos:s.find("</a>", pos)]
        au = re.search(r'<div class="auto-updated"[^>]*>(.*?)</div>', card, re.S)
        if not au:
            err("主页", c, "卡片缺少 auto-updated 元信息")
            continue
        txt = re.sub(r"<[^>]+>", "", au.group(1)).strip()
        if disk:
            latest = max(os.path.basename(p)[7:15] for p in disk)
            exp = "%s-%s-%s" % (latest[:4], latest[4:6], latest[6:8])
            if exp[5:] not in txt:
                err("主页", c, "卡片显示『%s』，实际最新 %s" % (txt, exp))
        if ("累计 %d 期" % len(disk)) not in txt:
            err("主页", c, "卡片期数不符: 『%s』实际 %d" % (txt, len(disk)))
    m = re.search(r'<div class="stat-num"[^>]*>(\d+)\+</div>\s*<div class="stat-label"[^>]*>已生成日报', s)
    if not m:
        warn("主页", "全局", "找不到『已生成日报』统计元素")
    elif int(m.group(1)) != total:
        err("主页", "全局", "已生成日报 %s+ ≠ 实际 %d" % (m.group(1), total))


def check_dates():
    """漏跑检测：统计各分类最新报告日期，找出「已有其它分类但本分类缺」的日期。"""
    cover = {}
    for c in CATEGORIES:
        ds = set()
        for p in glob.glob(os.path.join(ROOT, c, "report_*.html")):
            ds.add(os.path.basename(p)[7:15])
        cover[c] = ds
    all_days = set().union(*cover.values()) if cover else set()
    recent = sorted(d for d in all_days if d >= "20260901")
    for d in recent:
        miss = [c for c in CATEGORIES
                if d not in cover[c] and d >= START_DATES.get(c, "00000000")]
        if miss:
            iso = "%s-%s-%s" % (d[:4], d[4:6], d[6:8])
            err("漏期", iso, "缺 %d 个分类: %s" % (len(miss), ", ".join(miss)))

    # 全天缺失：某一天所有分类都没有报告时，上面的循环没有参照物、查不出来
    # （2026-09-16 就是这样被漏掉的）。这里用「已首报日期 → 昨天」的连续区间补一道检查。
    if recent:
        day = datetime.datetime.strptime(recent[0], "%Y%m%d").date() + datetime.timedelta(days=1)
        today = datetime.date.today()
        while day < today:
            st = day.strftime("%Y%m%d")
            if st not in all_days:
                warn("漏期", day.isoformat(),
                     "%d 个分类全部没有该日报告（全天缺失）——请用 build_backfill.py 补做"
                     % len(CATEGORIES))
            day += datetime.timedelta(days=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    for fn in (check_structure, check_comments, check_links,
               check_category_index, check_homepage, check_dates):
        fn()

    n_err = sum(len(v) for v in ERRORS.values())
    n_warn = sum(len(v) for v in WARNS.values())

    if not args.quiet or n_err:
        print("=" * 68)
        print("站点健康检查  |  分类 %d  报告 %d  首页 %s"
              % (len(CATEGORIES),
                 len(report_files()),
                 "OK" if os.path.exists(os.path.join(ROOT, "index.html")) else "缺失"))
        print("=" * 68)

    for group, tag in ((ERRORS, "[ERROR]"), (WARNS, "[WARN ]")):
        for k in sorted(group, key=lambda x: -len(group[x])):
            if not group[k]:
                continue
            print("\n%s %s（%d）" % (tag, k, len(group[k])))
            for it in group[k][:80]:
                print("   " + it)
            if len(group[k]) > 80:
                print("   ... 另有 %d 条" % (len(group[k]) - 80))

    if n_err:
        print("\n结果: %d 个错误, %d 个警告 → 需要修复" % (n_err, n_warn))
        return 1
    if n_warn:
        print("\n结果: 0 个错误, %d 个警告" % n_warn)
    else:
        print("\n结果: 全部通过 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
