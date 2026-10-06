# -*- coding: utf-8 -*-
"""2026-10-07 外链修复：死链删除 / 换源替换，带匹配计数断言"""
import re, sys

def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()

def save(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)

# (file, pattern, replacement, expected_count, is_regex, label)
ops = [
    # 1. weixiaoli: campus.nio.com -> nio.cn/careers (200 已验证)
    ('weixiaoli-recruit.html',
     'http://campus.nio.com/?ref=toptrafficsites#/',
     'https://www.nio.cn/careers', 2, False, 'nio 官网换源'),
    # 2. future-planning: 删 sntcm 死链（正文+表格行）
    ('future-planning.html',
     r'\s*<a class="source-link" href="http://rwkx\.sntcm\.edu\.cn/rcpy/sx/123672\.htm" target="_blank">[^<]*</a>',
     '', 1, True, '删 sntcm 正文链接'),
    ('future-planning.html',
     r'\s*<tr><td>求职复盘\+规划，让你赢在开局（陕西中医药大学）</td><td><a class="source-link" href="http://rwkx\.sntcm\.edu\.cn/rcpy/sx/123672\.htm" target="_blank">[^<]*</a></td><td>2026</td></tr>',
     '', 1, True, '删 sntcm 表格行'),
    # 3. anhui-recruit: 删两条 91wllm 404（正文+表格行）
    ('anhui-recruit.html',
     r'\s*<a class="source-link" href="https://cjxy\.91wllm\.cn/largefairs/company/id/8774/sid/5" target="_blank">[^<]*</a>',
     '', 1, True, '删 cjxy 正文链接'),
    ('anhui-recruit.html',
     r'\s*<tr><td>奇瑞新能源汽车股份展位·长江职业学院招聘会（湖北就业平台）</td><td><a class="source-link" href="https://cjxy\.91wllm\.cn/largefairs/company/id/8774/sid/5" target="_blank">[^<]*</a></td><td>2026-10-16</td></tr>',
     '', 1, True, '删 cjxy 表格行'),
    ('anhui-recruit.html',
     r'\s*<a class="source-link" href="https://whicu\.91wllm\.cn/largefairs/company/id/8637/sid/45" target="_blank">[^<]*</a>',
     '', 1, True, '删 whicu 正文链接'),
    ('anhui-recruit.html',
     r'\s*<tr><td>奇瑞控股集团展位·武汉商贸职院双选会（湖北就业平台）</td><td><a class="source-link" href="https://whicu\.91wllm\.cn/largefairs/company/id/8637/sid/45" target="_blank">[^<]*</a></td><td>2026-10-22</td></tr>',
     '', 1, True, '删 whicu 表格行'),
    # 4. jiangsu-recruit: 比亚迪双 91wllm 死链 -> job.byd.com (200 已验证)
    ('jiangsu-recruit.html',
     'https://www.91wllm.cn/job/view/id/2385178/from_type/4/from_id/1001669',
     'https://job.byd.com', 1, False, 'byd 死链换官方门户'),
    ('jiangsu-recruit.html',
     'https://cug.91wllm.cn/en/job/view/id/2385178',
     'https://job.byd.com', 1, False, 'byd 死链镜像换官方门户'),
    ('jiangsu-recruit.html',
     '比亚迪2027届校招应届生岗（湖北高校就业网络联盟收录）',
     '比亚迪2027届校招应届生岗（比亚迪招聘官网）', 1, False, 'byd 表格行文字'),
    ('jiangsu-recruit.html',
     '📎 查看原文（地大收录版）',
     '📎 查看原文（官方招聘门户）', 1, False, 'byd 正文链接文字'),
    # 5. xuzhou-news: 删 zgong 验证墙链接（同条目已留搜狐 200）
    ('xuzhou-news.html',
     r'\s*<a class="source-link" href="https://m\.zgong\.com/News/detail/81415\.html" target="_blank">[^<]*</a>',
     '', 1, True, '删 zgong 正文链接'),
    ('xuzhou-news.html',
     r'\s*<tr><td>投资5\.07亿元，厂房面积17万平方米！徐工农业机械启动智能制造项目（重工机械网）</td><td><a class="source-link" href="https://m\.zgong\.com/News/detail/81415\.html" target="_blank">[^<]*</a></td><td>2026-10</td></tr>',
     '', 1, True, '删 zgong 表格行'),
    # 6. supply-chain: aastocks 注入payload URL -> 车家号 200
    ('supply-chain-recruit.html',
     'https://wdatacn.aastocks.com/sc/(Z(@@n7cjDGdCXMF=acx%7B%7B%7Bbxss.me%7D%7D%7Dxca))/stocks/news/aafn-con/NOW.1505373/latest-news/AAFN',
     'https://chejiahao.m.autohome.com.cn/info/24893225', 2, False, '博世新闻换车家号'),
    ('supply-chain-recruit.html',
     '蔚来与博世签署战略合作（阿斯达克财经）',
     '蔚来与博世签署战略合作（车家号·汽车之家）', 1, False, '博世表格行文字'),
    # 7. geely-recruit: 删 wustyjs 404（同卡片还有浙财大+海南大学两条 200）
    ('geely-recruit.html',
     r'\s*<a class="source-link" href="https://wustyjs\.91wllm\.cn/teachin/view/id/250122" target="_blank">[^<]*</a>',
     '', 1, True, '删 wustyjs 正文链接'),
    ('geely-recruit.html',
     r'\s*<tr><td>吉利控股集团2027届秋季校园招聘宣讲会（武汉科技大学研究生就业信息网·9大方向35\+城市）</td><td><a class="source-link" href="https://wustyjs\.91wllm\.cn/teachin/view/id/250122" target="_blank">[^<]*</a></td><td>2026-10</td></tr>',
     '', 1, True, '删 wustyjs 表格行'),
    # 8. shanghai-news: 删 163.com 404（同卡片还有头条 200）
    ('shanghai-news.html',
     r'\s*<a class="source-link" href="https://www\.163\.com/dy/article/L862IEQ5055616Z4\.html" target="_blank">[^<]*</a>',
     '', 1, True, '删 163 正文链接'),
    ('shanghai-news.html',
     r'\s*<tr><td>订单直接排到2031年！日韩造船巨头干着急，中国造船厂凭啥通吃？（网易号）</td><td><a class="source-link" href="https://www\.163\.com/dy/article/L862IEQ5055616Z4\.html" target="_blank">[^<]*</a></td><td>2026-10-01</td></tr>',
     '', 1, True, '删 163 表格行'),
    # 9. anhui-news: CNA 不可达 -> 中国城市网 200
    ('anhui-news.html',
     'https://www.channelnewsasia.com/media-release/overseas-range-records-zero-carbon-factories-chery-auto-showcase-green-technology-2026-chery-international-user-summit-6423336',
     'https://www.zgcsb.com/news/pinDao/2026-09/23/a_692674.html', 2, False, '奇瑞峰会换中国城市网'),
    ('anhui-news.html',
     'Chery Auto to Showcase Green Technology at 2026 Chery International User Summit（GlobeNewswire/CNA）',
     '2026奇瑞全球用户大会10月启幕：展示近20项绿色技术（中国城市网）', 1, False, '奇瑞峰会表格行文字'),
]

# 按文件分组，逐文件顺序处理（同文件串行，避免并发写覆盖）
from collections import defaultdict
by_file = defaultdict(list)
for f, pat, rep, n, isre, label in ops:
    by_file[f].append((pat, rep, n, isre, label))

fail = []
for f in sorted(by_file):
    path = 'content/' + f
    text = load(path)
    for pat, rep, n, isre, label in by_file[f]:
        if isre:
            new_text, cnt = re.subn(pat, rep, text)
        else:
            cnt = text.count(pat)
            new_text = text.replace(pat, rep)
        if cnt != n:
            fail.append('%s | %s | 期望%d 实际%d' % (f, label, n, cnt))
            print('FAIL %-24s %-28s 期望%d 实际%d' % (f, label, n, cnt))
        else:
            text = new_text
            print('OK   %-24s %-28s x%d' % (f, label, cnt))
    save(path, text)

# 全局校验：残留检查
bad_marks = ['sntcm.edu.cn', 'cjxy.91wllm', 'whicu.91wllm', 'cug.91wllm',
             'm.zgong.com', 'aastocks.com', 'wustyjs.91wllm',
             'L862IEQ5055616Z4', 'channelnewsasia.com', 'bxss.me',
             'www.91wllm.cn/job', 'campus.nio.com']
print()
for f in sorted(by_file):
    t = load('content/' + f)
    for m in bad_marks:
        if m in t:
            print('RESIDUE %s contains %s' % (f, m))
if not fail:
    print('ALL DONE: %d ops applied' % len(ops))
