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
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail_template  # noqa: E402  标准尾部唯一真源

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEEKDAY_CN = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

ANCHORS = ['<div class="section"', '<div class="section ', '<div class="stats-grid',
           '<div class="nav-links', '<div class="card', '<div class="card-grid']

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
    files = sorted(glob.glob(os.path.join(d, "report_*.html")))
    if exclude_name:
        files = [f for f in files if os.path.basename(f) != exclude_name]
    if not files:
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
        # 更新 <title>
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", head_part, re.S)
        # <title> 沿用模板 <h1>：页面标题允许带 emoji / 用全称，属既有风格，历史报告一致。
        # 页脚日报名则统一走 tail_template.CATEGORY_NAMES（见 normalize_footer_name），
        # 因为页脚名是 unify_style 的统一对象，拿 <h1> 派生的名字会让两份工具每天打架。
        title = strip_tags(h1.group(1)) if h1 else category
        head_part = re.sub(r"<title>.*?</title>",
                           "<title>%s | %s</title>" % (title, dt.strftime("%Y-%m-%d")),
                           head_part, count=1, flags=re.S)
        # 标准尾部（评论区 + 页脚 + 返回顶部 + giscus）放在容器闭合之后，与 unify_style 结果一致
        tail = tail_template.build_tail(title, dt.year, dt.month, dt.day,
                                        GISCUS_SCRIPT, has_main_close=False)
        out = autoclose_divs(head_part + "\n" + body) + "\n" + tail

    # 兜底：页脚日报名统一为标准名（骨架 A / B 都覆盖）
    out = normalize_footer_name(out, category)

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
            '        <a href="%s" class="report-card%s">\n'
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
