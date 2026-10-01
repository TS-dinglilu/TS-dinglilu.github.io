#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自动化日报生成器 v3.0

用法:
  python scripts/build_report.py --category car-recruit --date 2026-09-09 --content path/to/body.html [--push]

兼容两种模板骨架:
  A. <main class="container"> 型 (如 car-recruit): 替换 <main> 内部, 保留原 header/footer
  B. 通用型: 保留模板 <head>+CSS+页面头部(hero), 丢弃正文与尾部,
     拼接新正文 + 统一 footer + giscus 脚本
"""
import argparse
import datetime
import glob
import hashlib
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail_template  # noqa: E402  标准尾部唯一真源

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEEKDAY_CN = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

ANCHORS = ['<div class="highlight-box"', '<div class="section"', '<div class="section "',
           '<div class="stats-grid',
           '<div class="nav-links', '<div class="card', '<div class="card-grid']
# 说明：把 highlight-box 放在最前，是因为部分分类（如 company-reputation）的正文以
# highlight-box 起头、且位于第一个 <div class="section"> 之前。若只按 section 切「头部」，
# 会把模板里同样位置的旧 highlight-box 一并当作页面头部保留，导致重建时该块重复出现。

GISCUS_SCRIPT = """<script>
// Scroll-to-top button visibility
window.addEventListener('scroll', function() {
  var btn = document.querySelector('.scroll-top');
  if (btn) {
    if (window.scrollY > 400) { btn.classList.add('visible'); }
    else { btn.classList.remove('visible'); }
  }
});

// Giscus configuration
var giscusScript = document.createElement('script');
giscusScript.src = 'https://giscus.app/client.js';
giscusScript.setAttribute('data-repo', 'TS-dinglilu/TS-dinglilu.github.io');
giscusScript.setAttribute('data-repo-id', 'R_kgDOTjqaJQ');
giscusScript.setAttribute('data-category', 'General');
giscusScript.setAttribute('data-category-id', 'DIC_kwDOTjqaJc4DCIL2');
giscusScript.setAttribute('data-mapping', 'pathname');
giscusScript.setAttribute('data-strict', '0');
giscusScript.setAttribute('data-reactions-enabled', '1');
giscusScript.setAttribute('data-emit-metadata', '0');
giscusScript.setAttribute('data-input-position', 'top');
giscusScript.setAttribute('data-theme', 'dark_dimmed');
giscusScript.setAttribute('data-lang', 'zh-CN');
giscusScript.setAttribute('data-loading', 'lazy');
giscusScript.crossOrigin = 'anonymous';
giscusScript.async = true;
var giscusBox = document.querySelector('.giscus');
if (giscusBox) { giscusBox.appendChild(giscusScript); }
</script>
"""


def die(msg):
    print("[ERROR] " + msg, file=sys.stderr)
    sys.exit(1)


def pick_template(category, exclude_name=None):
    d = os.path.join(ROOT, category)
    if not os.path.isdir(d):
        die("分类目录不存在: " + d)
    all_files = sorted(glob.glob(os.path.join(d, "report_*.html")))
    files = all_files
    if exclude_name:
        files = [f for f in all_files if os.path.basename(f) != exclude_name]
    if not files:
        # 新分类首期：目录里只有当天这一份报告，没有「别的历史报告」可当模板。
        # 此时退回用目标自身当模板（只取它的 <head>/CSS/hero 骨架），否则首期重建
        # （如同一天二次运行 publish_all）会因找不到模板直接失败。
        if all_files:
            return all_files[-1]
        die("该分类下没有任何历史报告可作为模板: " + category)
    return files[-1]


def replace_dates(text, dt):
    cn = "%d年%d月%d日" % (dt.year, dt.month, dt.day)
    iso = dt.strftime("%Y-%m-%d")
    text = re.sub(r"\d{4}年\d{1,2}月\d{1,2}日", cn, text)
    text = re.sub(r"\d{4}-\d{2}-\d{2}", iso, text)
    return text


def fix_weekday(text, dt):
    return re.sub(r"星期[一二三四五六日]", WEEKDAY_CN[dt.weekday()], text)


def normalize_head(html):
    """修复模板里的历史瑕疵: 重复 <body> 标签。"""
    html = re.sub(r"(<body[^>]*>)\s*(<body[^>]*>)+", r"\1", html)
    # 去掉头部结尾的空行：拼接处是 head_part + "\n" + body，若头部本身已带尾随空行，
    # 每重建一次就多积一行（实测 company-reputation 重建 7 次积了 7 个空行）。
    # 这里统一 rstrip 掉行尾空白，让构建幂等。
    html = html.rstrip() + "\n"
    return html


def autoclose_divs(html):
    """补齐未闭合的 <div>，避免尾部 footer 被吞进卡片；多余闭合则前置占位 div。"""
    o, c = html.count("<div"), html.count("</div>")
    if o > c:
        html = html + "\n" + "</div>\n" * (o - c)
    elif c > o:
        html = "<div>\n" * (c - o) + html
    return html


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def normalize_footer_name(html, category):
    """把页脚里的日报名换成标准名（唯一真源 tail_template.CATEGORY_NAMES）。

    页脚形如：<p>日报名 | 安徽工业大学机械工程硕士研究生个性化推荐报告</p>
    骨架 A（car-recruit）会整段保留模板的 footer，所以这里再兜一道，
    用 TITLE_SUFFIX 作锚点、只处理最后一个 <footer> 之后的区间，避免误伤正文。
    """
    std = tail_template.CATEGORY_NAMES.get(category)
    if not std:
        return html
    i = html.rfind("<footer")
    if i < 0:
        return html
    head, seg = html[:i], html[i:]
    new_seg, n = re.subn(
        r"<p>[^<]*?\|\s*" + re.escape(tail_template.TITLE_SUFFIX),
        "<p>" + std + " | " + tail_template.TITLE_SUFFIX,
        seg, count=1)
    return head + (new_seg if n else seg)


CSS_ASSET = os.path.join(ROOT, "assets", "report.css")
CSS_LINK = '<link rel="stylesheet" href="/assets/report.css">'


def extract_inline_css(html):
    """把与 assets/report.css 完全相同的内联 <style> 换成外部 <link>。

    报告页的公共 CSS 全站一致（约 50KB）。内联会让每份报告多背 49KB、
    且无法跨页缓存（全站 390 份 ≈ 19MB 纯重复）。抽成共享文件后浏览器只下一次。
    只替换「指纹与 assets/report.css 一致」的那一块；页面自带的
    custom overrides（.nav-toc / .summary-table 等）原样保留。
    """
    if not os.path.exists(CSS_ASSET):
        return html
    want = hashlib.md5(open(CSS_ASSET, encoding="utf-8").read().strip().encode()).hexdigest()
    n = 0

    def repl(m):
        nonlocal n
        if hashlib.md5(m.group(1).strip().encode()).hexdigest() == want:
            n += 1
            return CSS_LINK if n == 1 else ""
        return m.group(0)

    return re.sub(r"<style[^>]*>(.*?)</style>", repl, html, flags=re.S)


def inject_meta(html, category, title, dt):
    """确保 <head> 内的元信息完整且正确（description / og / canonical）。

    历史母版复制会造成 og:url 指错分类、缺 og 标签、缺 description。
    这里先清掉旧的同类标签，再注入一份标准块，保证每次都收敛到唯一正确状态。
    """
    i, j = html.find("<head"), html.find("</head>")
    if i < 0 or j < 0:
        return html
    head, rest = html[i:j], html[j:]

    def drop(pat):
        nonlocal head
        head = re.sub(pat, "", head, flags=re.S)

    for pat in (r'<meta name="description"[^>]*>\s*',
                r'<meta property="og:[^"]*"[^>]*>\s*',
                r'<meta name="twitter:[^"]*"[^>]*>\s*',
                r'<link rel="canonical"[^>]*>\s*'):
        drop(pat)

    iso_date = dt.strftime("%Y-%m-%d")
    block = tail_template.build_meta(category, title, iso_date)
    # 插在 <title> 之后、<style> 之前，保持可读
    mt = re.search(r"</title>", head)
    if mt:
        head = head[:mt.end()] + "\n" + block + head[mt.end():]
    else:
        head = head.rstrip() + "\n" + block + "\n"
    return html[:i] + head + rest


def unify_title_and_h1(head, category, dt):
    """把页面头部里的 <title> 与可见 <h1> 归一到「标准日报名 + 本次日期」。

    历史教训（2026-10-01 全站排查）：<title> 曾经是用模板 <h1> 派生的，于是母版里
    残留的旧文案会一直往下传染——实测积累了 96 份错标题（「六大XX」前缀 73 份、
    日期错位 1 份、格式不统一 22 份），详见 scripts/fix_titles.py。
    改成以 tail_template.CATEGORY_NAMES + 构建日期为唯一真源后，模板再脏也不会传染。
    """
    std = tail_template.CATEGORY_NAMES.get(category, category)
    title = "%s - %s年%d月%d日" % (std, dt.year, dt.month, dt.day)

    # 可见标题：去掉继承来的裸「六大」前缀，并把 h1 文本对齐标准名
    h1 = re.search(r"(<h1[^>]*>)(.*?)(</h1>)", head, re.S)
    if h1:
        inner = re.sub(r"^\s*六大\s*", "", h1.group(2), count=1)
        # 仅当 h1 里已含日报名时保留其 emoji 等装饰，否则直接用标准名
        if std not in strip_tags(inner):
            inner = std
        head = head[:h1.start(2)] + inner + head[h1.end(2):]

    head = re.sub(r"<title>.*?</title>", "<title>%s</title>" % title,
                  head, count=1, flags=re.S)
    return head


def build_report(category, dt, content_path):
    target_name = "report_%s.html" % dt.strftime("%Y%m%d")
    tpl_path = pick_template(category, exclude_name=target_name)
    tpl = open(tpl_path, encoding="utf-8").read()
    print("[..] 模板: " + os.path.basename(tpl_path))

    body = open(content_path, encoding="utf-8").read().strip()
    # 清掉正文里可能残留的旧评论区（尾部由骨架各自统一拼接，保证全站一致）
    body, _ = tail_template.strip_comment_artifacts(body)

    m = re.search(r"(<main[^>]*>)(.*?)(</main>)", tpl, re.S)

    if m:  # ---- 骨架 A: <main> 型 ----
        # 评论区需在 </main> 之内，故并入正文
        if tail_template.COMMENTS_BLOCK not in body:
            body += "\n\n" + tail_template.COMMENTS_BLOCK + "\n"
        head_part = tpl[: m.start(2)]
        tail_part = tpl[m.end(2):]
        head_part = fix_weekday(replace_dates(head_part, dt), dt)
        tail_part = fix_weekday(replace_dates(tail_part, dt), dt)
        tail_part = tail_part.replace("TraeWork Automation", "WorkBuddy Automation")
        # <title> / <h1> 统一为标准日报名 + 本次日期（骨架 A 曾原样继承模板头部，
        # 是历史错标题的另一条来源；见 scripts/fix_titles.py）
        head_part = unify_title_and_h1(head_part, category, dt)
        out = autoclose_divs(normalize_head(head_part) + "\n" + body) + tail_part
    else:  # ---- 骨架 B: 通用型 ----
        body_i = tpl.find("<body")
        body_i = tpl.find(">", body_i) + 1
        cands = [p for p in (tpl.find(a, body_i) for a in ANCHORS) if p > 0]
        if not cands:
            die("模板中找不到内容锚点: " + tpl_path)
        cs = min(cands)
        head_part = normalize_head(tpl[:cs])
        # 去掉头部里的目录导航(锚点会失效)
        head_part = re.sub(r'<div class="nav-links">.*?</div>\s*', "", head_part, flags=re.S)
        head_part = fix_weekday(replace_dates(head_part, dt), dt)
        # 更新 <title> / <h1>（统一走 unify_title_and_h1，见其 docstring）
        head_part = unify_title_and_h1(head_part, category, dt)
        std = tail_template.CATEGORY_NAMES.get(category, category)
        # 标准尾部（评论区 + 页脚 + 返回顶部 + giscus）放在容器闭合之后，与 unify_style 结果一致
        tail = tail_template.build_tail(std, dt.year, dt.month, dt.day,
                                        GISCUS_SCRIPT, has_main_close=False)
        out = autoclose_divs(head_part + "\n" + body) + "\n" + tail

    # 兜底：页脚日报名统一为标准名（骨架 A / B 都覆盖）
    out = normalize_footer_name(out, category)

    # 元信息（description / og / canonical）：统一按本分类注入，修掉母版复制的历史错配
    std_title = tail_template.CATEGORY_NAMES.get(category, category)
    out = inject_meta(out, category, std_title, dt)

    # 公共 CSS 抽成共享外链，避免每份报告重复内联 49KB
    out = extract_inline_css(out)

    # 密码守卫：每份新报告自动带上全站访问门（幂等）
    try:
        from password_gate import inject as _inject_gate
        out, _ = _inject_gate(out)
    except Exception as _e:  # noqa: BLE001
        print("[WARN] 密码守卫注入失败(不影响构建): %s" % _e)

    out_path = os.path.join(ROOT, category, target_name)
    open(out_path, "w", encoding="utf-8").write(out)
    print("[OK] 报告已生成: %s (%d bytes)" % (out_path, len(out)))
    return out_path


def rebuild_index(category):
    d = os.path.join(ROOT, category)
    idx_path = os.path.join(d, "index.html")
    if not os.path.exists(idx_path):
        print("[WARN] 无 index.html，跳过: " + idx_path)
        return None
    html = open(idx_path, encoding="utf-8").read()

    reports = sorted(glob.glob(os.path.join(d, "report_*.html")), reverse=True)
    names = [os.path.basename(p) for p in reports]

    cards = []
    for i, n in enumerate(names):
        ds = re.search(r"report_(\d{8})\.html", n).group(1)
        dt = datetime.datetime.strptime(ds, "%Y%m%d")
        iso = dt.strftime("%Y-%m-%d")
        wd = WEEKDAY_CN[dt.weekday()]
        latest_cls = " latest" if i == 0 else ""
        badge = '<span class="latest-badge">LATEST</span>' if i == 0 else ""
        link_text = "点击查看 →" if i == 0 else "查看 →"
        cards.append(
            '        <a href="%s" class="report-card%s" target="_blank">\n'
            '            <div class="card-info">\n'
            '                <div class="card-date">%s%s</div>\n'
            '                <div class="card-weekday">%s</div>\n'
            '            </div>\n'
            '            <div class="card-link">%s</div>\n'
            "        </a>" % (n, latest_cls, iso, badge, wd, link_text)
        )

    block = '<div class="report-list">\n' + "\n".join(cards) + "\n    </div>"

    start = html.find('<div class="report-list">')
    if start == -1:
        die("index.html 中找不到 report-list: " + idx_path)
    # 只在"报告列表"区域内定位结尾，避免误吞后面的评论区 / 页脚
    bounds = [p for p in (html.find('<div class="comments-section">', start),
                          html.find('<footer', start)) if p > start]
    bound = min(bounds) if bounds else len(html)
    window = html[start:bound]
    last_a = window.rfind("</a>")
    if last_a == -1:
        die("report-list 区域内找不到 </a>: " + idx_path)
    end = start + window.find("</div>", last_a) + len("</div>")
    html = html[:start] + block + html[end:]

    html = re.sub(
        r'(<div class="stat-num">)\d+(</div>\s*<div class="stat-label">报告总数</div>)',
        lambda m: m.group(1) + str(len(names)) + m.group(2),
        html,
        count=1,
    )
    new_latest = names[0][7:11] + "-" + names[0][11:13] + "-" + names[0][13:15]
    html = re.sub(r"最后更新[:：]\s*\d{4}-\d{2}-\d{2}", "最后更新: " + new_latest, html)

    open(idx_path, "w", encoding="utf-8").write(html)
    print("[OK] 索引已更新: %s (共 %d 份)" % (idx_path, len(names)))
    return idx_path


def push(dt):
    subprocess.run(["git", "add", "-A"], cwd=ROOT)
    stamp = dt.strftime("%Y-%m-%d")
    st = subprocess.run(
        ["git", "-c", "user.name=TS-dinglilu", "-c", "user.email=workbuddy@local",
         "commit", "-m", "每日日报自动更新 %s" % stamp],
        cwd=ROOT, capture_output=True, text=True)
    if st.returncode != 0:
        print("[WARN] commit 无变更或失败: " + (st.stdout or st.stderr).strip()[:200])
        return False
    for i in range(3):
        r = subprocess.run(["git", "push", "origin", "main"], cwd=ROOT,
                           capture_output=True, text=True,
                           env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
        if r.returncode == 0:
            print("[OK] 已推送到 GitHub")
            return True
        print("[WARN] push 第 %d 次失败: %s" % (i + 1, (r.stderr or r.stdout).strip()[:200]))
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--content", required=True, help="正文 HTML 文件路径")
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    dt = datetime.datetime.strptime(args.date, "%Y-%m-%d")
    build_report(args.category, dt, args.content)
    rebuild_index(args.category)
    if args.push:
        push(dt)


if __name__ == "__main__":
    main()
