# -*- coding: utf-8 -*-
"""一次性引导脚本：为「奇瑞职场口碑日报」(chery-insider) 生成首期报告与归档页（2026-09-27）。

借 traditional-auto 最新报告做壳（通用型骨架），改写名字/emoji/关键词/日期后
套用 build_report 骨架逻辑产出 report_20260927.html + index.html，
再由 rebuild_index 重建归档列表。此后每日构建即可自我复制。

用法（在 repo/ 下）：C:/Users/dingliu/.workbuddy/binaries/python/versions/3.13.12/python.exe logs/bootstrap_chery_insider.py
"""
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_report  # noqa: E402
import tail_template  # noqa: E402

CAT = "chery-insider"
NAME = "奇瑞职场口碑日报"
SHELL_CAT = "traditional-auto"
DT = datetime.datetime(2026, 9, 27)
EMOJI = "💬"
KW = "待遇 · 加班 · 薪资 · 口碑 · 网友评论"
DESC = "聚焦奇瑞打工体验：薪资结构、加班文化、员工口碑与全网网友评论"
IDX_DESC = "奇瑞待遇、加班、薪资与员工口碑全景"
SHELL_KW = "一汽 · 上汽 · 东风 · 广汽 · 长安 · 北汽"
SHELL_DESC = "每日推送一汽/上汽/东风/广汽/长安/北汽招聘信息"
SHELL_IDX_DESC = "一汽/上汽/东风等传统车企招聘信息"


def build_head(tpl):
    k = tpl.find('<div class="report-header">')
    if k < 0:
        raise SystemExit("模板中找不到 report-header")
    head = build_report.normalize_head(tpl[:k])
    head = re.sub(r'<div class="nav-links">.*?</div>\s*', "", head, flags=re.S)
    head = re.sub(r"<!--\s*=+[^>]*?=+\s*-->", "", head, flags=re.S)
    head = head.replace(tail_template.CATEGORY_NAMES[SHELL_CAT], NAME)
    head = head.replace(SHELL_KW, KW)
    head = head.replace(SHELL_DESC, DESC)
    head = head.replace("🚗", EMOJI)
    head = build_report.fix_weekday(build_report.replace_dates(head, DT), DT)
    head = head.replace("TraeWork Automation", "WorkBuddy Automation")
    head = re.sub(r"<title>.*?</title>",
                  "<title>%s | %s</title>" % (NAME, DT.strftime("%Y-%m-%d")),
                  head, count=1, flags=re.S)
    return head


def main():
    shell = sorted(
        f for f in os.listdir(os.path.join(ROOT, SHELL_CAT))
        if f.startswith("report_") and f.endswith(".html"))
    shell_path = os.path.join(ROOT, SHELL_CAT, shell[-1])
    tpl = open(shell_path, encoding="utf-8").read()
    print("[..] 借壳模板: %s/%s" % (SHELL_CAT, shell[-1]))

    body = open(os.path.join(ROOT, "content", CAT + ".html"),
                encoding="utf-8").read().strip()
    body, _ = tail_template.strip_comment_artifacts(body)

    head = build_head(tpl)
    tail = tail_template.build_tail(NAME, DT.year, DT.month, DT.day,
                                    build_report.GISCUS_SCRIPT, has_main_close=False)
    out = build_report.autoclose_divs(head + "\n" + body) + "\n" + tail
    out = build_report.normalize_footer_name(out, CAT)

    try:
        from password_gate import inject as _inject_gate
        out, _ = _inject_gate(out)
    except Exception as e:  # noqa: BLE001
        print("[WARN] 密码守卫注入失败: %s" % e)

    outdir = os.path.join(ROOT, CAT)
    os.makedirs(outdir, exist_ok=True)
    out_path = os.path.join(outdir, "report_%s.html" % DT.strftime("%Y%m%d"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)
    print("[OK] 首期报告: %s (%d bytes)" % (out_path, len(out)))

    idx_path = os.path.join(outdir, "index.html")
    idx = open(os.path.join(ROOT, SHELL_CAT, "index.html"), encoding="utf-8").read()
    idx = idx.replace(tail_template.CATEGORY_NAMES[SHELL_CAT], NAME)
    idx = idx.replace(SHELL_IDX_DESC, IDX_DESC)
    idx = idx.replace("📋", EMOJI)
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(idx)
    print("[OK] 归档页")

    build_report.rebuild_index(CAT)
    print("DONE")


if __name__ == "__main__":
    main()
