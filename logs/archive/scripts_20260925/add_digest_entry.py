# -*- coding: utf-8 -*-
"""一次性脚本：为「周记月记年记」板块加入口。
1. 23 个分类归档页 back-link 后插入 digest 入口行（幂等，marker: digest-entry）
2. 主页：筛选标签加「汇总」、卡片列表加 digest 卡、底部导航加链接、统计 23→24
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import tail_template  # noqa: E402

ENTRY_HTML = (
    '<a href="https://ts-dinglilu.github.io/digest/" class="back-link digest-entry" '
    'target="_blank">📊 周记 · 月记 · 年记（站级汇总） →</a>\n'
)

DIGEST_CARD = '''
      <a href="https://ts-dinglilu.github.io/digest/" class="auto-card" target="_blank" data-cat="digest" style="animation-delay:1.15s">
        <div class="auto-icon" style="background:rgba(52,211,153,0.12)">📊</div>
        <h3>周记 · 月记 · 年记</h3>
        <p>站级汇总报告：每周/每月/每年结束时自动汇总全站 23 个分类的动态要点与数据统计，可按招聘、地区、校园科研、规划标签筛选。</p>
        <div class="auto-updated">最新 <b>周记 W38</b> · 每周一更新</div>
        <div class="auto-meta">
          <span class="auto-badge active">运行中</span>
          <span class="auto-badge early">每周 / 月 / 年</span>
          <span class="auto-link">访问 →</span>
        </div>
      </a>
'''


def patch_archive(cat):
    p = os.path.join(ROOT, cat, "index.html")
    if not os.path.exists(p):
        print("[SKIP] %s 无归档页" % cat)
        return
    s = io.open(p, encoding="utf-8").read()
    if "digest-entry" in s:
        print("[SKIP] %s 已有入口" % cat)
        return
    m = re.search(r'<a href="[^"]*" class="back-link">[^<]*</a>\n', s)
    assert m, "%s 找不到 back-link" % cat
    s = s[:m.end()] + ENTRY_HTML + s[m.end():]
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("[OK] %s 入口已加" % cat)


def patch_homepage():
    p = os.path.join(ROOT, "index.html")
    s = io.open(p, encoding="utf-8").read()

    if 'data-cat="digest"' in s:
        print("[SKIP] 主页已有 digest 卡")
        return

    # 1) 筛选标签「地区」后加「汇总」
    m = re.search(r'<div class="filter-tab" onclick="setFilter\(&#39;region&#39;|<div class="filter-tab" onclick="setFilter\(\'region\'[^>]*>地区</div>', s)
    assert m, "主页找不到地区筛选标签"
    s = s[:m.end()] + '\n      <div class="filter-tab" onclick="setFilter(\'digest\', this)">汇总</div>' + s[m.end():]

    # 2) 地区最后一张卡（深圳）后插入 digest 卡
    m = re.search(r'data-cat="region"[^>]*>.*?</a>\s*</a>\s*\n', s, re.S)
    if not m:
        m = re.search(r'shenzhen-news/" class="auto-card".*?</a>\n', s, re.S)
    assert m, "主页找不到地区卡片结尾"
    s = s[:m.end()] + DIGEST_CARD + s[m.end():]

    # 3) 底部导航：深圳链接后加「汇总」
    m = re.search(r'<a href="https://ts-dinglilu\.github\.io/shenzhen-news/" target="_blank">深圳</a>', s)
    assert m, "主页找不到底部导航深圳链接"
    s = s[:m.end()] + '\n      <a href="https://ts-dinglilu.github.io/digest/" target="_blank">周记月记年记</a>' + s[m.end():]

    # 4) 统计数字 23 → 24（简介、stat-num、SYSTEMS LIVE 徽章里的 23）
    s2 = s.replace("23 个自动化日报", "24 个板块（23 日报 + 周记月记年记）")
    s2 = re.sub(r'(<div class="stat-num">)23(</div>)', r"\g<1>24\g<2>", s2, count=1)
    s2 = s2.replace("SYSTEMS LIVE", "SYSTEMS LIVE")  # 徽章文本若含 23 由下面处理
    s2 = re.sub(r"(\bSYSTEMS LIVE[^<]*)23", r"\g<1>24", s2)

    io.open(p, "w", encoding="utf-8", newline="\n").write(s2)
    print("[OK] 主页已加 digest 卡 + 汇总标签 + 导航链接")


def main():
    cats = list(tail_template.CATEGORY_NAMES.keys())
    assert len(cats) == 23, "分类数异常: %d" % len(cats)
    for c in cats:
        patch_archive(c)
    patch_homepage()
    print("DONE")


if __name__ == "__main__":
    main()
