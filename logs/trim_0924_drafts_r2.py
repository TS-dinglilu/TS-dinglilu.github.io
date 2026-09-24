#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0924 草稿裁剪第二轮：删内部重复条目，byd 22317-><=20000, weixiaoli 24120-><=20000"""
import re

def cut_between(html, start_marker, end_marker):
    s = html.find(start_marker)
    assert s != -1, "start not found: " + start_marker[:60]
    e = html.find(end_marker, s + len(start_marker))
    assert e != -1, "end not found: " + end_marker[:60]
    return html[:s] + html[e:]

def del_rows(html, keywords):
    removed = 0
    for kw in keywords:
        m = re.search(r"<tr><td>[^<]*%s[^<]*</td>.*?</tr>\s*" % re.escape(kw), html)
        if m:
            html = html[:m.start()] + html[m.end():]
            removed += 1
    return html, removed

def load(p): return open(p, encoding="utf-8").read()
def save(p, h): open(p, "w", encoding="utf-8", newline="\n").write(h)

# ---------------- byd ----------------
p = "content/byd-recruit.html"
h = load(p); orig = len(h)
# 1) 板块一：删「上市细节」条目（权益/座舱营销细节，岗位相关性最低）
h = cut_between(h,
    '<div class="news-item">\n      <div class="news-meta"><span class="tag tag-byd">上市细节</span>',
    '<div class="news-item">\n      <div class="news-meta"><span class="tag tag-byd">海狮 08</span>')
# 2) 板块二：删「智驾下放」条目（配置综合，与板块一重复）
h = cut_between(h,
    '<div class="news-item">\n      <div class="news-meta"><span class="tag tag-byd">智驾下放</span>',
    '  </div>\n</div>\n\n<div class="section">\n  <div class="section-title">板块三 · 校招窗口')
h, n = del_rows(h, ['中国财富网', '比亚迪新车官宣：纯电续航1100km，9月23日即将上市', '车研晨报'])
save(p, h)
print("[byd r2] %d -> %d chars, rows=%d" % (orig, len(h), n))

# ---------------- weixiaoli ----------------
p = "content/weixiaoli-recruit.html"
h = load(p); orig = len(h)
# 1) 板块二：删 ES8 销量结构条目（数据与板块一 ES8 条目重复）
h = cut_between(h,
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-purple">蔚来 · 销量结构</span>',
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-purple">蔚来 · 27 届校招</span>')
# 2) 板块三：删 量产与订单条目（与汇天时间线条目口径重叠）
h = cut_between(h,
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-green">量产与订单</span>',
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-green">在招岗位 · 逐条读</span>')
# 3) 板块四：删 财务基本面条目（数字已并入板块五风险提示）
h = cut_between(h,
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-teal">理想 · 财务基本面</span>',
    '\n  </div>\n\n  <div class="note-box">')
h, n = del_rows(h, ['坠机 50 多次', '低空经济 eVTOL 企业人才画像', '小鹏汇天企业数据与融资历程',
                    "Li Auto's i9 Launch"])
save(p, h)
print("[weixiaoli r2] %d -> %d chars, rows=%d" % (orig, len(h), n))
