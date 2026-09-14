#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全站修复器：一次性修掉历史报告里的确定性缺陷（幂等，可重复执行）。

修复项
  1. 死链：指向已不存在路径的站点链接（如 /car-recruit-news/ → /car-recruit/）
  2. 旧品牌：TRAE / TraeWork Automation → WorkBuddy Automation
  3. 缺失评论区：正文里完全没有 giscus 的老报告，补一个标准评论区
  4. 重复 <body> 标签
  5. 指向废弃页 homepage_index.html 的返回链接 → ../index.html

不修复（有意保留）：老报告的页脚写法差异、来源板块措辞差异 —— 这些是历史风格，
功能正常，改动收益低而风险高。

用法:
  python scripts/fix_site.py --dry-run     # 只报告将要做的改动
  python scripts/fix_site.py               # 实际修复
"""
import argparse
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORIES = ["car-recruit", "mechanical-recruit", "school-news", "drone-research",
              "ahut-campus", "byd-recruit", "chery-recruit", "geely-recruit",
              "xiaomi-recruit", "weixiaoli-recruit", "traditional-auto",
              "research-institute", "future-planning"]
VALID = set(CATEGORIES)

# 已知的历史错误子路径 → 正确分类
BAD_PATHS = {
    "car-recruit-news": "car-recruit",
    "mechanical-recruit-news": "mechanical-recruit",
    "drone-research-daily": "drone-research",
    "ahut-campus-info": "ahut-campus",
    "research-institute-recruit": "research-institute",
}

COMMENT_BLOCK = """<!-- 评论区 -->
<div style="max-width:860px;margin:40px auto 0;padding:24px 20px;background:rgba(20,28,48,0.9);border-radius:12px;border:1px solid rgba(0, 212, 255, 0.12);">
<h2 style="font-size:1.1rem;margin-bottom:6px">💬 评论区</h2>
<p>登录 GitHub 账号即可评论，支持 Markdown 和表情回应。历史报告也可评论。</p>
<script src="https://giscus.app/client.js" data-repo="TS-dinglilu/TS-dinglilu.github.io" data-repo-id="R_kgDOTjqaJQ" data-category="General" data-category-id="DIC_kwDOTjqaJc4DCIL2" data-mapping="pathname" data-strict="0" data-reactions-enabled="1" data-emit-metadata="0" data-input-position="top" data-theme="dark_dimmed" data-lang="zh-CN" crossorigin="anonymous" async></script>
</div>
"""

stats = {"死链": 0, "旧品牌": 0, "补评论区": 0, "重复body": 0, "废弃页链接": 0}
changed_files = []


def fix_text(s, rel, log):
    """对单个文件内容做全部修复，返回 (新内容, 是否变化)。"""
    orig = s

    # 1) 死链：同时覆盖 href="/xxx/" 与正文纯文本 "ts-dinglilu.github.io/xxx"（可能无尾部斜杠）
    def _path_sub(m):
        bad = m.group(1)
        if bad in BAD_PATHS:
            stats["死链"] += 1
            log.append("死链: /%s → /%s/" % (bad, BAD_PATHS[bad]))
            return "ts-dinglilu.github.io/%s/" % BAD_PATHS[bad]
        return m.group(0)

    s = re.sub(r"ts-dinglilu\.github\.io/([a-z\-]+)(?=[/\"'\s<)]|$)", _path_sub, s, flags=re.M)
    # 上一轮替换会在路径后强制补 "/"，避免与已带斜杠的原写法产生 "//"
    s = re.sub(r"ts-dinglilu\.github\.io/([a-z\-]+)//+", r"ts-dinglilu.github.io/\1/", s)

    # 2) 旧品牌
    n_brand = len(re.findall(r"TRAE Automation|TraeWork Automation", s))
    if n_brand:
        s = re.sub(r"TRAE Automation|TraeWork Automation", "WorkBuddy Automation", s)
        stats["旧品牌"] += n_brand
        log.append("旧品牌: %d 处 → WorkBuddy Automation" % n_brand)

    # 3) 废弃页返回链接
    n_home = s.count("../homepage_index.html")
    if n_home:
        s = s.replace("../homepage_index.html", "../index.html")
        stats["废弃页链接"] += n_home
        log.append("废弃页链接: %d 处 → ../index.html" % n_home)

    # 4) 重复 <body>
    new_s = re.sub(r"(<body[^>]*>)\s*(?:<body[^>]*>\s*)+", r"\1", s)
    if new_s != s:
        stats["重复body"] += 1
        log.append("重复 <body> 已合并")
        s = new_s

    # 5) 补评论区（仅当完全没有 giscus 时）
    if "giscus.app" not in s and "</body>" in s:
        s = s.replace("</body>", COMMENT_BLOCK + "\n</body>", 1)
        stats["补评论区"] += 1
        log.append("补评论区（原文件完全无 giscus）")

    return s, s != orig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(set(
        glob.glob(os.path.join(ROOT, "*", "*.html"))       # 各分类报告 + 分类索引
        + glob.glob(os.path.join(ROOT, "*.html"))          # 站点主页等根级页面
    ))

    for f in files:
        if not os.path.exists(f):
            continue
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        s = open(f, encoding="utf-8").read()
        log = []
        new_s, changed = fix_text(s, rel, log)
        if changed:
            changed_files.append(rel)
            print("[%s] %s" % ("DRY" if args.dry_run else "FIX", rel))
            for l in log:
                print("      · " + l)
            if not args.dry_run:
                open(f, "w", encoding="utf-8").write(new_s)

    print("\n" + "=" * 60)
    print("改动文件数: %d" % len(changed_files))
    for k, v in stats.items():
        print("  %-12s %d" % (k, v))
    if args.dry_run:
        print("（dry-run，未写入任何文件）")


if __name__ == "__main__":
    main()
