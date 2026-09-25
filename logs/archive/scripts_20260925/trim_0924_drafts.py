#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0924 两份超标草稿裁剪：byd 30579-><=20000, weixiaoli 37142-><=20000
删块原则：① 与专属分类重复的整块 ② 内部重复块 ③ 汇总表同源冗余行。"""
import re, sys

def cut_between(html, start_marker, end_marker, keep_end=True):
    s = html.find(start_marker)
    assert s != -1, "start not found: " + start_marker[:60]
    e = html.find(end_marker, s + len(start_marker))
    assert e != -1, "end not found: " + end_marker[:60]
    if keep_end:
        return html[:s] + html[e:]
    return html[:s] + html[e + len(end_marker):]

def del_rows(html, keywords):
    """删除汇总表中 <tr> 含任一关键词的行"""
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
h = load(p)
orig = len(h)

# 1) 删板块二（销量与出海）
h = cut_between(h,
    '<div class="section">\n  <div class="section-title">板块二 · 销量与出海数据',
    '<div class="section">\n  <div class="section-title">板块三 · 智驾与技术')
# 2) 删板块四（具身智能）
h = cut_between(h,
    '<div class="section">\n  <div class="section-title">板块四 · 具身智能',
    '<div class="section">\n  <div class="section-title">板块五 · 校招窗口')
# 3) 重编号
h = h.replace('板块三 · 智驾与技术', '板块二 · 智驾与技术')
h = h.replace('板块五 · 校招窗口', '板块三 · 校招窗口')
# 4) 副标题去掉销量出口口径
h = h.replace('8月销44.02万辆、出口18.87万辆；', '')
# 5) 统计卡1 换成留存板块的口径
h = h.replace(
    '<div class="stat-box"><div class="count-badge">44.02万</div><div class="label">8月集团销量</div><div class="sub">出口 18.87 万辆、同比 ＋134.6%</div></div>',
    '<div class="stat-box"><div class="count-badge">2000座</div><div class="label">高速闪充站</div><div class="sub">年度目标提前 3 个月完成</div></div>')
# 6) 汇总表删 12 行
h, n1 = del_rows(h, ['8月车企销量解读', '8月车企销量大盘点', '小漠港「出货量」再刷新',
    '6154辆新能源车出口阿联酋', '单船出口数量刷新纪录', '中东出口37万辆', '珠江口两岸港口迎大单',
    '人形机器人进入工厂实测', '帕西尼启动上市辅导', '李想的投资野心', '整车亏到骨头里', '车企竞逐「造人」'])
save(p, h)
print("[byd] %d -> %d chars, table rows removed=%d" % (orig, len(h), n1))

# ---------------- weixiaoli ----------------
p = "content/weixiaoli-recruit.html"
h = load(p)
orig = len(h)

# 1) 板块一：删 蔚来 NIO Power 条目（补能新闻，与综合分类重叠）
h = cut_between(h,
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-purple">蔚来 · NIO Power',
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-green">小鹏')
# 2) 板块一：删 2027 届就业大盘条目（与 school-news/car-recruit 重叠）
h = cut_between(h,
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-accent">2027 届就业大盘',
    '\n  </div>\n\n  <div class="info-box">')
# 3) 板块一 h3 与 info-box 口径修正
h = h.replace('交付、补能、揽才、政策四条线在这三天同时落地',
              '交付与揽才两条线在这三天同时落地')
h = h.replace(
    '<p>这三天的信息指向三种不同的岗位增量：蔚来在扩<strong>制造与补能基础设施</strong>（换电站每天数站在建，对应电力电子、储能、结构、运维工程），小鹏在扩<strong>物理 AI 与飞控</strong>（算法、芯片、机器人、飞行汽车），理想在调<strong>产品与交付节奏</strong>（整车与智能硬件、供应链与智能制造）。三条线互不冲突，准备材料的侧重点完全不同，详见后文各专题。</p>',
    '<p>这两天的信息指向三种不同的岗位增量：蔚来在扩<strong>制造与交付体系</strong>（ES8 单车型月销过万，对应整车工程、制造工艺、质量、属性仿真），小鹏在扩<strong>物理 AI 与飞控</strong>（算法、芯片、机器人、飞行汽车），理想在调<strong>产品与交付节奏</strong>（整车与智能硬件、供应链与智能制造）。三条线互不冲突，准备材料的侧重点完全不同，详见后文各专题。</p>')
# 4) 板块二：删 乐道 L90 条目（产品资讯，与综合分类重叠）
h = cut_between(h,
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-purple">蔚来 · 乐道',
    '\n  </div>\n\n  <div class="highlight-box">')
# 5) 板块三：删 集团基本面条目（券商观点，与综合分类重叠）
h = cut_between(h,
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-green">集团基本面',
    '\n  </div>\n\n  <div class="tip-box">')
# 6) 板块三：删 低空赛道 warning-box（与板块六风险条内部重复）
s = h.find('  <div class="warning-box">')
e = h.find('\n</div>\n\n<div class="section">\n  <div class="section-title">板块四', s)
assert s != -1 and e != -1
h = h[:s] + '\n' + h[e + 1:]
# 7) 板块四：删 理想 i9 条目（保留 i6 条目，二者口径有重叠）
h = cut_between(h,
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-teal">理想 i9',
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-teal">理想 · 2026 款 i6')
# 8) 板块六：删 行业基本盘/换轨条目（与综合分类重叠）
h = cut_between(h,
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-accent">行业基本盘',
    '<div class="news-item">\n      <div class="news-meta">\n        <span class="tag tag-info">策略')
# 9) 板块五（岗位卡，与板块三/四内部重复）整块删除，板块六 -> 板块五
h = cut_between(h,
    '<div class="section">\n  <div class="section-title">板块五 · 重点推荐岗位卡',
    '<div class="section">\n  <div class="section-title">板块六')
h = h.replace('板块六 · 投递策略与风险提示', '板块五 · 投递策略与风险提示')
# 10) 汇总表删行
h, n2 = del_rows(h, ['22 座充换电站', '零碳离网光储换电站', 'NIO Power 上新 9 座',
    '乐道 L90 推出星瀚金辉', '乐道 L90 上线星瀚金辉',
    '财中 ETF 风向标', 'The Road to Autonomy', '「探索者计划」全球校招',
    '36.98 万，理想这次真的把旗舰纯电', '车研职场速递',
    '赛道规则重塑', '低空经济逆势走强',
    '2027 届高校毕业生校园招聘月活动启动', '「金秋启航」校园招聘月', '9000+ 场双选会'])
save(p, h)
print("[weixiaoli] %d -> %d chars, table rows removed=%d" % (orig, len(h), n2))
