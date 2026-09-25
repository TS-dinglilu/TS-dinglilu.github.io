# -*- coding: utf-8 -*-
"""把 content/supply-chain-recruit.html 的「信息来源汇总」表压到 13 行（规范：优先删汇总表冗余行）。"""
import re

P = "content/supply-chain-recruit.html"
KEEP = [
    "https://jdjyw.jlu.edu.cn/portal/jyzp/recruit/details?id=2cd524af9c244bbba8abb0d71ec3dbda",
    "https://career.smbu.edu.cn/detail/online?id=3595552",
    "https://zbjy.nuc.edu.cn/detail/job?id=3234466",
    "https://m.quanzhi.com/job/detail/691d59cbfc1e16b7afdab576",
    "https://blog.gaodingoffer.cn/e38bf354fd854ec1b31b2760abacf089",
    "https://www.wondercv.com/xiaozhao/bosch-rexroth-2027-campus-recruitment-16164-9bc827",
    "https://blog.gaodingoffer.cn/edae73bd89824b25b1e92332ea042e2a",
    "https://jxdxsjy.jx.edu.cn/campus/view/id/985524",
    "https://career.hebut.edu.cn/correcruit/content/id/80214.html",
    "https://www.wondercv.com/xiaozhao/desay-sv-2027-global-campus-recruitment-14528-e82811",
    "https://hbcnc.ahbys.com/job2.html?cid=394&jid=84576",
    "https://job.ucas.edu.cn/f/recruitmentFair/show?recruitmentFairId=88b4ed910cd44474b44aaa5624f87de0",
    "https://job.hitwh.edu.cn/zhxy-whxszyfzpt/zpxx/zpxxxq?id=MDYwYzU3NzI2ZTJhNDEwOGFmZTRjZmY1MmZhMTY4Yjk=",
]

s = open(P, encoding="utf-8").read()
i = s.find('<table class="summary-table">', s.find("信息来源汇总"))
j = s.find("</tbody>", i)
head, table, rest = s[:i], s[i:j], s[j:]

rows = re.findall(r"<tr>.*?</tr>", table, re.S)
body_rows = [r for r in rows if "source-link" in r]
other = [r for r in rows if "source-link" not in r]
print("原数据行 %d" % len(body_rows))

kept = []
for href in KEEP:
    hit = [r for r in body_rows if href in r]
    if len(hit) != 1:
        raise SystemExit("href 未唯一匹配(%d): %s" % (len(hit), href))
    kept.append("        " + hit[0])

new_table = table
new_table = new_table[: new_table.find("<tr>")] + "\n".join(kept) + "\n      " + \
    new_table[new_table.rfind("</tr>") + len("</tr>"):]
s = head + new_table + rest
open(P, "w", encoding="utf-8").write(s)
print("压缩后字符数 = %d" % len(s))
