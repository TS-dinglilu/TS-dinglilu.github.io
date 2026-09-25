# -*- coding: utf-8 -*-
"""周记 / 月记 / 年记生成器：站级汇总报告 + digest/ 聚合归档页。

周期规则（与每日自动化 05:00 错峰，自动化 06:30 触发）：
- weekly  ：date 所在周的上一周（周一 ~ 周日），周一运行生成上周
- monthly ：date 所在月的上一月，每月 1 日运行生成上月
- yearly  ：date 所在年的上一年，次年 1 月 2 日运行生成上一年

输出：
- digest/weekly_2026W38.html / monthly_2026M09.html / yearly_2026.html
- digest/index.html 聚合归档页（带 全部/周记/月记/年记 筛选）
报告内含 大类筛选标签（招聘 / 校园科研 / 地区 / 规划，同主页交互）+ 数据统计表。

用法（在 repo/ 下）：
  python scripts/build_digest.py --type weekly               # date 默认今天
  python scripts/build_digest.py --type weekly --date 2026-09-28
  python scripts/build_digest.py --type weekly --force       # 覆盖已存在
"""
import argparse
import datetime
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_report  # noqa: E402
import tail_template  # noqa: E402

DIGEST_DIR = os.path.join(ROOT, "digest")
GISCUS = build_report.GISCUS_SCRIPT

# 大类分组（聚合页筛选标签，与主页 data-cat 命名一致）
GROUPS = [
    ("recruit", "招聘", ["car-recruit", "mechanical-recruit", "byd-recruit",
                         "chery-recruit", "geely-recruit", "xiaomi-recruit",
                         "weixiaoli-recruit", "traditional-auto",
                         "supply-chain-recruit", "research-institute"]),
    ("campus", "校园科研", ["school-news", "ahut-campus", "drone-research"]),
    ("region", "地区", ["xuzhou-news", "nanjing-news", "shanghai-news",
                        "hangzhou-news", "jiangzhehu-news", "hefei-news",
                        "anhui-news", "jiangsu-news", "shenzhen-news"]),
    ("personal", "规划", ["future-planning"]),
]
CAT_NAME = tail_template.CATEGORY_NAMES

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0e1a; color: #d8e2f0; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; line-height: 1.7; }
a { color: #00d4ff; text-decoration: none; }
a:hover { text-decoration: underline; }
.hero { padding: 42px 20px 26px; text-align: center; background: linear-gradient(180deg, rgba(0,212,255,.08), transparent); border-bottom: 1px solid rgba(0,212,255,.15); }
.hero-tag { display: inline-block; font-size: 12px; letter-spacing: 2px; color: #00d4ff; border: 1px solid rgba(0,212,255,.4); border-radius: 999px; padding: 3px 14px; margin-bottom: 14px; }
.hero h1 { font-size: 26px; color: #fff; margin-bottom: 8px; }
.hero .subtitle { color: #8fa3c0; font-size: 14px; }
.stats { display: flex; justify-content: center; gap: 34px; margin-top: 20px; flex-wrap: wrap; }
.stat-num { font-size: 24px; font-weight: 700; color: #00d4ff; }
.stat-label { font-size: 12px; color: #8fa3c0; }
.container { max-width: 960px; margin: 0 auto; padding: 26px 18px 60px; }
.back-link { display: inline-block; font-size: 14px; margin-bottom: 18px; }
.filter-bar { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 22px; }
.filter-tab { cursor: pointer; font-size: 13px; padding: 6px 16px; border-radius: 999px; border: 1px solid rgba(0,212,255,.25); color: #8fa3c0; user-select: none; }
.filter-tab.active { background: rgba(0,212,255,.14); color: #00d4ff; border-color: rgba(0,212,255,.6); }
.group { margin-bottom: 30px; }
.group > h2 { font-size: 19px; color: #fff; border-left: 4px solid #00d4ff; padding-left: 12px; margin-bottom: 6px; }
.group > .group-sub { font-size: 12px; color: #8fa3c0; margin-bottom: 12px; padding-left: 16px; }
.cat-block { background: #111827; border: 1px solid rgba(0,212,255,.14); border-radius: 12px; padding: 14px 16px; margin-bottom: 12px; }
.cat-block.hidden { display: none; }
.group.hidden { display: none; }
.cat-head { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.cat-head h3 { font-size: 15px; color: #e8f2ff; }
.cnt { font-size: 12px; color: #00d4ff; background: rgba(0,212,255,.1); border-radius: 999px; padding: 1px 10px; }
.rep-item { padding: 8px 0; border-top: 1px dashed rgba(0,212,255,.12); }
.rep-item:first-of-type { border-top: none; }
.rep-line { font-size: 14px; }
.rep-date { color: #8fa3c0; font-size: 12px; margin-right: 8px; }
.toc { font-size: 12px; color: #7d8ea8; margin-top: 2px; }
.zero { color: #7d8ea8; font-size: 13px; }
h2.sec { font-size: 18px; color: #fff; border-left: 4px solid #00d4ff; padding-left: 12px; margin: 30px 0 12px; }
.table-wrap { overflow-x: auto; }
table.summary-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.summary-table th, .summary-table td { border: 1px solid rgba(0,212,255,.18); padding: 8px 10px; text-align: left; }
.summary-table th { background: rgba(0,212,255,.08); color: #9fd8ff; }
.footer { text-align: center; color: #5f7089; font-size: 12px; padding: 24px 0 34px; border-top: 1px solid rgba(0,212,255,.1); margin-top: 40px; }
"""


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def scan_reports(start_d, end_d):
    """返回 {cat: [(date, rel_path, title, sections[]), ...]} 周期内各分类报告。"""
    out = {}
    cats = [c for _, _, lst in GROUPS for c in lst]
    for cat in cats:
        items = []
        for p in sorted(glob.glob(os.path.join(ROOT, cat, "report_*.html"))):
            m = re.search(r"report_(\d{8})\.html", p)
            if not m:
                continue
            d = datetime.datetime.strptime(m.group(1), "%Y%m%d").date()
            if not (start_d <= d <= end_d):
                continue
            html = open(p, encoding="utf-8").read()
            secs = [strip_tags(x) for x in
                    re.findall(r'<div class="section-title">(.*?)</div>', html, re.S)]
            secs = [s for s in secs if s and "信息来源" not in s][:8]
            rel = "%s/%s" % (cat, os.path.basename(p))
            items.append((d, rel, CAT_NAME[cat], secs))
        items.sort(key=lambda t: t[0])
        out[cat] = items
    return out


def fmt_d(d):
    return d.strftime("%m-%d")


def build_report_html(kind, start_d, end_d, data):
    if kind == "weekly":
        iso = start_d.isocalendar()
        cn = "周记 · %d 年第 %d 周" % (iso[0], iso[1])
        fname = "weekly_%dW%02d.html" % (iso[0], iso[1])
    elif kind == "monthly":
        cn = "月记 · %d 年 %d 月" % (start_d.year, start_d.month)
        fname = "monthly_%dM%02d.html" % (start_d.year, start_d.month)
    else:
        cn = "年记 · %d 年" % start_d.year
        fname = "yearly_%d.html" % start_d.year

    n_reports = sum(len(v) for v in data.values())
    n_cats = sum(1 for v in data.values() if v)
    n_links = sum(len(re.findall(r'source-link',
                                 open(os.path.join(ROOT, rel), encoding="utf-8").read()))
                  for v in data.values() for _, rel, _, _ in v)
    total_days = (end_d - start_d).days + 1

    # 分组板块
    groups_html = []
    for gkey, gname, cats in GROUPS:
        g_reports = sum(len(data[c]) for c in cats)
        blocks = []
        for c in cats:
            items = data[c]
            if not items:
                blocks.append(
                    '<div class="cat-block" data-cat="%s">\n'
                    '  <div class="cat-head"><h3>%s</h3><span class="cnt">0 份</span></div>\n'
                    '  <p class="zero">本周期内该分类暂无报告（站点留白）</p>\n</div>' % (gkey, CAT_NAME[c]))
                continue
            lines = []
            for d, rel, title, secs in items:
                toc = ("板块：" + " · ".join(secs)) if secs else ""
                lines.append(
                    '<div class="rep-item">\n'
                    '  <div class="rep-line"><span class="rep-date">%s</span>'
                    '<a href="https://ts-dinglilu.github.io/%s" target="_blank">%s 📎</a></div>\n'
                    '  <div class="toc">%s</div>\n</div>' % (d.isoformat(), rel, title, toc))
            blocks.append(
                '<div class="cat-block" data-cat="%s">\n'
                '  <div class="cat-head"><h3>%s</h3><span class="cnt">%d 份</span></div>\n'
                '%s\n</div>' % (gkey, CAT_NAME[c], len(items), "\n".join(lines)))
        groups_html.append(
            '<div class="group" data-group="%s">\n'
            '  <h2>%s</h2>\n'
            '  <div class="group-sub">%d 个分类 · %d 份报告</div>\n'
            '%s\n</div>' % (gkey, gname, len(cats), g_reports, "\n".join(blocks)))

    # 统计表
    stat_rows = "\n".join(
        '<tr><td>%s</td><td>%d 份</td><td>%s</td></tr>' % (
            CAT_NAME[c], len(data[c]),
            ", ".join(fmt_d(d) for d, _, _, _ in data[c]) or "—")
        for _, _, cats in GROUPS for c in cats)

    # 来源汇总表
    src_rows = "\n".join(
        '<tr><td>%s</td><td><a href="https://ts-dinglilu.github.io/%s" target="_blank">📎 查看</a></td><td>%s</td></tr>'
        % (title, rel, d.isoformat())
        for c in [x for _, _, lst in GROUPS for x in lst] for d, rel, title, _ in data[c])

    tabs = ('<div class="filter-tab active" onclick="setFilter(this)">全部</div>\n'
            + "\n".join('<div class="filter-tab" onclick="setFilter(this, \'%s\')">%s</div>' % (k, n)
                        for k, n, _ in GROUPS))

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(cn)s | 站级汇总</title>
<style>%(css)s</style>
<script src="/guard.js" charset="utf-8"></script>
</head>
<body>
<div class="hero">
  <div class="hero-tag">站级汇总 · 自动生成</div>
  <h1>%(cn)s</h1>
  <p class="subtitle">覆盖 %(s_iso)s ~ %(e_iso)s（共 %(days)d 天）· 全站 23 个分类</p>
  <div class="stats">
    <div><div class="stat-num">%(n_rep)d</div><div class="stat-label">日报份数</div></div>
    <div><div class="stat-num">%(n_cat)d</div><div class="stat-label">活跃分类</div></div>
    <div><div class="stat-num">%(n_link)d</div><div class="stat-label">信息链接</div></div>
  </div>
</div>
<div class="container">
  <a class="back-link" href="https://ts-dinglilu.github.io/">← 返回主页</a>
  <div class="filter-bar">%(tabs)s</div>
%(groups)s
<h2 class="sec">数据统计</h2>
<div class="table-wrap">
<table class="summary-table">
<thead><tr><th>分类</th><th>本期报告</th><th>报告日期</th></tr></thead>
<tbody>
%(stat_rows)s
</tbody>
</table>
</div>
<h2 class="sec">信息来源汇总</h2>
<div class="table-wrap">
<table class="summary-table">
<thead><tr><th>报告</th><th>链接</th><th>日期</th></tr></thead>
<tbody>
%(src_rows)s
</tbody>
</table>
</div>
<div class="giscus"></div>
</div>
<div class="footer">周记月记年记 · 每周/月/年自动汇总 · © 2026 TS-dinglilu</div>
<script>
function setFilter(tab, key) {
  if (!key) key = 'all';
  document.querySelectorAll('.filter-tab').forEach(function(t) { t.classList.remove('active'); });
  tab.classList.add('active');
  document.querySelectorAll('.group').forEach(function(g) {
    g.classList.toggle('hidden', key !== 'all' && g.getAttribute('data-group') !== key);
  });
  document.querySelectorAll('.cat-block').forEach(function(b) {
    b.classList.toggle('hidden', key !== 'all' && b.getAttribute('data-cat') !== key);
  });
}
</script>
%(giscus)s
</body>
</html>
""" % dict(cn=cn, css=CSS, s_iso=start_d.isoformat(), e_iso=end_d.isoformat(),
           days=total_days, n_rep=n_reports, n_cat=n_cats, n_link=n_links,
           tabs=tabs, groups="\n".join(groups_html), stat_rows=stat_rows,
           src_rows=src_rows, giscus=GISCUS)
    return fname, html


INDEX_CSS = CSS + """
.report-list { display: flex; flex-direction: column; gap: 12px; }
.report-card { display: flex; justify-content: space-between; align-items: center; background: #111827; border: 1px solid rgba(0,212,255,.14); border-radius: 12px; padding: 14px 18px; color: #d8e2f0; }
.report-card.latest { border-color: rgba(0,212,255,.5); }
.report-card:hover { border-color: rgba(0,212,255,.55); text-decoration: none; }
.card-date { font-size: 15px; color: #fff; }
.latest-badge { font-size: 10px; color: #0a0e1a; background: #00d4ff; border-radius: 4px; padding: 1px 6px; margin-left: 8px; font-weight: 700; }
.card-link { font-size: 13px; color: #00d4ff; }
"""


def build_digest_index():
    files = sorted(glob.glob(os.path.join(DIGEST_DIR, "weekly_*.html"))
                   + glob.glob(os.path.join(DIGEST_DIR, "monthly_*.html"))
                   + glob.glob(os.path.join(DIGEST_DIR, "yearly_*.html")), reverse=True)
    cards = []
    for i, p in enumerate(files):
        n = os.path.basename(p)
        kind = ("周记" if n.startswith("weekly") else
                "月记" if n.startswith("monthly") else "年记")
        label = (re.sub(r"\.html$", "", n)
                 .replace("weekly_", "").replace("monthly_", "").replace("yearly_", ""))
        badge = '<span class="latest-badge">NEW</span>' if i == 0 else ""
        cards.append(
            '<a href="%s" class="report-card%s" target="_blank">\n'
            '  <div class="card-date">[%s] %s%s</div>\n'
            '  <div class="card-link">查看 →</div>\n</a>' % (n, " latest" if i == 0 else "",
                                                             kind, label, badge))
    listing = "\n".join(cards) or '<p class="zero">暂无汇总报告</p>'

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>周记月记年记 | 站级汇总</title>
<style>%(css)s</style>
<script src="/guard.js" charset="utf-8"></script>
</head>
<body>
<div class="hero">
  <div class="hero-tag">站级汇总 · 自动生成</div>
  <h1>周记 · 月记 · 年记</h1>
  <p class="subtitle">每周/每月/每年结束时自动汇总全站 23 个分类的动态与数据</p>
  <div class="stats">
    <div><div class="stat-num">%(n)d</div><div class="stat-label">汇总报告</div></div>
    <div><div class="stat-num">每周一</div><div class="stat-label">周记更新</div></div>
    <div><div class="stat-num">每月 1 日</div><div class="stat-label">月记更新</div></div>
  </div>
</div>
<div class="container">
  <a class="back-link" href="https://ts-dinglilu.github.io/">← 返回主页</a>
  <h2 class="sec">汇总归档</h2>
  <div class="report-list">
%(listing)s
  </div>
</div>
<div class="footer">周记月记年记 · © 2026 TS-dinglilu</div>
%(giscus)s
</body>
</html>
""" % dict(css=INDEX_CSS, n=len(files), listing=listing, giscus=GISCUS)
    with open(os.path.join(DIGEST_DIR, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("[OK] digest/index.html 已更新（%d 份汇总报告）" % len(files))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True, choices=["weekly", "monthly", "yearly"])
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    d = datetime.date.fromisoformat(args.date)

    if args.type == "weekly":
        monday = d - datetime.timedelta(days=d.weekday())
        start_d, end_d = monday - datetime.timedelta(days=7), monday - datetime.timedelta(days=1)
    elif args.type == "monthly":
        first = d.replace(day=1)
        start_d = (first - datetime.timedelta(days=1)).replace(day=1)
        end_d = first - datetime.timedelta(days=1)
    else:
        start_d, end_d = datetime.date(d.year - 1, 1, 1), datetime.date(d.year - 1, 12, 31)

    data = scan_reports(start_d, end_d)
    fname, html = build_report_html(args.type, start_d, end_d, data)

    os.makedirs(DIGEST_DIR, exist_ok=True)
    out_path = os.path.join(DIGEST_DIR, fname)
    if os.path.exists(out_path) and not args.force:
        print("[SKIP] 已存在: %s（--force 可覆盖）" % fname)
    else:
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print("[OK] 汇总报告已生成: digest/%s (%d bytes)" % (fname, len(html)))

    build_digest_index()


if __name__ == "__main__":
    main()
