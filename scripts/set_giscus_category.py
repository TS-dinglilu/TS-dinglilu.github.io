#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
切换全站 giscus 评论分类。

背景：站点原先用 Announcements 分类，该分类在 GitHub Discussions 中仅维护者可发帖，
访客无法创建讨论 → 评论功能实际不可用。改用 General / Q&A 后访客可正常评论。

用法:
  python scripts/set_giscus_category.py --name General --id DIC_kwDOxxxxxxxx --dry-run
  python scripts/set_giscus_category.py --name General --id DIC_kwDOxxxxxxxx

ID 获取方式：打开 https://giscus.app/zh-CN ，填入仓库 TS-dinglilu/TS-dinglilu.github.io，
在 "Discussion 分类" 选择 General，页面生成的配置代码里 data-category-id 即为所需 ID。
"""
import argparse
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD_NAME = "Announcements"
OLD_ID = "DIC_kwDOTjqaJc4DCIL1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="新的分类名，如 General")
    ap.add_argument("--id", required=True, dest="cat_id", help="新的分类 ID，如 DIC_kwDO...")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not re.match(r"^DIC_[A-Za-z0-9_-]{8,}$", args.cat_id):
        print("[ERROR] 分类 ID 格式不对，应形如 DIC_kwDOxxxxxxxx")
        return 1

    targets = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
        for fn in filenames:
            if fn.endswith((".html", ".py", ".md")):
                targets.append(os.path.join(dirpath, fn))

    changed = []
    for path in targets:
        s = open(path, encoding="utf-8").read()
        orig = s
        s = s.replace('data-category="%s"' % OLD_NAME, 'data-category="%s"' % args.name)
        s = s.replace("data-category-id='%s'" % OLD_ID, "data-category-id='%s'" % args.cat_id)
        s = s.replace('data-category-id="%s"' % OLD_ID, 'data-category-id="%s"' % args.cat_id)
        s = s.replace("'%s'" % OLD_ID, "'%s'" % args.cat_id)
        if s != orig:
            changed.append(os.path.relpath(path, ROOT))
            if not args.dry_run:
                open(path, "w", encoding="utf-8").write(s)

    print("[%s] 待修改文件 %d 个 -> 分类 %s (%s)" %
          ("DRY-RUN" if args.dry_run else "OK", len(changed), args.name, args.cat_id))
    for c in changed[:15]:
        print("   " + c)
    if len(changed) > 15:
        print("   ... 其余 %d 个" % (len(changed) - 15))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
