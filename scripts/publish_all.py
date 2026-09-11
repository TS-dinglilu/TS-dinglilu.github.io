#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键发布：校验正文 → 批量构建 13 分类报告 + 索引 → 更新主页 → git 提交推送。

用法:
  python scripts/publish_all.py                     # 构建+更新主页（默认今天），不推送
  python scripts/publish_all.py --push              # 构建后提交并推送
  python scripts/publish_all.py --categories car-recruit,future-planning
  python scripts/publish_all.py --date 2026-09-10
"""
import argparse
import datetime
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_report  # noqa: E402

CATEGORIES = ["car-recruit", "mechanical-recruit", "school-news", "drone-research",
              "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
              "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
              "research-institute", "future-planning"]
CONTENT_DIR = os.path.join(os.path.dirname(ROOT), "content")


def validate_content(path):
    """返回问题列表；空列表 = 通过。"""
    s = open(path, encoding="utf-8").read()
    issues = []
    if re.search(r"<!DOCTYPE|<html[\s>]|<head[\s>]|<body[\s>]", s, re.I):
        issues.append("含完整文档标签（只应输出 main 内部内容）")
    md = re.search(r"\]\((https?://[^)]+)\)", s)
    if md:
        issues.append("Markdown 链接: " + md.group(1)[:60])
    if 'class="giscus"' not in s:
        issues.append("缺少 giscus 容器")
    if "信息来源" not in s:
        issues.append("缺少信息来源板块")
    if len(s) < 3000:
        issues.append("内容过短(%d 字符)" % len(s))
    return issues


def missing_dates(days=3):
    """检查最近 N 天里哪些日期没有报告（用于漏跑自查）。"""
    today = datetime.date.today()
    out = []
    for i in range(days):
        d = today - datetime.timedelta(days=i)
        stamp = d.strftime("%Y%m%d")
        have = all(glob.glob(os.path.join(ROOT, c, "report_%s.html" % stamp)) for c in CATEGORIES)
        out.append((d.isoformat(), have))
    return out


def push_with_retry(attempts=6, base_sleep=45):
    """带退避的推送。国内网络下 github.com 时常不可达，退避重试能显著提高成功率。"""
    import time
    for i in range(attempts):
        r = subprocess.run(["git", "push", "origin", "main"], cwd=ROOT,
                           capture_output=True, text=True, timeout=180,
                           env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
        if r.returncode == 0:
            return "[OK] 已推送 GitHub Pages"
        err = (r.stderr or r.stdout).strip().splitlines()
        err = err[-1] if err else "unknown"
        print("[WARN] push 第 %d/%d 次失败: %s" % (i + 1, attempts, err[:130]))
        if i < attempts - 1:
            time.sleep(base_sleep * (i + 1))
    return "[FAIL] 推送失败（本地提交已保留，网络恢复后运行 git push origin main 即可）"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--categories", help="逗号分隔，默认全部 13 个")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--no-build", action="store_true", help="跳过构建，只更新主页并推送")
    args = ap.parse_args()

    cats = [c.strip() for c in args.categories.split(",")] if args.categories else CATEGORIES
    dt = datetime.datetime.strptime(args.date, "%Y-%m-%d")

    # 0) 漏跑自查
    miss = [d for d, have in missing_dates(3) if not have]
    if miss:
        print("[注意] 最近 3 天缺失报告: %s （如需补齐，请为这些日期生成正文并分别构建）" % ", ".join(miss))

    # 1) 校验
    print("=" * 8, "校验正文", "=" * 8)
    ready, missing, bad = [], [], {}
    for c in cats:
        p = os.path.join(CONTENT_DIR, c + ".html")
        if not os.path.exists(p):
            missing.append(c)
            continue
        issues = validate_content(p)
        if issues:
            bad[c] = issues
        else:
            ready.append(c)
    for c, iss in bad.items():
        print("[FAIL] %s: %s" % (c, "; ".join(iss)))
    if missing:
        print("[SKIP] 无正文文件: %s" % ", ".join(missing))
    print("[READY] %d/%d 通过校验" % (len(ready), len(cats)))

    # 2) 构建
    if not args.no_build:
        print("=" * 8, "构建报告 %s" % args.date, "=" * 8)
        for c in ready:
            try:
                build_report.build_report(c, dt, os.path.join(CONTENT_DIR, c + ".html"))
                build_report.rebuild_index(c)
            except SystemExit as e:
                print("[FAIL] %s 构建失败: %s" % (c, e))
    else:
        print("[SKIP] --no-build")

    # 3) 主页
    print("=" * 8, "更新主页", "=" * 8)
    subprocess.run([sys.executable, os.path.join(HERE, "update_homepage.py")], cwd=ROOT)

    # 4) 提交推送
    if args.push:
        print("=" * 8, "提交推送", "=" * 8)
        subprocess.run(["git", "add", "-A"], cwd=ROOT)
        msg = "每日日报自动更新 %s" % args.date
        st = subprocess.run(["git", "-c", "user.name=TS-dinglilu", "-c",
                             "user.email=workbuddy@local", "commit", "-m", msg],
                            cwd=ROOT, capture_output=True, text=True)
        if st.returncode != 0:
            print("[WARN] commit: " + (st.stdout or st.stderr).strip()[:160])
        print(push_with_retry())

    # 5) 汇总
    print("=" * 8, "汇总", "=" * 8)
    print("成功: %s" % ", ".join(ready))
    if missing:
        print("缺正文: %s" % ", ".join(missing))
    if bad:
        print("校验失败: %s" % ", ".join(bad))


if __name__ == "__main__":
    main()
