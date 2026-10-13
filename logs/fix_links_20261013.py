# -*- coding: utf-8 -*-
"""2026-10-13 外链修复：7 文件，全部带出现次数断言，任一失败则整文件不落盘。"""
import io, sys

def fix(path, pairs):
    with io.open(path, encoding="utf-8") as f:
        s = f.read()
    for old, new, expect in pairs:
        n = s.count(old)
        if n != expect:
            print(f"FAIL {path}: expect {expect} got {n} :: {old[:60]}")
            return False
        s = s.replace(old, new)
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(s)
    print(f"OK   {path} ({len(pairs)} rules)")
    return True

# 1. supply-chain-recruit：里昂 740（4月旧文）→ 820（10月上旬新文）
sc_pairs = [
    ("宁德时代成为全球唯一连续三期发布 GBA 电池护照企业、里昂上调 H 股目标价至 740 港元",
     "宁德时代成为全球唯一连续三期发布 GBA 电池护照企业、里昂上调 H 股目标价至 820 港元", 1),
    ("<strong>里昂将宁德时代 H 股目标价由 710 港元上调至 740 港元</strong>",
     "<strong>里昂将宁德时代 H 股目标价由 740 港元上调至 820 港元</strong>", 1),
    ('<div class="stat-box"><div class="count-badge">740港元</div><div class="label">里昂宁德时代H股目标价</div><div class="sub">10-13上调 · 原目标710</div></div>',
     '<div class="stat-box"><div class="count-badge">820港元</div><div class="label">里昂宁德时代H股目标价</div><div class="sub">10月上旬上调 · 原目标740</div></div>', 1),
    ('<span class="badge badge-success">✅ 大行看多</span><span>阿斯达克 10-13</span>',
     '<span class="badge badge-success">✅ 大行看多</span><span>阿斯达克 10-09</span>', 1),
    ("<p>10 月 13 日盘面：里昂发表报告指宁德时代今年首季纯利按年增长 <strong>49% 至 207 亿元</strong>、毛利率 24.8%，尽管年初至今锂价上升仍略胜预期，预计 2026 年是毛利率底部、次季起成本转嫁带动改善；<strong>上调 2026—2028 年每股盈利预测 2%—3%，H 股目标价由 710 港元升至 740 港元、A 股目标价由 505 元升至 515 元，重申「高确信度跑赢大市」</strong>。同日中财网研报视角：",
     "<p>宁德时代科技日后，里昂发表报告指 2026 年科技日未发布突破性技术、而是对现有产品持续改进以保持领先，但钠离子电池投产延后至今年末季、叠加今年次季至第三季可能出现锂供应缺口或为锂价带来上行风险；<strong>H 股目标价由 740 港元升至 820 港元、A 股目标价由 515 元升至 570 元，重申「高确信度跑赢大市」</strong>（10 月上旬）。中财网研报视角：", 1),
    ('<a class="source-link" href="https://wdatacn.aastocks.com/sc/stocks/analysis/stock-aafn-con/3750/HK6/NOW.1518067/hk-stock-news" target="_blank">📎 查看原文（阿斯达克·里昂升目标价至740港元）</a>',
     '<a class="source-link" href="https://www.aastocks.com/sc/stocks/analysis/stock-aafn-con/3750/hk6/NOW.1519365/hk-stock-news" target="_blank">📎 查看原文（阿斯达克·里昂升目标价至820港元）</a>', 1),
    ('<tr><td>3</td><td>里昂升宁德时代(03750.HK)目标价至740港元（10-13）</td><td>阿斯达克财经</td><td><a class="source-link" href="https://wdatacn.aastocks.com/sc/stocks/analysis/stock-aafn-con/3750/HK6/NOW.1518067/hk-stock-news" target="_blank">📎 查看原文</a></td></tr>',
     '<tr><td>3</td><td>里昂升宁德时代(03750.HK)目标价至820港元（10月上旬）</td><td>阿斯达克财经</td><td><a class="source-link" href="https://www.aastocks.com/sc/stocks/analysis/stock-aafn-con/3750/hk6/NOW.1519365/hk-stock-news" target="_blank">📎 查看原文</a></td></tr>', 1),
]

# 2. jiangzhehu-news：吉利 9 月销量官方 PDF 编号修正（EN_V1 → CN_V1）
jzh_pairs = [
    ("https://www.geelyauto.com.hk/wp-content/uploads/2026/10/Geely_2026_Sept-Sales_EN_V1.pdf",
     "https://www.geelyauto.com.hk/wp-content/uploads/2026/10/Geely_2026-Sept-Sales_CN_V1.pdf", 2),
]

# 3. xiaomi-recruit：smzdm 404 → 两条已验证 smzdm 文（第1/2/4处→aqrqgl47，第3处→a3mx2w65）
OLD_SMZDM = '<a class="source-link" href="https://post.m.smzdm.com/p/aomv7nm6"'
with io.open("content/xiaomi-recruit.html", encoding="utf-8") as f:
    _s = f.read()
_n = _s.count(OLD_SMZDM)
if _n != 4:
    print(f"FAIL xiaomi-recruit: smzdm expect 4 got {_n}")
else:
    parts = _s.split(OLD_SMZDM)
    repl = ["https://post.smzdm.com/p/aqrqgl47/", "https://post.smzdm.com/p/aqrqgl47/",
            "https://post.smzdm.com/p/a3mx2w65/", "https://post.smzdm.com/p/aqrqgl47/"]
    _s2 = parts[0]
    for i, r in enumerate(repl):
        _s2 += '<a class="source-link" href="' + r + '"' + parts[i + 1]
    with io.open("content/xiaomi-recruit.html", "w", encoding="utf-8", newline="") as f:
        f.write(_s2)
    print("OK   content/xiaomi-recruit.html (4 links)")

# 4. company-reputation：网易 163 文被下架 → 头条·车圈第一线（内容吻合）
cr_pairs = [
    ("：网易还原「苏工泼水」——研发岗员工与主管冲突后泼水",
     "：头条·车圈第一线还原「苏工泼水」——研发岗员工与主管冲突后泼水", 1),
    ('<a class="source-link" href="https://m.163.com/news/article/L91O25DN0553TF8P.html" target="_blank">📎 查看原文</a>',
     '<a class="source-link" href="https://www.toutiao.com/article/7695582203148763695" target="_blank">📎 查看原文</a>', 2),
    ("<td>比亚迪苏工事件＋待遇正反面</td><td>网易＋爱企查×2</td>",
     "<td>比亚迪苏工事件＋待遇正反面</td><td>头条＋爱企查×2</td>", 1),
]
# 表格里可能还有第二个 163 链接（row 4 同 href）
with io.open("content/company-reputation.html", encoding="utf-8") as f:
    _s = f.read()
print("  163 href count in cr:", _s.count("L91O25DN0553TF8P"))

# 5/6. nio 校招官网：campus.nio.com → nio.cn/careers（既有判据）
nio_pairs_weixiaoli = [
    ('href="http://campus.nio.com/"', 'href="https://www.nio.cn/careers"', 2),
]
nio_pairs_hefei = [
    ('<span>campus.nio.com</span>', '<span>nio.cn/careers</span>', 1),
    ('<td>campus.nio.com</td>', '<td>nio.cn/careers</td>', 1),
    ('href="http://campus.nio.com/"', 'href="https://www.nio.cn/careers"', 2),
]

# 7. anhui-recruit：肥东政府网深链不可验（521，官网整体不可达）→ 粉笔考试日历（内容双源证实）
ar_pairs = [
    ('<span class="badge-info">ℹ️ 10-09至10-16报名</span><span>县政府官网</span>',
     '<span class="badge-info">ℹ️ 10-09至10-16报名</span><span>粉笔考试日历</span>', 1),
    ('<td>肥东县县管国有企业2026年公开招聘公告</td><td>肥东县人民政府官网</td><td><a class="source-link" href="https://www.feidong.gov.cn/dtxw/tzgg/120395399.html" target="_blank">📎 查看原文</a></td>',
     '<td>肥东县县管国有企业2026年公开招聘公告</td><td>粉笔教育考试日历</td><td><a class="source-link" href="https://fenbi.com/page/exam-timeline-detail/954401" target="_blank">📎 查看原文</a></td>', 1),
    ('<a class="source-link" href="https://www.feidong.gov.cn/dtxw/tzgg/120395399.html" target="_blank">📎 查看原文</a>',
     '<a class="source-link" href="https://fenbi.com/page/exam-timeline-detail/954401" target="_blank">📎 查看原文（粉笔·考试日历）</a>', 1),
]

ok = True
ok &= fix("content/supply-chain-recruit.html", sc_pairs)
ok &= fix("content/jiangzhehu-news.html", jzh_pairs)
ok &= fix("content/company-reputation.html", cr_pairs)
ok &= fix("content/weixiaoli-recruit.html", nio_pairs_weixiaoli)
ok &= fix("content/hefei-recruit.html", nio_pairs_hefei)
ok &= fix("content/anhui-recruit.html", ar_pairs)
sys.exit(0 if ok else 1)
