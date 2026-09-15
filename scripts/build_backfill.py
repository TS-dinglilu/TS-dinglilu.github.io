#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补做漏跑日期：从指定正文目录批量构建某个历史日期的分类报告 + 重建索引。

用于自动化当天没跑（机器/应用离线）后的补漏。正文按 `<分类>.html` 命名放在
--dir 指向的目录里；缺失的分类会被跳过并列出，不会中断整体流程。

用法:
  python scripts/build_backfill.py --date 2026-09-10 --dir content/backfill0910
  python scripts/build_backfill.py --date 2026-09-10 --dir content/backfill0910 --push
  python scripts/build_backfill.py --date 2026-09-10 --dir content/backfill0910 --check
"""
import argparse
import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_report  # noqa: E402
import publish_all    # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="漏跑日期 YYYY-MM-DD")
    ap.add_argument("--dir", required=True, help="正文目录（含 <分类>.html）")
    ap.add_argument("--push", action="store_true", help="构建后提交推送")
    ap.add_argument("--check", action="store_true", help="只校验正文，不构建")
    ap.add_argument("--force", action="store_true",
                    help="目标报告已存在时也覆盖重建（默认跳过，避免误改已上线内容）")
    args = ap.parse_args()

    try:
        dt = datetime.datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("[ERROR] --date 需为 YYYY-MM-DD 格式: %s" % args.date)
        return 2

    src = os.path.abspath(args.dir)
    if not os.path.isdir(src):
        print("[ERROR] 正文目录不存在: %s" % src)
        return 2

    stamp = dt.strftime("%Y%m%d")
    print("=" * 10, "补做 %s（正文源: %s）" % (args.date, src), "=" * 10)

    built, skipped_exists, bad, missing = [], [], {}, []
    for c in publish_all.CATEGORIES:
        cpath = os.path.join(src, c + ".html")
        target = os.path.join(ROOT, c, "report_%s.html" % stamp)

        if not os.path.exists(cpath):
            missing.append(c)
            continue

        issues = publish_all.validate_content(cpath)
        if issues:
            bad[c] = issues
            print("[FAIL] %-22s %s" % (c, "; ".join(issues)))
            continue

        if os.path.exists(target) and not args.force:
            skipped_exists.append(c)
            print("[SKIP] %-22s 已存在 report_%s.html（加 --force 可覆盖）" % (c, stamp))
            continue

        if args.check:
            built.append(c)
            continue

        try:
            build_report.build_report(c, dt, cpath)
            build_report.rebuild_index(c)
            built.append(c)
        except SystemExit as e:
            bad[c] = ["构建失败: %s" % e]
            print("[FAIL] %s 构建失败: %s" % (c, e))

    print("=" * 10, "汇总", "=" * 10)
    print("成功: %d 个%s" % (len(built), (" → " + ", ".join(built)) if built else ""))
    if skipped_exists:
        print("已存在跳过: %s" % ", ".join(skipped_exists))
    if missing:
        print("缺正文（需补写）: %s" % ", ".join(missing))
    if bad:
        print("失败: %s" % ", ".join(bad))

    if args.push and built and not args.check:
        print("=" * 10, "更新主页 + 提交推送", "=" * 10)
        import subprocess
        subprocess.run([sys.executable, os.path.join(HERE, "update_homepage.py")], cwd=ROOT)
        subprocess.run(["git", "add", "-A"], cwd=ROOT)
        st = subprocess.run(
            ["git", "-c", "user.name=TS-dinglilu", "-c", "user.email=workbuddy@local",
             "commit", "-m", "补做漏跑日报 %s" % args.date],
            cwd=ROOT, capture_output=True, text=True)
        if st.returncode != 0:
            print("[WARN] commit: " + (st.stdout or st.stderr).strip()[:200])
        print(publish_all.push_with_retry())

    return 0


if __name__ == "__main__":
    sys.exit(main())
