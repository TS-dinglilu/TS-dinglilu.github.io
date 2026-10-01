#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复历史报告里的两类「文本性」瑕疵（幂等，可反复运行）：

1. 标题日期错位
   ahut-campus/report_20260805.html 的 <title> 写成「2026年8月4日」（应为 8月5日）——
   当天的构建脚本日期算错或模板日期没跟文件名走。

2. 标题/正文首行混入「六大」前缀
   73 份「地区类」报告（20260925 起）的 <title> 与 <h1> 出现形如
   「六大安徽汽车机械日报」的多余「六大」，来源是当时为「六大XX」聚合主题写的
   正文被当成日常正文套进模板，前缀没清掉。站点日常报没有「六大」这个概念。

做法：以文件名为唯一日期真源，重建 <title>；去掉 <h1> 开头的裸「六大」。
只动 <title> 与 <h1> 的纯文本，不碰正文其它内容。

用法:
  python scripts/fix_titles.py --check
  python scripts/fix_titles.py
"""
import argparse
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_NAME = "TS-dinglilu 自动化日报"

# 分类目录 -> 标准日报名（与 tail_template.CATEGORY_NAMES 保持一致）
CATEGORY_NAMES = {
    "car-recruit": "车企招聘日报", "mechanical-recruit": "机械招聘日报",
    "school-news": "校园新闻日报", "drone-research": "无人机科研日报",
    "ahut-campus": "安工大校园日报", "byd-recruit": "比亚迪招聘日报",
    "chery-recruit": "奇瑞招聘日报", "chery-insider": "奇瑞职场口碑日报",
    "geely-recruit": "吉利招聘日报", "xiaomi-recruit": "小米汽车招聘日报",
    "weixiaoli-recruit": "蔚小理招聘日报", "traditional-auto": "传统车企招聘日报",
    "supply-chain-recruit": "车企供应链招聘日报", "research-institute": "科研院所招聘日报",
    "future-planning": "未来规划日报",
    "xuzhou-news": "徐州汽车机械日报", "nanjing-news": "南京汽车机械日报",
    "shanghai-news": "上海汽车机械日报", "hangzhou-news": "杭州汽车机械日报",
    "jiangzhehu-news": "江浙沪汽车机械日报", "hefei-news": "合肥汽车机械日报",
    "anhui-news": "安徽汽车机械日报", "jiangsu-news": "江苏汽车机械日报",
    "shenzhen-news": "深圳汽车机械日报",
    "xuzhou-recruit": "徐州招聘日报", "nanjing-recruit": "南京招聘日报",
    "shanghai-recruit": "上海招聘日报", "hangzhou-recruit": "杭州招聘日报",
    "jiangzhehu-recruit": "江浙沪招聘日报", "hefei-recruit": "合肥招聘日报",
    "anhui-recruit": "安徽招聘日报", "jiangsu-recruit": "江苏招聘日报",
    "shenzhen-recruit": "深圳招聘日报",
    "company-reputation": "企业口碑日报",
}


def norm_title(cat, date8):
    name = CATEGORY_NAMES.get(cat, cat)
    y, mo, da = date8[:4], int(date8[4:6]), int(date8[6:8])
    return "%s - %s年%d月%d日" % (name, y, mo, da)


def fix_file(path, dry=True):
    cat = os.path.basename(os.path.dirname(path))
    date8 = os.path.basename(path)[7:15]
    s = open(path, encoding="utf-8").read()
    orig = s
    notes = []

    # --- 1) <title> 重建 ---
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    want = norm_title(cat, date8)
    if m:
        cur = m.group(1).strip()
        # 只有当「日期与文件名不符」或「带六大前缀」时才改，避免动正常标题
        y, mo, da = date8[:4], int(date8[4:6]), int(date8[6:8])
        date_ok = ("%s年%d月%d日" % (y, mo, da)) in cur or ("%s-%02d-%02d" % (y, mo, da)) in cur
        if ("六大" in cur) or (not date_ok):
            s = s[:m.start(1)] + want + s[m.end(1):]
            notes.append("title: %r → %r" % (cur, want))

    # --- 2) <h1> 去掉开头的「六大」 ---
    h = re.search(r"<h1([^>]*)>(.*?)</h1>", s, re.S)
    if h and "六大" in h.group(2):
        inner = h.group(2)
        cleaned = re.sub(r"^\s*六大\s*", "", inner, count=1)
        if cleaned != inner:
            s = s[:h.start(2)] + cleaned + s[h.end(2):]
            notes.append("h1 去「六大」")

    # --- 3) og:title 同步 ---
    m = re.search(r'(<meta property="og:title" content=")([^"]*)(")', s)
    if m and "六大" in m.group(2):
        s = s[:m.start(2)] + m.group(2).replace("六大", "", 1) + s[m.end(2):]
        notes.append("og:title 去「六大」")

    if s == orig:
        return False, []
    if not dry:
        open(path, "w", encoding="utf-8", newline="").write(s)
    return True, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    n = 0
    for d in sorted(CATEGORY_NAMES):
        for p in sorted(glob.glob(os.path.join(ROOT, d, "report_*.html"))):
            changed, notes = fix_file(p, dry=args.check)
            if changed:
                n += 1
                print("%-4s %-44s %s" % ("FIX" if not args.check else "TODO",
                                         os.path.relpath(p, ROOT).replace("\\", "/"),
                                         " | ".join(notes)))
    print("\n%s: %d 份报告" % ("待修复" if args.check else "已修复", n))


if __name__ == "__main__":
    main()
