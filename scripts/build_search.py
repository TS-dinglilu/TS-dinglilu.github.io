#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成全站搜索索引 search-index.json。

为什么需要：站点有 798+ 份日报，此前唯一的检索方式是「进某个分类归档页慢慢翻」。
内容完全静态、没有服务端，所以采用「构建期生成索引 + 浏览器端检索」的方案，
零后端成本，且不引入第三方搜索服务（不泄露数据、不依赖外网）。

索引刻意**不放正文全文**：否则 798 份 × 上万字会让 JSON 膨胀到数 MB，
首次打开搜索页要下载好几 MB，得不偿失。改为抽取最有检索价值的字段：
板块名(section-title)、条目标题(h3)、摘要、分类名、日期。
用户搜「比亚迪」「公积金」「徐工」这类关键词时，靠标题/板块即可命中。

用法:
  python scripts/build_search.py            # 生成 assets/search-index.json
  python scripts/build_search.py --check    # 只统计不写盘
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import re
import sys
from html import unescape

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail_template  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_BASE = getattr(tail_template, "SITE_BASE", "https://ts-dinglilu.github.io")
OUT = os.path.join(ROOT, "assets", "search-index.json")

# —— 全站搜索入口注入（幂等，marker 包裹）——
ENTRY_START = "<!-- search-entry:start -->"
ENTRY_END = "<!-- search-entry:end -->"
SEARCH_URL = "/search.html"

SKIP_DIRS = {".git", "logs", "scripts", "content", "assets", ".github",
             ".workbuddy", "__pycache__", "backups"}

MAX_TOPICS = 10      # 每份报告最多收录多少条 h3 条目作为检索关键词
TOPIC_LEN = 26       # 单条目截断长度（前 26 字通常已含核心名词）
SUMMARY_LEN = 100    # 摘要长度
# 板块名多为「板块一 · 本期导览：……」这类每期雷同的句式，检索区分度低于 h3 条目，
# 且与 h3 高度重叠，因此只留少量作为兜底命中。
MAX_SECS = 3


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def get_body_zone(html: str) -> str:
    """取正文区域：优先 <main>，没有则退到 <body>（并剔除 script/style）。"""
    m = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    zone = m.group(1) if m else html
    zone = re.sub(r"<script.*?</script>", " ", zone, flags=re.S)
    zone = re.sub(r"<style.*?</style>", " ", zone, flags=re.S)
    return zone


def pick_summary(zone: str) -> str:
    """摘要：取第一个「有实质内容」的段落。

    早先版本限定在第一个 <div class="section"> 内找 <p>，但部分报告的板块
    用的是 h3+p 之外的结构（如深度档案注入块），导致取到空字符串。
    改为在整段正文里找第一个长度 > 40 的段落，既能跳过页眉重复标题噪声，
    又不会因为某块结构特殊而落空；最后保留「纯文本兜底」保证绝不为空。
    """
    paras = [strip_tags(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", zone, re.S)]
    text = ""
    for p in paras:
        if len(p) > 40:
            text = p
            break
    if not text:
        for p in paras:
            if len(p) > 15:
                text = p
                break
    if not text:
        text = strip_tags(zone)
    if len(text) > SUMMARY_LEN:
        return text[:SUMMARY_LEN].rstrip("，。、；：,;: ") + "…"
    return text


def extract(rel: str) -> dict | None:
    """从单个报告/汇总页抽取索引条目。"""
    parts = rel.split("/")
    category = parts[0] if len(parts) > 1 else ""
    base = os.path.basename(rel)
    if category == "digest":
        category = "digest"

    m = re.search(r"report_(\d{8})\.html", base)
    if m:
        d = datetime.datetime.strptime(m.group(1), "%Y%m%d")
        date = d.strftime("%Y-%m-%d")
        kind = "report"
    else:
        m2 = re.search(r"(weekly_\d{4}W\d{2}|monthly_\d{4}M\d{2}|yearly_\d{4})", base)
        if not m2:
            return None
        date = _digest_date(m2.group(1))
        kind = "digest"

    html = open(rel, encoding="utf-8").read()
    zone = get_body_zone(html)

    # 板块名（<div class="section-title"> 内的文本）
    secs, seen = [], set()
    for t in re.findall(r'<div class="section-title"[^>]*>(.*?)</div>', zone, re.S):
        t = strip_tags(t)
        if t and t not in seen and len(t) < 60:
            seen.add(t)
            secs.append(t)

    # 条目标题（h2/h3）
    topics, seen_t = [], set()
    for tag in ("h2", "h3"):
        for t in re.findall(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), zone, re.S):
            t = strip_tags(t)
            if not t or t in seen_t or len(t) < 4:
                continue
            seen_t.add(t)
            topics.append(t[:TOPIC_LEN])
    topics = topics[:MAX_TOPICS]

    cat_name = tail_template.CATEGORY_NAMES.get(category, "汇总" if kind == "digest" else category)
    return {
        "c": category,
        "cn": cat_name,
        "d": date,
        "u": "%s/%s" % (SITE_BASE, rel),
        "s": pick_summary(zone),
        "sec": secs[:MAX_SECS],
        "t": topics,
    }


def _digest_date(token: str) -> str:
    """从 digest 文件名取代表日期。注意「weekly_」是 7 个字符（含下划线），
    年份从下标 7 起、周数从下标 12 起 —— 早期版本按下标 6 切会把 '_' 算进年份。"""
    if token.startswith("weekly"):        # weekly_2026W38
        y, w = token[7:11], int(token[12:14])
        try:
            # ISO 周：%W 以「周一是第几天」计算，够用于排序/展示
            d = datetime.datetime.strptime("%s-W%02d-1" % (y, w), "%Y-W%W-%w")
            return d.strftime("%Y-%m-%d")
        except ValueError:
            return "%s-01-01" % y
    if token.startswith("monthly"):       # monthly_2026M09（"monthly_" 是 8 字符）
        return "%s-%s-01" % (token[8:12], token[13:15])
    if token.startswith("yearly"):        # yearly_2026
        return "%s-01-01" % token[7:11]
    return ""


def build(write=True):
    rels = []
    for p in sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        if rel.split("/")[0] in SKIP_DIRS:
            continue
        if os.path.basename(rel) == "index.html":
            continue
        rels.append(rel)

    items = []
    for rel in rels:
        try:
            e = extract(rel)
        except Exception as e_:  # noqa: BLE001  单份失败不应拖垮全站索引
            print("  [WARN] 跳过 %s: %s" % (rel, e_))
            continue
        if e:
            items.append(e)

    items.sort(key=lambda x: (x["d"], x["c"]), reverse=True)
    payload = {
        "v": 1,
        "generated": datetime.date.today().isoformat(),
        "total": len(items),
        "items": items,
    }
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    size = len(blob.encode("utf-8"))
    print("索引条目 %d 条，JSON %d 字节（约 %.0f KB）" % (len(items), size, size / 1024))
    if write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "w", encoding="utf-8", newline="").write(blob)
        print("[OK] 已写入 %s" % OUT)
    return payload


def _replace_marked(html: str, block: str) -> str:
    """marker 区间整体替换；不存在 marker 则视为未注入。返回 (新html, 是否已有marker)。"""
    i = html.find(ENTRY_START)
    if i < 0:
        return html, False
    j = html.find(ENTRY_END, i)
    if j < 0:  # 有头无尾视为损坏，清掉重注
        return html.replace(ENTRY_START, ""), False
    return html[:i] + block + html[j + len(ENTRY_END):], True


def _inject(html: str, anchor: str, block: str, after: bool = True) -> tuple[str, bool]:
    """在 anchor 处注入搜索入口（marker 包裹，幂等）。返回 (新html, 是否有改动)。"""
    block = ENTRY_START + "\n" + block.strip() + "\n" + ENTRY_END
    html, had = _replace_marked(html, block)
    if had:
        return html, True  # 已注入（本次等于刷新内容）
    i = html.find(anchor)
    if i < 0:
        return html, False
    pos = i + len(anchor) if after else i
    return html[:pos] + "\n" + block + "\n" + html[pos:], True


def inject_entries() -> int:
    """给主页、34 个分类归档页、404 页注入「全站搜索」入口。

    搜索页做得再好，没有入口就是死的。三类页面用各自的既有锚点：
      - 归档页：back-link 之后（与「返回主页」并排，视觉自然）
      - 主页：AUTOMATION PROJECTS 注释之前（hero 与内容区之间，最显眼处）
      - 404：links 按钮组里 GitHub 之后（迷路用户正需要搜索）
    """
    n = 0
    arch = ('<a class="back-link" href="%s" style="margin-left:14px">'
            '🔍 全站搜索</a>' % SEARCH_URL)
    for cat in tail_template.CATEGORY_NAMES:
        p = os.path.join(ROOT, cat, "index.html")
        if not os.path.exists(p):
            continue
        html = open(p, encoding="utf-8").read()
        anchor = '<a href="%s/" class="back-link">← 返回主页</a>' % SITE_BASE
        new, ok = _inject(html, anchor, arch)
        if ok and new != html:
            open(p, "w", encoding="utf-8", newline="").write(new)
            n += 1
        elif ok and new == html:
            n += 1  # 已注入且内容一致

    home_block = (
        '<div style="text-align:center;margin:22px 0 0">'
        '<a href="%s" style="display:inline-block;background:linear-gradient(135deg,#00d4ff,#818cf8);'
        'color:#0a0e1a;font-weight:700;border-radius:999px;padding:13px 32px;text-decoration:none;'
        'font-size:1rem;box-shadow:0 8px 24px rgba(0,212,255,.18)">🔍 全站搜索 800+ 期日报</a>'
        "</div>" % SEARCH_URL)
    p = os.path.join(ROOT, "index.html")
    if os.path.exists(p):
        html = open(p, encoding="utf-8").read()
        new, ok = _inject(html, "<!-- AUTOMATION PROJECTS -->", home_block, after=False)
        if ok and new != html:
            open(p, "w", encoding="utf-8", newline="").write(new)
        n += 1 if ok else 0

    e404 = os.path.join(ROOT, "404.html")
    if os.path.exists(e404):
        html = open(e404, encoding="utf-8").read()
        anchor = '<a href="https://github.com/TS-dinglilu" class="btn">GitHub</a>'
        block = '<a href="%s" class="btn">🔍 全站搜索</a>' % SEARCH_URL
        new, ok = _inject(html, anchor, block)
        if ok and new != html:
            open(e404, "w", encoding="utf-8", newline="").write(new)
        n += 1 if ok else 0
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只统计不写盘")
    ap.add_argument("--no-inject", action="store_true", help="跳过搜索入口注入")
    a = ap.parse_args()
    build(write=not a.check)
    if not a.check and not a.no_inject:
        cnt = inject_entries()
        print("[OK] 搜索入口注入/刷新 %d 页（主页 + 归档页 + 404）" % cnt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
