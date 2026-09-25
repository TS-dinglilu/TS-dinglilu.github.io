#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主页新增「地区」分组（与招聘同级）：筛选标签 + 9 卡片 + 页脚导航 + 统计数字 23。"""
import io

P = "index.html"
h = io.open(P, encoding="utf-8").read()
orig = len(h)
assert "/guard.js" in h

# 1) 筛选标签加「地区」
old_tab = '<div class="filter-tab" onclick="setFilter(\'personal\', this)" data-page-node-id="wBxz8fieCr7k2lFgLtqP2i">规划</div>'
assert old_tab in h
h = h.replace(old_tab, old_tab + '\n        <div class="filter-tab" onclick="setFilter(\'region\', this)">地区</div>')

# 2) 九张地区卡片，插在 auto-grid 结束前（future-planning 卡之后）
CARDS = [
    ("xuzhou-news", "🏗️", "rgba(0,212,255,0.12)", "徐州汽车机械日报", "0.70s",
     "徐工集团与徐州工程机械产业集群最新动态，家乡本地汽车与机械产业新闻跟踪。"),
    ("nanjing-news", "🏙️", "rgba(129,140,248,0.12)", "南京汽车机械日报", "0.75s",
     "南京汽车与机械制造产业动态：长安汽车南京基地、南汽集团、LG 新能源滨江等要闻。"),
    ("shanghai-news", "🌃", "rgba(255,179,71,0.12)", "上海汽车机械日报", "0.80s",
     "上汽集团、特斯拉上海超级工厂与上海高端装备制造产业新闻。"),
    ("hangzhou-news", "🛶", "rgba(34,211,160,0.12)", "杭州汽车机械日报", "0.85s",
     "吉利控股、零跑科技等杭州汽车产业与智能制造企业最新动态。"),
    ("jiangzhehu-news", "🌊", "rgba(0,212,255,0.12)", "江浙沪汽车机械日报", "0.90s",
     "长三角（江浙沪）一体化汽车与机械产业要闻，跨区域产业协同与布局跟踪。"),
    ("hefei-news", "🔬", "rgba(34,211,160,0.12)", "合肥汽车机械日报", "0.95s",
     "蔚来、江淮、大众安徽与合肥「新能源汽车之都」建设最新动态。"),
    ("anhui-news", "🏭", "rgba(251,146,60,0.12)", "安徽汽车机械日报", "1.00s",
     "奇瑞、江淮、蔚来等安徽汽车产业全景与全省机械制造业新闻。"),
    ("jiangsu-news", "⚓", "rgba(129,140,248,0.12)", "江苏汽车机械日报", "1.05s",
     "江苏汽车零部件与高端装备制造产业集群新闻（苏州、无锡、常州、盐城等）。"),
    ("shenzhen-news", "🌴", "rgba(248,113,113,0.12)", "深圳汽车机械日报", "1.10s",
     "比亚迪总部与深圳新能源汽车、智能制造产业最新动态。"),
]
card_tmpl = '''      <a href="https://ts-dinglilu.github.io/{slug}/" class="auto-card" target="_blank" data-cat="region" style="animation-delay:{delay}">
        <div class="auto-icon" style="background:{color}">{emoji}</div>
        <h3>{name}</h3>
        <p>{desc}</p>
        <div class="auto-updated">最新 <b>09-25</b> · 累计 1 期</div>
        <div class="auto-meta">
          <span class="auto-badge active">运行中</span>
          <span class="auto-badge early">每周一 · 周四</span>
          <span class="auto-link">访问 →</span>
        </div>
      </a>

'''
cards_html = "".join(card_tmpl.format(slug=s, emoji=e, color=c, name=n, delay=d, desc=p)
                     for s, e, c, n, d, p in CARDS)
grid_end = '''    </div>
  </div>
</section>

<!-- ABOUT -->'''
assert grid_end in h
h = h.replace(grid_end, cards_html + grid_end, 1)

# 3) 页脚导航加 9 链接
fp_link = '<a href="https://ts-dinglilu.github.io/future-planning/" target="_blank" data-page-node-id="wdWQEjWUc4I5INUwugJXOD">未来规划</a>'
assert fp_link in h
footer_add = "".join(
    '\n      <a href="https://ts-dinglilu.github.io/%s/" target="_blank">%s</a>' % (s, n)
    for s, n in [("xuzhou-news", "徐州"), ("nanjing-news", "南京"), ("shanghai-news", "上海"),
                 ("hangzhou-news", "杭州"), ("jiangzhehu-news", "江浙沪"), ("hefei-news", "合肥"),
                 ("anhui-news", "安徽"), ("jiangsu-news", "江苏"), ("shenzhen-news", "深圳")])
h = h.replace(fp_link, fp_link + footer_add, 1)

# 4) 统计数字 14 -> 23
h = h.replace("独立开发并维护 14 个每日自动化信息聚合系统", "独立开发并维护 23 个每日自动化信息聚合系统")
h = h.replace('<div class="stat-num" data-page-node-id="rWec4oWhBYk3TVgA5hAgvX">14</div>',
              '<div class="stat-num" data-page-node-id="rWec4oWhBYk3TVgA5hAgvX">23</div>')
h = h.replace(" 14 SYSTEMS LIVE", " 23 SYSTEMS LIVE")

io.open(P, "w", encoding="utf-8", newline="\n").write(h)
print("[OK] 主页地区分组: %d -> %d chars, 卡片 %d 张" % (orig, len(h), len(CARDS)))
