# -*- coding: utf-8 -*-
"""一次性引导脚本：为 9 个地区日报分类批量生成首期报告与归档页。

借 traditional-auto 最新报告做壳（通用型骨架），改写名字/emoji/关键词/日期后
套用 build_report 骨架逻辑产出 report_20260924.html + index.html，
再由 rebuild_index 重建归档列表。此后每日构建即可自我复制。

用法（在 repo/ 下）：python logs/bootstrap_regions.py
"""
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_report  # noqa: E402
import tail_template  # noqa: E402

SHELL_CAT = "traditional-auto"
SHELL_REPORT = "report_20260919.html"
SHELL_NAME = tail_template.CATEGORY_NAMES[SHELL_CAT]
DT = datetime.datetime(2026, 9, 24)

REGIONS = {
    "xuzhou-news": {
        "name": "徐州汽车机械日报",
        "emoji": "🏗️",
        "kw": "徐工 · 淮海经济区 · 工程机械 · 新能源商用车",
        "desc": "聚焦徐州工程机械之都：徐工动态、本地机械制造与淮海经济区汽车产业新闻",
        "idx_desc": "徐工与淮海经济区工程机械、汽车产业新闻",
    },
    "nanjing-news": {
        "name": "南京汽车机械日报",
        "emoji": "🦌",
        "kw": "长安深蓝 · 天枢智驾 · 汽车电子 · 布雷博",
        "desc": "聚焦南京整车基地与汽车电子：长安系产能、智驾落地与零部件动态",
        "idx_desc": "南京整车基地与汽车电子产业新闻",
    },
    "shanghai-news": {
        "name": "上海汽车机械日报",
        "emoji": "🌃",
        "kw": "特斯拉 · 上汽集团 · 智己 · 储能",
        "desc": "聚焦上海汽车产业：特斯拉上海工厂、上汽系与智能网联、储能新赛道",
        "idx_desc": "特斯拉、上汽与上海汽车产业新闻",
    },
    "hangzhou-news": {
        "name": "杭州汽车机械日报",
        "emoji": "⛵",
        "kw": "零跑 · 吉利 · 醇氢电动 · 智能驾驶",
        "desc": "聚焦杭州与浙江汽车产业：零跑放量、吉利体系与醇氢电动新路线",
        "idx_desc": "零跑、吉利与浙江汽车产业新闻",
    },
    "jiangzhehu-news": {
        "name": "江浙沪汽车机械日报",
        "emoji": "🕸️",
        "kw": "4小时产业圈 · G60走廊 · 一体化 · 供应链",
        "desc": "聚焦长三角一体化：跨省产业协同、供应链走廊与区域产业集群新闻",
        "idx_desc": "长三角一体化与区域汽车产业新闻",
    },
    "hefei-news": {
        "name": "合肥汽车机械日报",
        "emoji": "🚕",
        "kw": "蔚来 · 江淮 · 大众安徽 · 具身智能",
        "desc": "聚焦合肥新能源汽车之都：蔚来、江淮、大众安徽与智能装备产业",
        "idx_desc": "蔚来、江淮与合肥新能源汽车产业新闻",
    },
    "anhui-news": {
        "name": "安徽汽车机械日报",
        "emoji": "🏔️",
        "kw": "奇瑞 · 芜湖港 · 汽车出口 · 零部件",
        "desc": "聚焦安徽汽车强省建设：奇瑞出口、芜湖基地与全省零部件配套动态",
        "idx_desc": "奇瑞与安徽全省汽车产业新闻",
    },
    "jiangsu-news": {
        "name": "江苏汽车机械日报",
        "emoji": "🏭",
        "kw": "县域集群 · 轻量化 · 靖江 · 零部件",
        "desc": "聚焦江苏汽车机械产业：县域集群、轻量化工艺与零部件配套动态",
        "idx_desc": "江苏县域集群与零部件产业新闻",
    },
    "shenzhen-news": {
        "name": "深圳汽车机械日报",
        "emoji": "🌴",
        "kw": "比亚迪 · 机器人 · 出海 · 垂直整合",
        "desc": "聚焦深圳汽车与机器人产业：比亚迪出海、智能制造与跨界融合动态",
        "idx_desc": "比亚迪与深圳汽车机器人产业新闻",
    },
}


def rename(html, cat):
    cfg = REGIONS[cat]
    html = html.replace(SHELL_NAME, cfg["name"])
    return html


def build_head(tpl, cat):
    cfg = REGIONS[cat]
    k = tpl.find('<div class="report-header">')
    if k < 0:
        raise SystemExit("[%s] 模板中找不到 report-header" % cat)
    head = build_report.normalize_head(tpl[:k])
    head = re.sub(r'<div class="nav-links">.*?</div>\s*', "", head, flags=re.S)
    head = re.sub(r"<!--\s*=+[^>]*?=+\s*-->", "", head, flags=re.S)
    head = rename(head, cat)
    head = head.replace("一汽 · 上汽 · 东风 · 广汽 · 长安 · 北汽", cfg["kw"])
    head = head.replace("每日推送一汽/上汽/东风/广汽/长安/北汽招聘信息", cfg["desc"])
    head = head.replace("🚗", cfg["emoji"])
    head = build_report.fix_weekday(build_report.replace_dates(head, DT), DT)
    head = head.replace("TraeWork Automation", "WorkBuddy Automation")
    head = re.sub(r"<title>.*?</title>",
                  "<title>%s | %s</title>" % (cfg["name"], DT.strftime("%Y-%m-%d")),
                  head, count=1, flags=re.S)
    return head


def main():
    tpl = open(os.path.join(ROOT, SHELL_CAT, SHELL_REPORT), encoding="utf-8").read()
    print("[..] 借壳模板: %s/%s" % (SHELL_CAT, SHELL_REPORT))

    for cat, cfg in REGIONS.items():
        body = open(os.path.join(ROOT, "content", cat + ".html"),
                    encoding="utf-8").read().strip()
        body, _ = tail_template.strip_comment_artifacts(body)

        head = build_head(tpl, cat)
        tail = tail_template.build_tail(cfg["name"], DT.year, DT.month, DT.day,
                                        build_report.GISCUS_SCRIPT, has_main_close=False)
        out = build_report.autoclose_divs(head + "\n" + body) + "\n" + tail
        out = build_report.normalize_footer_name(out, cat)

        outdir = os.path.join(ROOT, cat)
        os.makedirs(outdir, exist_ok=True)
        out_path = os.path.join(outdir, "report_%s.html" % DT.strftime("%Y%m%d"))
        if os.path.exists(out_path):
            print("[SKIP] %s 首期已存在" % cat)
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(out)
            print("[OK] %s 首期报告: %d bytes" % (cat, len(out)))

        idx_path = os.path.join(outdir, "index.html")
        if os.path.exists(idx_path):
            print("[SKIP] %s 归档页已存在" % cat)
        else:
            idx = open(os.path.join(ROOT, SHELL_CAT, "index.html"),
                       encoding="utf-8").read()
            idx = rename(idx, cat)
            idx = idx.replace("一汽/上汽/东风等传统车企招聘信息", cfg["idx_desc"])
            idx = idx.replace("📋", cfg["emoji"])
            with open(idx_path, "w", encoding="utf-8") as f:
                f.write(idx)
            print("[OK] %s 归档页" % cat)

        build_report.rebuild_index(cat)

    print("DONE")


if __name__ == "__main__":
    main()
