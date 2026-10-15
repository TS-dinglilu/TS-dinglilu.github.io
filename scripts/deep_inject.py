#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 content/deep/<分类>.html 的「深度档案」板块注入当天构建好的报告。

用法：
  python scripts/deep_inject.py                 # 注入今天(本地日期)的报告
  python scripts/deep_inject.py --date 20261014 # 指定日期
  python scripts/deep_inject.py --push          # 注入后 git add -A + commit + push

规则：
  - 深度档案文件：content/deep/<分类>.html（存在才处理对应分类）
  - 目标报告：<分类>/report_<date>.html
  - 注入点：报告中第一个 <div class="section"> 之前
  - 幂等：报告里已含「🔍 深度档案」则跳过
"""
import argparse
import datetime
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEEP_DIR = os.path.join(ROOT, "content", "deep")
MARK = "\U0001F50D 深度档案"  # 🔍 深度档案


def inject(cat, date):
    deep_path = os.path.join(DEEP_DIR, cat + ".html")
    if not os.path.exists(deep_path):
        return None
    report = os.path.join(ROOT, cat, "report_%s.html" % date)
    if not os.path.exists(report):
        return None
    s = open(report, encoding="utf-8").read()
    if MARK in s:
        return "skip"
    deep = open(deep_path, encoding="utf-8").read().strip()
    m = re.search(r'<div class="section">', s)
    if not m:
        return "no-section"
    s2 = s[: m.start()] + deep + "\n\n" + s[m.start():]
    open(report, "w", encoding="utf-8", newline="\n").write(s2)
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().strftime("%Y%m%d"))
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    cats = [os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(DEEP_DIR, "*.html"))]
    cats.sort()
    done, skipped, failed = [], [], []
    for c in cats:
        try:
            r = inject(c, args.date)
        except Exception as e:  # noqa: BLE001
            print("[FAIL] %s: %s" % (c, e))
            failed.append(c)
            continue
        if r == "ok":
            done.append(c)
        elif r in ("skip", "no-section") or r is None:
            skipped.append((c, r))
        else:
            failed.append(c)
    print("[OK] 注入 %d 份: %s" % (len(done), ", ".join(done)))
    print("[SKIP] %d 份" % len(skipped))
    if failed:
        print("[FAIL] %d 份: %s" % (len(failed), ", ".join(failed)))

    if args.push and done:
        subprocess.run(["git", "add", "-A"], cwd=ROOT, check=False)
        msg = "深度档案注入 %s（%d 分类）" % (args.date, len(done))
        r = subprocess.run(
            ["git", "-c", "user.name=TS-dinglilu", "-c", "user.email=workbuddy@local",
             "commit", "-m", msg],
            cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
            print("[FAIL] commit:", r.stdout, r.stderr)
            sys.exit(1)
        p = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
        print("[PUSH] rc=%d %s" % (p.returncode, (p.stdout + p.stderr).strip()[:300]))
        if p.returncode != 0:
            print("[提示] 常规 push 失败，请跑：python logs/push_manual.py")


if __name__ == "__main__":
    main()
