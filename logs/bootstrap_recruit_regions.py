# -*- coding: utf-8 -*-
"""一次性引导脚本：为 9 个地区招聘日报分类批量生成首期报告与归档页（2026-09-26）。

借 traditional-auto 最新报告做壳（通用型骨架），改写名字/emoji/关键词/日期后
套用 build_report 骨架逻辑产出 report_20260926.html + index.html，
再由 rebuild_index 重建归档列表。此后每日构建即可自我复制。

用法（在 repo/ 下）：python logs/bootstrap_recruit_regions.py
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
SHELL_REPORT = "report_20260926.html"
SHELL_NAME = tail_template.CATEGORY_NAMES[SHELL_CAT]
DT = datetime.datetime(2026, 9, 26)

REGIONS = {
    "xuzhou-recruit": {
        "name": "徐州招聘日报",
        "emoji": "💼",
        "kw": "徐工 · 校招 · 社招 · 工程机械岗位",
        "desc": "聚焦徐州工程机械之都招聘：徐工集团、徐工汽车等校招社招与投递提示",
        "idx_desc": "徐工与徐州工程机械企业招聘动态",
    },
    "nanjing-recruit": {
        "name": "南京招聘日报",
        "emoji": "📋",
        "kw": "长安马自达 · 南汽 · LG新能源 · 岗位速递",
        "desc": "聚焦南京汽车机械招聘：长安马自达、南汽、LG新能源滨江等岗位动态",
        "idx_desc": "南京汽车机械企业招聘动态",
    },
    "shanghai-recruit": {
        "name": "上海招聘日报",
        "emoji": "🌆",
        "kw": "特斯拉 · 上汽 · 智己 · 高端装备岗位",
        "desc": "聚焦上海汽车产业招聘：特斯拉上海、上汽系与高端装备岗位速递",
        "idx_desc": "特斯拉、上汽与上海汽车产业招聘",
    },
    "hangzhou-recruit": {
        "name": "杭州招聘日报",
        "emoji": "🚀",
        "kw": "零跑 · 吉利 · 校招 · 投递攻略",
        "desc": "聚焦杭州车企招聘：吉利、零跑等岗位动态与投递攻略",
        "idx_desc": "零跑、吉利与杭州车企招聘动态",
    },
    "jiangzhehu-recruit": {
        "name": "江浙沪招聘日报",
        "emoji": "🧭",
        "kw": "长三角 · 校招日历 · 社招 · 内推",
        "desc": "聚焦长三角汽车机械招聘：跨区域校招日历、社招岗位与内推信息",
        "idx_desc": "长三角汽车机械招聘汇总",
    },
    "hefei-recruit": {
        "name": "合肥招聘日报",
        "emoji": "🧪",
        "kw": "蔚来 · 江淮 · 大众安徽 · 新能源岗位",
        "desc": "聚焦合肥新能源汽车之都招聘：蔚来、江淮、大众安徽与产业岗位动态",
        "idx_desc": "蔚来、江淮与合肥新能源汽车产业招聘",
    },
    "anhui-recruit": {
        "name": "安徽招聘日报",
        "emoji": "⚙️",
        "kw": "奇瑞 · 江淮 · 全省招聘 · 岗位推荐",
        "desc": "聚焦安徽汽车强省招聘：奇瑞、江淮等全省汽车机械岗位全景",
        "idx_desc": "奇瑞与安徽全省汽车产业招聘",
    },
    "jiangsu-recruit": {
        "name": "江苏招聘日报",
        "emoji": "🛠️",
        "kw": "零部件 · 高端装备 · 苏州 · 常州岗位",
        "desc": "聚焦江苏汽车机械招聘：零部件与高端装备企业岗位速递",
        "idx_desc": "江苏汽车零部件与高端装备企业招聘",
    },
    "shenzhen-recruit": {
        "name": "深圳招聘日报",
        "emoji": "🌇",
        "kw": "比亚迪 · 机器人 · 校招 · 产业岗位",
        "desc": "聚焦深圳汽车与机器人产业招聘：比亚迪总部及智能制造岗位动态",
        "idx_desc": "比亚迪与深圳汽车机器人产业招聘",
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
