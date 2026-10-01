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
  8. 元信息       每页含唯一 title / description / og:url（且指向自身分类）、canonical
  9. 资源外链     </head> 完整、报告页外链 /assets/report.css（不再内联大块 CSS）
 10. 站点基建     根目录存在 404.html / robots.txt / sitemap.xml / .nojekyll，且 sitemap 覆盖全部报告

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
              "ahut-campus", "byd-recruit", "chery-recruit", "chery-insider", "geely-recruit",
              "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
              "supply-chain-recruit", "research-institute", "future-planning",
              "xuzhou-news", "nanjing-news", "shanghai-news", "hangzhou-news",
              "jiangzhehu-news", "hefei-news", "anhui-news", "jiangsu-news",
              "shenzhen-news",
              "xuzhou-recruit", "nanjing-recruit", "shanghai-recruit",
              "hangzhou-recruit", "jiangzhehu-recruit", "hefei-recruit",
              "anhui-recruit", "jiangsu-recruit", "shenzhen-recruit",
              "company-reputation"]
VALID = set(CATEGORIES) | {"digest"}  # digest = 周记月记年记板块

# 分类的「建号日期」：新增分类是从某一天才开始有报告的，此前各天不参与「跨分类漏期」比对，
# 否则新分类会被判定成「自 20260901 起每天都缺」，一次刷出几十条假 ERROR。
# 只登记「中途新增」的分类；老分类默认不设下限（00000000）。
# 已拍板不补的历史欠账日期（2026-09-25 用户确认保留留白，audit 不再报 WARN）
SKIP_DAYS = {"20260916", "20260920", "20260921", "20260922", "20260923"}

START_DATES = {
    "company-reputation": "20261001",    # 企业口碑日报，2026-10-01 新增
    "chery-insider": "20260927",          # 奇瑞职场口碑日报，2026-09-27 新增
    "supply-chain-recruit": "20260924",  # 车企供应链招聘日报，2026-09-24 新增
    "xuzhou-news": "20260924",           # 地区·徐州汽车机械日报，2026-09-25 新增
    "nanjing-news": "20260924",          # 地区·南京汽车机械日报
    "shanghai-news": "20260924",         # 地区·上海汽车机械日报
    "hangzhou-news": "20260924",         # 地区·杭州汽车机械日报
    "jiangzhehu-news": "20260924",       # 地区·江浙沪汽车机械日报
    "hefei-news": "20260924",            # 地区·合肥汽车机械日报
    "anhui-news": "20260924",            # 地区·安徽汽车机械日报
    "jiangsu-news": "20260924",          # 地区·江苏汽车机械日报
    "shenzhen-news": "20260924",         # 地区·深圳汽车机械日报
    "xuzhou-recruit": "20260926",        # 地区·徐州招聘日报，2026-09-26 新增
    "nanjing-recruit": "20260926",       # 地区·南京招聘日报
    "shanghai-recruit": "20260926",      # 地区·上海招聘日报
    "hangzhou-recruit": "20260926",      # 地区·杭州招聘日报
    "jiangzhehu-recruit": "20260926",    # 地区·江浙沪招聘日报
    "hefei-recruit": "20260926",         # 地区·合肥招聘日报
    "anhui-recruit": "20260926",         # 地区·安徽招聘日报
    "jiangsu-recruit": "20260926",       # 地区·江苏招聘日报
    "shenzhen-recruit": "20260926",      # 地区·深圳招聘日报
}

SITE_BASE = "https://ts-dinglilu.github.io"

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
                if d not in cover[c] and d >= START_DATES.get(c, "00000000")
                and d not in SKIP_DAYS]
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
            if st not in all_days and st not in SKIP_DAYS:
                miss = [c for c in CATEGORIES
                        if st >= START_DATES.get(c, "00000000")]
                if miss:
                    warn("漏期", day.isoformat(),
                         "缺 %d 个分类（全天缺失）: %s ——请用 build_backfill.py 补做"
                         % (len(miss), ", ".join(miss)))
            day += datetime.timedelta(days=1)


def _page_expected_url(path):
    """由文件路径推出该页面「应有的」规范 URL（用于校验 og:url / canonical 是否指错分类）。"""
    r = rel(path)
    if r == "index.html":
        return SITE_BASE + "/"
    seg = r.split("/")[0]
    if "/" in r:
        return "%s/%s/" % (SITE_BASE, seg)
    return "%s/%s" % (SITE_BASE, seg)


def _titles_of(paths):
    """读一批页面的 <title>，返回 {title: [files]} 供重复标题检测。"""
    seen = defaultdict(list)
    for f in paths:
        if not os.path.exists(f):
            continue
        m = re.search(r"<title>(.*?)</title>", open(f, encoding="utf-8").read(), re.S)
        if m:
            seen[m.group(1).strip()].append(rel(f))
    return seen


def check_meta():
    """元信息一致性：每页必须有 description / og:url 且 og:url 指向自身、有 canonical。
    历史教训：新增分类复制母版后忘记改 og:url，导致 18 个分类的 og:url 全指向
    traditional-auto/（社交分享与搜索引擎都会串页）。这里把它固化成硬校验。"""
    pages = html_files()
    for f in pages:
        r = rel(f)
        # 404 页刻意 noindex，不需要 description/og/canonical（搜索引擎也不该索引它）
        if r.endswith("404.html"):
            s404 = open(f, encoding="utf-8").read()
            if 'name="robots"' not in s404 or "noindex" not in s404:
                warn("元信息", r, "404 页缺少 noindex（可能被搜索引擎收进索引）")
            continue
        s = open(f, encoding="utf-8").read()
        head = s[:s.find("</head>")] if "</head>" in s else s[:5000]
        if "</head>" not in s:
            err("元信息", r, "缺少 </head>（头部未正确闭合）")
        m = re.search(r'<meta name="description" content="([^"]*)"', head)
        if not m or not m.group(1).strip():
            err("元信息", r, "缺少 meta description")
        m = re.search(r'<meta property="og:url" content="([^"]*)"', head)
        exp = _page_expected_url(f)
        if not m:
            err("元信息", r, "缺少 og:url")
        elif m.group(1).rstrip("/") != exp.rstrip("/"):
            err("元信息", r, "og:url=%s 应为 %s" % (m.group(1), exp))
        m = re.search(r'<link rel="canonical" href="([^"]*)"', head)
        if not m:
            err("元信息", r, "缺少 canonical")
        elif m.group(1).rstrip("/") != exp.rstrip("/"):
            err("元信息", r, "canonical=%s 应为 %s" % (m.group(1), exp))
        if not re.search(r'<meta name="viewport"', head):
            warn("元信息", r, "缺少 viewport（移动端缩放异常）")

    # 同一分类内不应出现完全相同的 <title>（说明日报名没跟着分类走）
    for c in CATEGORIES:
        seen = _titles_of(glob.glob(os.path.join(ROOT, c, "report_*.html")))
        for t, fs in seen.items():
            if len(fs) > 1:
                warn("元信息", c, "%d 份报告共用同一 <title>: %s" % (len(fs), t[:60]))


def check_assets():
    """资源外链化：报告页应外链 /assets/report.css，而不是各自内联 49KB CSS。
    内联 CSS 会让每份报告多 20KB+，390 份累计就是十几 MB 的重复传输。"""
    css = os.path.join(ROOT, "assets", "report.css")
    if not os.path.exists(css):
        err("资源", "assets/report.css", "缺失（报告页外链的共享样式表）")
    else:
        sz = os.path.getsize(css)
        if sz < 20000:
            warn("资源", "assets/report.css", "体积仅 %d 字节，疑似被截断" % sz)

    inline_big = 0
    for f in report_files():
        s = open(f, encoding="utf-8").read()
        if "/assets/report.css" not in s:
            inline_big += 1
            err("资源", rel(f), "未外链 /assets/report.css（仍在页内自带样式）")
    if inline_big:
        warn("资源", "全站", "%d 份报告仍内联样式，可用 scripts/extract_css.py 批量抽离" % inline_big)

    # 主页 / 分类归档页同样纳入 <head> 完整性检查
    for f in [os.path.join(ROOT, "index.html")] + \
             [os.path.join(ROOT, c, "index.html") for c in CATEGORIES] + \
             [os.path.join(ROOT, "digest", "index.html")]:
        if os.path.exists(f) and "</head>" not in open(f, encoding="utf-8").read():
            err("资源", rel(f), "缺少 </head>")


def check_infra():
    """站点基建：404 页、robots、sitemap、.nojekyll 必须存在；sitemap 必须覆盖全部报告页。
    缺 .nojekyll 时 GitHub Pages 会跳过下划线开头的文件；缺 sitemap 则搜索引擎收录慢。"""
    for name, must in (("404.html", True), ("robots.txt", True),
                       ("sitemap.xml", True), (".nojekyll", False)):
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            (err if must else warn)("基建", name, "站点根缺少该文件")
    reb = os.path.join(ROOT, "robots.txt")
    if os.path.exists(reb):
        t = open(reb, encoding="utf-8").read()
        if "Sitemap:" not in t:
            warn("基建", "robots.txt", "未声明 Sitemap 地址")
        if "Allow" not in t:
            warn("基建", "robots.txt", "未显式 Allow，部分爬虫可能保守抓取")

    sm = os.path.join(ROOT, "sitemap.xml")
    if os.path.exists(sm):
        t = open(sm, encoding="utf-8").read()
        # sitemap 里的目录 URL 带尾斜杠、报告 URL 不带；统一去尾斜杠后比对
        def norm(u):
            u = u.rstrip("/")
            return u if u else SITE_BASE
        locs = {norm(x) for x in re.findall(r"<loc>([^<]+)</loc>", t)}
        need = {norm(_page_expected_url(f)) for f in report_files()}
        need |= {norm(_page_expected_url(os.path.join(ROOT, c, "index.html")))
                 for c in CATEGORIES}
        need.add(norm(SITE_BASE + "/"))
        miss = need - locs
        if miss:
            err("基建", "sitemap.xml", "缺失 %d 条（例：%s）—— 请运行 scripts/build_sitemap.py"
                % (len(miss), sorted(miss)[0]))
        if len(locs) < len(need):
            warn("基建", "sitemap.xml", "仅 %d 条，预期至少 %d 条" % (len(locs), len(need)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    for fn in (check_structure, check_comments, check_links,
               check_category_index, check_homepage, check_dates,
               check_meta, check_assets, check_infra):
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
