# -*- coding: utf-8 -*-
"""第二轮：表格行已删，收掉剩余正文链接（期望均为1）"""
import re

def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()

def save(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)

ops = [
    ('anhui-recruit.html',
     r'\s*<a class="source-link" href="https://cjxy\.91wllm\.cn/largefairs/company/id/8774/sid/5" target="_blank">[^<]*</a>', ''),
    ('anhui-recruit.html',
     r'\s*<a class="source-link" href="https://whicu\.91wllm\.cn/largefairs/company/id/8637/sid/45" target="_blank">[^<]*</a>', ''),
    ('future-planning.html',
     r'\s*<a class="source-link" href="http://rwkx\.sntcm\.edu\.cn/rcpy/sx/123672\.htm" target="_blank">[^<]*</a>', ''),
    ('geely-recruit.html',
     r'\s*<a class="source-link" href="https://wustyjs\.91wllm\.cn/teachin/view/id/250122" target="_blank">[^<]*</a>', ''),
    ('jiangsu-recruit.html',
     'https://www.91wllm.cn/job/view/id/2385178/from_type/4/from_id/1001669', 'https://job.byd.com'),
    ('shanghai-news.html',
     r'\s*<a class="source-link" href="https://www\.163\.com/dy/article/L862IEQ5055616Z4\.html" target="_blank">[^<]*</a>', ''),
    ('xuzhou-news.html',
     r'\s*<a class="source-link" href="https://m\.zgong\.com/News/detail/81415\.html" target="_blank">[^<]*</a>', ''),
]

bad_marks = ['sntcm.edu.cn', 'cjxy.91wllm', 'whicu.91wllm', 'cug.91wllm',
             'm.zgong.com', 'aastocks.com', 'wustyjs.91wllm',
             'L862IEQ5055616Z4', 'channelnewsasia.com', 'bxss.me',
             'www.91wllm.cn/job', 'campus.nio.com']
nfail = 0
for f, pat, rep in ops:
    path = 'content/' + f
    text = load(path)
    new_text, cnt = re.subn(pat, rep, text)
    if cnt != 1:
        print('FAIL %-24s 期望1 实际%d' % (f, cnt)); nfail += 1
    else:
        save(path, new_text)
        print('OK   %-24s x%d' % (f, cnt))

print()
residue = False
for f in sorted(set(x[0] for x in ops)) + ['supply-chain-recruit.html', 'weixiaoli-recruit.html', 'anhui-news.html']:
    t = load('content/' + f)
    for m in bad_marks:
        if m in t:
            print('RESIDUE %s contains %s' % (f, m)); residue = True
if not nfail and not residue:
    print('ALL CLEAN')
