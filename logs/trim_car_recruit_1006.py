# -*- coding: utf-8 -*-
"""car-recruit 10-06 正文压缩：23008 -> <20000。只删整块，不增内容，不动其余链接。"""
import re, io

P = 'content/car-recruit.html'
s = io.open(P, encoding='utf-8').read()
orig = len(s)

def cut(s, start_mark, end_mark, keep_end=True):
    """删除 [start_mark 起, end_mark 前) 的内容；keep_end=True 时保留 end_mark 本身。"""
    i = s.index(start_mark)
    j = s.index(end_mark, i + len(start_mark))
    assert i < j, (start_mark[:40], i, j)
    return s[:i] + s[j:]

# 1) 删板块六 card ①（深圳车展——与 shenzhen-news 重复，核心数据已保留在 highlight-box）
s = cut(s,
    '  <div class="card">\n    <h3>① 国庆车市分层',
    '  <div class="card">\n    <h3>② 9 月数据三主线')

# 2) 删板块六 card ③（长沙芒果车展——区域市场，与招聘主线关联最弱）
s = cut(s,
    '  <div class="card">\n    <h3>③ 长沙芒果车展',
    '</div>\n\n<div class="section">\n  <div class="section-title">板块七')

# 3) 板块六标题去掉已删的车展部分
s = s.replace('板块六 · 行业风向：车展「旺丁不旺财」与 9 月数据的三条主线',
              '板块六 · 行业风向：9 月数据的三条主线')

# 4) 删板块一导览里的「板块导航」news-item（与速读三段重复）
s = cut(s,
    '    <div class="news-item">\n      <div class="news-meta"><span class="tag tag-info">导读</span>',
    '  </div>\n</div>\n\n<div class="section">\n  <div class="section-title">板块二')

# 5) 汇总表删除已删卡片对应的 <tr> 行（按 URL 子串匹配）
drop_urls = [
    'https://www.nfnews.com/content/EynG4mzd3Z.html',
    'https://m.21jingji.com/article/20261005/herald/1f144e3997fef44b043c9375c97ca953.html',
    'https://k.sina.com.cn/article_1001961051_3bb8b65b001018xn0.html',
    'https://www.toutiao.com/article/7691625615220343311/',
]
for u in drop_urls:
    s = re.sub(r'[ \t]*<tr><td>(?:(?!</tr>).)*?' + re.escape(u) + r'(?:(?!</tr>).)*?</tr>\r?\n', '', s, flags=re.S)
    assert u not in s, u

n = len(s)
open_div = s.count('<div')
close_div = s.count('</div>')
links = s.count('source-link')
print(f'chars: {orig} -> {n}  (cut {orig-n})')
print(f'div balance: {open_div}/{close_div}  links: {links}')
assert 12000 <= n <= 20000, 'LEN out of range'
assert open_div == close_div, 'div unbalanced'
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('OK written')
