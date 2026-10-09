# -*- coding: utf-8 -*-
"""2026-10-10 外链核验修复：换源 / 删除失效锚点，逐条 assert 替换次数。"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = "content/"

# (文件, [(旧串, 新串, 期望次数), ...])
OPS = [
    # 9. cqbys 全族死链：research-institute 两条删锚点留文字（上轮 5 文件已完成，跳过）
    ("research-institute.html", [
        ('<a class="source-link" href="https://cqu.cqbys.com/teachin/view?id=132946" target="_blank">📎 查看自控所2027届校招宣讲信息（重庆大学就业网）</a>',
         '📎 自控所2027届校招宣讲信息（重庆大学就业网·原链已失效，可检索标题核验）', 1),
        ('<a class="source-link" href="https://cqu.cqbys.com/en/teachin/view/id/132786" target="_blank">📎 查看航发沈阳发动机研究所2027届校招（重庆大学就业网）</a>',
         '📎 航发沈阳发动机研究所2027届校招（重庆大学就业网·原链已失效，可检索标题核验）', 1),
        (' <a class="source-link" href="https://cqu.cqbys.com/teachin/view?id=132946" target="_blank">📎 查看原文</a>', "", 1),
        ('<a class="source-link" href="https://cqu.cqbys.com/en/teachin/view/id/132786" target="_blank">📎 查看原文</a> ', "", 1),
    ]),
    # 10. cqbys 死链 → 科大讯飞校招官网（已验证 200）
    ("anhui-recruit.html", [
        ("https://www.cqbys.com/campus/view/id/735886", "https://campus.iflytek.com/", 2),
        ("（重庆高校就业平台）", "（科大讯飞校招官网）", 1),
    ]),
    # 11. cqbys 死链：supply-chain 删锚点留文字
    ("supply-chain-recruit.html", [
        ('<a class="source-link" href="https://www.cqbys.com/jobfair91/stand/sid/298290" target="_blank">📎 查看原文</a>',
         '📎 原链已失效，可检索标题核验', 1),
    ]),
    # 14. 武大就业网深链无法验证：删锚点留文字
    ("jiangsu-recruit.html", [
        ('<a class="source-link" href="https://xsjy.whu.edu.cn/f/recruitmentinfo/show?recruitmentId=d02b9fe82b0248748d1b30f4443b322e" target="_blank">📎 查看原文</a>',
         '📎 原链已失效，可检索标题核验', 2),
    ]),
    # 15. 吴江人才网 404：删锚点留文字
    ("jiangzhehu-recruit.html", [
        ('<a class="source-link" href="https://z5.wjhr.net/Information/Read.aspx?id=9747" target="_blank">📎 查看原文</a>',
         '📎 原链已失效，可检索标题核验', 2),
    ]),
]

for fname, ops in OPS:
    path = BASE + fname
    s = open(path, encoding="utf-8").read()
    for old, new, expect in ops:
        n = s.count(old)
        assert n == expect, "%s: 期望 %d 次, 实际 %d 次 :: %s..." % (fname, expect, n, old[:60])
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(s)
    print("OK", fname, "(%d 处替换)" % len(ops))

print("ALL DONE")
