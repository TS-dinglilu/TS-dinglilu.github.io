# -*- coding: utf-8 -*-
"""一次性引导脚本：为「车企供应链招聘日报」(supply-chain-recruit) 生成首期报告与归档页。

为什么需要它：build_report.pick_template() 只在本分类目录里找上一期报告当模板，
新分类目录是空的 → 鸡生蛋问题。这里借「传统车企招聘日报」(同为通用型骨架的招聘日报)
的最新报告做壳，改写名字 / 日期后套用 build_report 的骨架 B 逻辑产出首期报告；
此后每日构建即可正常自我复制。

⚠️ 注意：build_report 的 head 切片取的是「首个内容锚点之前」，会把模板里历史累积的
report-header / highlight-box 区块一并带过来。借壳时必须只取到 hero 为止，
否则会把「传统车企」的正文块（一汽-大众、江淮等）污染进新分类。

用法（在 repo/ 下）：python logs/bootstrap_supply_chain.py
"""
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_report  # noqa: E402
import tail_template  # noqa: E402

CAT = "supply-chain-recruit"
NAME = "车企供应链招聘日报"
SHELL_CAT = "traditional-auto"      # 借壳来源（同为招聘日报、通用型骨架）
SHELL_REPORT = "report_20260919.html"
DT = datetime.datetime(2026, 9, 24)
KEYWORDS = "宁德时代 · 博世 · 麦格纳 · 均胜电子 · 三花智控 · 延锋 · 德赛西威 · 立讯精密"


def rename(html):
    """借壳改名：模板分类的名字 → 新分类名字。"""
    html = html.replace("六大" + tail_template.CATEGORY_NAMES[SHELL_CAT], NAME)
    html = html.replace(tail_template.CATEGORY_NAMES[SHELL_CAT], NAME)
    return html


def build_head(tpl):
    # 只取到 hero 结束：首个 report-header 之前（不含历史累积的标题块）
    k = tpl.find('<div class="report-header">')
    if k < 0:
        raise SystemExit("模板中找不到 report-header")
    head = build_report.normalize_head(tpl[:k])
    head = re.sub(r'<div class="nav-links">.*?</div>\s*', "", head, flags=re.S)
    head = re.sub(r"<!--\s*=+[^>]*?=+\s*-->", "", head, flags=re.S)   # 清掉遗留的板块注释
    head = rename(head)
    head = head.replace("一汽 · 上汽 · 东风 · 广汽 · 长安 · 北汽", KEYWORDS)
    head = head.replace("每日推送一汽/上汽/东风/广汽/长安/北汽招聘信息",
                        "每日推送零部件与供应链岗位招聘信息")
    head = head.replace("🚗", "🚚")
    head = build_report.fix_weekday(build_report.replace_dates(head, DT), DT)
    head = head.replace("TraeWork Automation", "WorkBuddy Automation")
    head = re.sub(r"<title>.*?</title>",
                  "<title>%s | %s</title>" % (NAME, DT.strftime("%Y-%m-%d")),
                  head, count=1, flags=re.S)
    return head


def main():
    tpl_path = os.path.join(ROOT, SHELL_CAT, SHELL_REPORT)
    tpl = open(tpl_path, encoding="utf-8").read()
    print("[..] 借壳模板: %s/%s" % (SHELL_CAT, SHELL_REPORT))

    body = open(os.path.join(ROOT, "content", CAT + ".html"), encoding="utf-8").read().strip()
    body, _ = tail_template.strip_comment_artifacts(body)

    head = build_head(tpl)
    tail = tail_template.build_tail(NAME, DT.year, DT.month, DT.day,
                                    build_report.GISCUS_SCRIPT, has_main_close=False)
    out = build_report.autoclose_divs(head + "\n" + body) + "\n" + tail
    out = build_report.normalize_footer_name(out, CAT)

    outdir = os.path.join(ROOT, CAT)
    os.makedirs(outdir, exist_ok=True)
    out_path = os.path.join(outdir, "report_%s.html" % DT.strftime("%Y%m%d"))
    open(out_path, "w", encoding="utf-8").write(out)
    print("[OK] 首期报告已生成: %s (%d bytes)" % (out_path, len(out)))

    # 归档页：借传统车企归档页，改名后由 rebuild_index 重建列表
    idx_path = os.path.join(outdir, "index.html")
    if not os.path.exists(idx_path):
        idx = open(os.path.join(ROOT, SHELL_CAT, "index.html"), encoding="utf-8").read()
        idx = rename(idx)
        idx = idx.replace("一汽/上汽/东风等传统车企招聘信息", "零部件与供应链岗位招聘信息")
        idx = idx.replace("📋", "🚚")
        open(idx_path, "w", encoding="utf-8").write(idx)
        print("[OK] 归档页已生成: %s" % idx_path)

    build_report.rebuild_index(CAT)


if __name__ == "__main__":
    main()
