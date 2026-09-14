#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全站视觉统一：把历史报告的结尾区块统一成标准结构（见 tail_template.py）。

原理
----
定位「尾部区间」= 从文件末尾窗口内最早出现的尾部标记（评论区 / 页脚）到 </body>，整段替换为
标准尾部。区间内原有的 </main> 保留；区间内多余的 </div>（闭合正文容器）折算成等量的前置
</div> 补偿，保证替换前后 <div> 总数配平。区间内若含真实「信息来源汇总」板块，则原样提取保留
（若其外层是页脚标签，降级为 <div class="section"> 避免双页脚）。

每份文件替换后立即校验（结尾 </html>、<div> 配平、单一 </body>/</html>、含 giscus），
不通过则跳过不写。重复执行不改变已统一的文件（幂等）。

用法:
  python scripts/unify_style.py --dry-run        # 预演，列出每个文件的判断
  python scripts/unify_style.py                  # 执行
  python scripts/unify_style.py --show <path>    # 预览单个文件替换后的尾部
"""
import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_report     # noqa: E402  GISCUS_SCRIPT
import tail_template as TT  # noqa: E402  标准尾部唯一真源

NAMES = {
    "car-recruit": "车企招聘日报",
    "mechanical-recruit": "机械招聘日报",
    "school-news": "校园新闻日报",
    "drone-research": "无人机科研日报",
    "ahut-campus": "安工大校园日报",
    "byd-recruit": "比亚迪招聘日报",
    "chery-recruit": "奇瑞招聘日报",
    "geely-recruit": "吉利招聘日报",
    "xiaomi-recruit": "小米汽车招聘日报",
    "weixiaoli-recruit": "蔚小理招聘日报",
    "traditional-auto": "传统车企招聘日报",
    "research-institute": "科研院所招聘日报",
    "future-planning": "未来规划日报",
}

# 正文里出现的「评论区」字样属于内容，不作标记 —— 只用注释 / 容器 / 页脚标签。
TAIL_MARKERS = TT.TAIL_MARKERS
SEARCH_WINDOW = TT.SEARCH_WINDOW
CMT_TAIL_RE = re.compile(r"<!--[^>]*(?:giscus|评论区|comments?)[^>]*-->", re.I)

_DIV_RE = re.compile(r"<div\b|</div>")
PREVIEW = {"new": None, "tail": None}


def match_div(s, start):
    """s[start] 处是 '<div'，返回配对 '</div>' 之后的偏移；失败返回 -1。"""
    depth = 0
    for m in _DIV_RE.finditer(s, start):
        if m.group(0) == "</div>":
            depth -= 1
            if depth == 0:
                return m.end()
        else:
            depth += 1
    return -1


def match_tag(s, start, tag):
    """s[start] 处是 '<tag'，返回配对 '</tag>' 之后的偏移；失败返回 -1。"""
    ore = re.compile(r"<%s\b" % tag)
    cre = re.compile(r"</%s>" % tag)
    depth, pos = 0, start
    while True:
        mo, mc = ore.search(s, pos), cre.search(s, pos)
        if mo is None and mc is None:
            return -1
        if mo is not None and (mc is None or mo.start() < mc.start()):
            depth += 1
            pos = mo.end()
        else:
            depth -= 1
            if depth == 0:
                return mc.end()
            pos = mc.end()


def find_source_block(seg):
    """在尾部区间内定位「信息来源」板块，返回 (start, end)；找不到返回 None。

    优先：若「信息来源」位于旧页脚（footer / .footer / .footer-info）内，则整段保留该页脚，
          以免连同页脚内的其它正文（如「今日亮点」摘要、归档链接）一起被删。
    否则：取距「信息来源」字样最近的块起点。
    """
    k = seg.find("信息来源")
    if k < 0:
        return None
    for w in TT.FOOTER_WRAPPERS:
        q = seg.rfind(w, 0, k)
        while q >= 0:
            if seg.startswith("<footer", q):
                e = seg.find("</footer>", q)
                end = e + len("</footer>") if e >= 0 else -1
            else:
                end = match_div(seg, q)
            if end > k:
                return (q, end)
            q = seg.rfind(w, 0, q)
    cands = []
    for p in TT.SRC_BLOCK_STARTS:
        i = seg.rfind(p, 0, k)
        if i >= 0:
            cands.append((k - i, i))
        j = seg.find(p, k)
        if j >= 0:
            cands.append((j - k, j))
    if not cands:
        return None
    _, s0 = min(cands, key=lambda x: x[0])
    if seg.startswith("<footer", s0):
        e = seg.find("</footer>", s0)
        return (s0, e + len("</footer>")) if e >= 0 else None
    e = match_div(seg, s0)
    return (s0, e) if e >= 0 else None


def to_start(s, p, floor):
    """把命中位置 p 回退到所属标签起点，再回退掉该行的首部缩进。"""
    lt = s.rfind("<", max(floor, p - 160), p + 1)
    if lt != -1:
        p = lt
    q = p
    while q > 0 and s[q - 1] in " \t":
        q -= 1
    if q == 0 or s[q - 1] == "\n":
        p = q
    return p


def expand_wrapper(s, p, floor):
    """若评论/页脚被外层 <div class="section"> / <section> 包裹（其间只有标题、注释、空白），
    则把起点前移到该外层容器，避免留下孤立标题。"""
    while True:
        cand = None
        for pat in ('<div class="section"', '<div class="section ', "<section"):
            q = s.rfind(pat, floor, p)
            if q >= 0 and (cand is None or q > cand):
                cand = q
        if cand is None:
            return p
        end = match_div(s, cand) if s.startswith("<div", cand) else match_tag(s, cand, "section")
        if end < 0 or end < p:
            return p
        between = s[s.find(">", cand) + 1:p]
        t = CMT_TAIL_RE.sub("", between)
        t = re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", t, flags=re.S)
        t = re.sub(r'<div class="section-(?:title|label)"[^>]*>.*?</div>', "", t, flags=re.S)
        t = re.sub(r'<p class="(?:section-desc|comments-desc)"[^>]*>.*?</p>', "", t, flags=re.S)
        t = re.sub(r"<span[^>]*>.*?</span>", "", t, flags=re.S)
        if t.strip():
            return p
        p = cand


def locate_start(s, win_start, body_end):
    """返回尾部区间起点（绝对偏移），失败返回 None。"""
    win = s[win_start:body_end]
    cands = []
    for mk in TAIL_MARKERS:
        i = win.find(mk)
        if i != -1:
            cands.append(i)
    for m in CMT_TAIL_RE.finditer(win):
        cands.append(m.start())
    if not cands:
        return None
    start = to_start(s, win_start + min(cands), win_start)
    start = expand_wrapper(s, start, win_start)
    return to_start(s, start, win_start)


def transform(path, cat, dry=False):
    """返回 (状态, 说明)。状态: 'ok' / 'skip'。"""
    s = open(path, encoding="utf-8").read()
    mm = re.search(r"report_(\d{4})(\d{2})(\d{2})\.html", os.path.basename(path))
    if not mm:
        return "skip", "文件名无法解析日期"
    y, m, d = int(mm.group(1)), int(mm.group(2)), int(mm.group(3))

    body_end = s.rfind("</body>")
    if body_end == -1:
        return "skip", "无 </body>"
    win_start = max(0, body_end - SEARCH_WINDOW)

    start = locate_start(s, win_start, body_end)
    if start is None:
        return "skip", "窗口内找不到尾部标记"

    segment = s[start:body_end]
    delta = segment.count("<div") - segment.count("</div>")
    has_main = "</main>" in segment

    # 提取并保留真实「信息来源汇总」板块
    blk = ""
    found = find_source_block(segment)
    if found:
        cand = segment[found[0]:found[1]]
        if re.search(r"<table[\s>]|<ol[\s>]|class=\"sources\"", cand):
            if cand.count("<div") != cand.count("</div>"):
                return "skip", "来源板块 <div> 不平衡，保守跳过"
            if cand.count("<footer") != cand.count("</footer>"):
                return "skip", "来源板块 footer 不平衡，保守跳过"
            blk = TT.demote_footer_wrapper(cand)

    # 计算 <div> 补偿
    std0 = TT.build_tail(NAMES.get(cat, cat), y, m, d, build_report.GISCUS_SCRIPT,
                         has_main, 0, blk)
    need = (std0.count("<div") - std0.count("</div>")) - delta
    extra_close = need if need > 0 else 0
    extra_open = -need if need < 0 else 0

    std = TT.build_tail(NAMES.get(cat, cat), y, m, d, build_report.GISCUS_SCRIPT,
                        has_main, extra_close, blk)
    if extra_open:
        std = std + "\n" + "<div>\n" * extra_open

    # 清理尾部区间「之前」残留的旧评论区 / 内联 giscus 脚本（含被误放进 <head> 的情况）
    prefix, n_rm = TT.strip_comment_artifacts(s[:start])
    new_s = prefix + std

    # —— 校验 ——
    if not new_s.rstrip().endswith("</html>"):
        return "skip", "替换后结尾异常"
    if new_s.count("<div") != new_s.count("</div>"):
        return "skip", "替换后 <div> 不平衡 %+d" % (new_s.count("<div") - new_s.count("</div>"))
    if "giscus.app" not in new_s:
        return "skip", "替换后无 giscus"
    if new_s.count("</body>") != 1 or new_s.count("</html>") != 1:
        return "skip", "body/html 标签数量异常"

    PREVIEW["new"], PREVIEW["tail"] = new_s, std
    if new_s == s:
        return "skip", "已是标准尾部"

    note = "区间 %d 字符, 原div净%+d%s, 补%s%s%s" % (
        len(segment), delta, " 含</main>" if has_main else "",
        ("%d个</div>" % extra_close) if extra_close else ("%d个<div>" % extra_open if extra_open else "无"),
        (", 保留来源块 %d 字符" % len(blk)) if blk else "",
        (", 清理残留 %d 处" % n_rm) if n_rm else "")
    if not dry:
        open(path, "w", encoding="utf-8").write(new_s)
    return "ok", note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--show", help="预览单个文件（相对 repo 的路径），不改文件")
    args = ap.parse_args()

    if args.show:
        f = os.path.join(ROOT, args.show.replace("/", os.sep))
        st, note = transform(f, os.path.basename(os.path.dirname(f)), dry=True)
        print("[%s] %s\n%s" % (st, args.show, note))
        if st == "ok" and PREVIEW.get("new"):
            new = PREVIEW["new"]
            lines = new.rstrip().splitlines()
            shown = lines if len(lines) <= 80 else lines[-(80 - 12):]
            print("\n--- 替换后文件尾部 ---")
            for l in shown:
                print("  " + l)
        return 0

    files = sorted(glob.glob(os.path.join(ROOT, "*", "report_*.html")))
    ok, skipped = [], []
    for f in files:
        cat = os.path.basename(os.path.dirname(f))
        if cat not in NAMES:
            continue
        st, note = transform(f, cat, dry=args.dry_run)
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        (ok if st == "ok" else skipped).append((rel, note))

    print("=== 将被统一（%d 份）===" % len(ok) if args.dry_run else "已统一 %d 份报告" % len(ok))
    if args.dry_run:
        for rel, note in ok:
            print("  %-48s %s" % (rel, note))
    if skipped:
        print("\n=== 跳过（%d 份）===" % len(skipped))
        for rel, note in skipped:
            print("  %-48s %s" % (rel, note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
