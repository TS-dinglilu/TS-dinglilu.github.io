#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站 HTML「head 层」优化器（幂等）。

背景：站点有 798+ 份报告，存在几类全站一致的结构性缺陷，逐个手改不现实，
而 build_report 只影响「新建」的报告 —— 历史存量必须由回溯脚本收敛。
本脚本把各项优化做成可重复运行的 pass，跑多少次结果都一样（幂等）。

设计原则（务必遵守，否则会造成难以察觉的站点级损坏）：
 1. **只在 <head> 区间内增删/hint**，绝不触碰 <body> 正文内容，避免破坏文章。
 2. **每个 pass 必须先自增判定**：已处理过的文件要能就地识别并跳过，
    所以 OP_TAG 注释会被打进 head，作为「这批优化已落地」的指纹。
 3. **写回前做完整性校验**：</head>/</body>/</html> 齐全、无重复 <!DOCTYPE>、
    <div> 与 </div> 数量不发生漂移（head 内本不应有 div，漂移即异常）。
 4. **默认 dry-run**：必须显式传 --apply 才落盘，防止误操作全站。

用法：
  python scripts/optimize_site.py                 # 预演，列出将改动的文件与项
  python scripts/optimize_site.py --apply         # 实际改写
  python scripts/optimize_site.py --only fonts    # 只跑某一项（逗号分隔）
  python scripts/optimize_site.py --file index.html
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001  非 TTY 环境可能不支持，忽略即可
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail_template  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_BASE = getattr(tail_template, "SITE_BASE", "https://ts-dinglilu.github.io")
COVER_IMAGE = SITE_BASE + "/assets/cover.png"

# —— 本地字体栈：取代原先从 Google Fonts 下载的 Noto Sans SC / JetBrains Mono ——
# 顺序讲究：先取各平台「系统原生中文字体」（观感最佳、零网络请求），
# Noto Sans SC 退居其后（若用户本机装过则命中），最后落到通用 sans-serif。
LOCAL_SANS = ('-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", '
              '"Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif')
LOCAL_MONO = ('ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, '
              '"Liberation Mono", "Courier New", monospace')
# 全站内联 <style> 里实际出现的两种字体声明写法（已枚举确认，无其它变体）
MONO_DECL = "'JetBrains Mono', monospace"
SANS_DECL = "'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

OP_TAG = "<!-- optimize_site:head -->"
OP_VERSION = "2026-10-15.1"

# —— 处理范围：只改报告页/分类归档页/主页/404/digest，不动 content 草稿与基建 ——
SKIP_DIRS = {".git", "logs", "scripts", "content", ".github", ".workbuddy",
             "assets", "__pycache__", "backups"}

# ============================================================
# 各优化项
# ============================================================

FONTS_PATTERNS = [
    r'<link[^>]*fonts\.googleapis\.com[^>]*>\s*',
    r'<link[^>]*fonts\.gstatic\.com[^>]*>\s*',
]
# 主页把整份 CSS 内联进 <style>，其中 @import 同样会去 Google Fonts 取字体。
# @import 比 <link> 更糟：要先拿到 CSS 才开始解析这条依赖项，串行阻塞两轮 RTT。
FONTS_IMPORT = r'@import\s+url\(\s*[\'"]?https://fonts\.googleapis\.com[^\'")]*[\'"]?\s*\)\s*;\s*'

CACHE_PATTERNS = [
    r'<meta\s+http-equiv="Cache-Control"[^>]*>\s*',
    r'<meta\s+http-equiv="Pragma"[^>]*>\s*',
    r'<meta\s+http-equiv="Expires"[^>]*>\s*',
]


def already_applied(head: str) -> bool:
    """幂等指纹：本版本（或更新版本）已处理过就不再动 head 区。"""
    m = re.search(r'<!-- optimize_site:head(\s+ver=([\w.\-]+))? -->', head)
    if not m:
        return False
    return (m.group(2) or "0") == OP_VERSION


def opt_fonts(html: str, ctx: dict) -> tuple[str, bool]:
    """移除 Google Fonts 外链。

    这些是渲染阻塞型 <link rel=stylesheet>。字体服务器在国内直连不可达，
    浏览器会一直等到连接超时才继续渲染 → 首屏白屏数秒。
    CSS 里已有系统字体回退栈，去掉后观感不变、可用性显著提升。
    """
    head = ctx["head"]
    new, n = re.subn("|".join(FONTS_PATTERNS), "", head, flags=re.I)
    new, n2 = re.subn(FONTS_IMPORT, "", new, flags=re.I)
    if not (n or n2):
        return html, False
    ctx["head"] = new
    return _reassemble(html, ctx), True


def opt_fontstack(html: str, ctx: dict) -> tuple[str, bool]:
    """把内联 <style> 里的字体声明换成本地字体栈。

    assets/report.css 已由 upgrade_css.py 处理；但另有 36 个页面（主页/404/
    各分类归档页/digest）把 CSS 内联进了 <style>，它们是独立副本、不会跟着变，
    必须在这里一并替换，否则这些页面仍会引用已不再加载的网络字体。
    """
    head = ctx["head"]
    nm, ns = head.count(MONO_DECL), head.count(SANS_DECL)
    if not (nm or ns):
        return html, False
    head = head.replace(MONO_DECL, LOCAL_MONO).replace(SANS_DECL, LOCAL_SANS)
    ctx["head"] = head
    return _reassemble(html, ctx), True


def opt_cache(html: str, ctx: dict) -> tuple[str, bool]:
    """去掉无效且有害的 no-cache 三件套。

    HTTP 响应头优先级高于 <meta http-equiv>，GitHub Pages 自己会下发
    cache-control，所以这三个标记通常不生效，只是每页多背约 200 字节。
    更糟的是它会误导后来的维护者以为「已缓存控制」。直接删掉。
    """
    head = ctx["head"]
    new, n = re.subn("|".join(CACHE_PATTERNS), "", head, flags=re.I)
    if not n:
        return html, False
    ctx["head"] = new
    return _reassemble(html, ctx), True


def _canonical_url(rel: str) -> str:
    """把仓库相对路径转成站点的规范 URL。

    目录型路径（…/index.html）收敛到目录本身，保持「一个页面一个 URL」，
    避免出现 /car-recruit/ 与 /car-recruit/index.html 两个自相竞争的入口。
    """
    rel = rel.replace("\\", "/").lstrip("/")
    # 注意锚定 ^|/ ：否则 "car-recruit/index.html" 会被误拼成 "car-recruit//"
    rel = re.sub(r"(^|/)index\.html$", "/", rel)
    if rel in ("", "/"):          # 站点根，不能拼成 "//"
        return SITE_BASE + "/"
    return SITE_BASE + "/" + rel


def opt_canonical(html: str, ctx: dict) -> tuple[str, bool]:
    """修正 canonical / og:url —— 全站 798 份报告原本全部指向所属分类首页。

    后果比看起来严重：搜索引擎会把同一分类下几百份日报判成首页的重复内容，
    真正有内容的报告页反而进不了索引。这里改为指向页面自身，
    并用 og:url 與 canonical 保持一致。
    """
    head, can = ctx["head"], _canonical_url(ctx["rel"])
    changed = False
    cur = re.search(r'<link rel="canonical" href="([^"]+)"', head)
    line = '<link rel="canonical" href="%s">' % can
    if cur and cur.group(1) != can:
        # 按切片替换而非 str.replace：正则 group(0) 不含结尾的 '>'，
        # 若直接 replace 会在行尾多留一个 '>' 出来。
        head = head[:cur.start()] + line + head[cur.end():]
        changed = True
    elif not cur:
        head = _inject_after_title(head, line)
        changed = True

    for prop in ("og:url",):
        m = re.search(r'<meta property="%s" content="([^"]+)"' % prop, head)
        line = '<meta property="%s" content="%s">' % (prop, can)
        if m and m.group(1) != can:
            head = head[:m.start()] + line + head[m.end():]
            changed = True
        elif not m:
            head = _inject_after_title(head, line)
            changed = True

    if not changed:
        return html, False
    ctx["head"] = head
    return _reassemble(html, ctx), True


def opt_theme(html: str, ctx: dict) -> tuple[str, bool]:
    """补 theme-color：移动端浏览器会把地址栏染成站点主色，观感一体化。"""
    head = ctx["head"]
    if re.search(r'name="theme-color"', head, re.I):
        return html, False
    line = '<meta name="theme-color" content="#0a0e1a">'
    ctx["head"] = _inject_after_title(head, line)
    return _reassemble(html, ctx), True


def opt_og_tags(html: str, ctx: dict) -> tuple[str, bool]:
    """补 og:image / og:type:article / article:published_time。

    没有 og:image 时，链接被分享到微信/QQ/微博会退化成无任何缩略图的纯文字卡片。
    报告页本质是一篇文章，og:type 标成 website 并不准确。
    """
    head = ctx["head"]
    changed = False
    if not re.search(r'property="og:image"', head):
        line = '<meta property="og:image" content="%s">' % COVER_IMAGE
        head = _inject_after_title(head, line)
        changed = True
    if ctx.get("kind") == "report" and not re.search(r'property="og:type" content="article"', head):
        head = re.sub(r'<meta property="og:type" content="website">',
                      '<meta property="og:type" content="article">', head, count=1)
        head = _inject_after_title(
            head, '<meta property="article:published_time" content="%s">' % ctx["iso"])
        changed = True
    if not changed:
        return html, False
    ctx["head"] = head
    return _reassemble(html, ctx), True


def opt_jsonld(html: str, ctx: dict) -> tuple[str, bool]:
    """注入 schema.org JSON-LD 结构化数据。

    搜索引擎读不懂 HTML 排版，但读得懂这段 JSON。有了它，报告页才有机会以
    「带日期的文章」形态被理解（富摘要/站点内搜索链接的基础）。
    """
    head = ctx["head"]
    if "application/ld+json" in head:
        return html, False
    url = _canonical_url(ctx["rel"])
    name = tail_template.CATEGORY_NAMES.get(ctx["category"], ctx["category"])
    if ctx["kind"] == "report":
        title = "%s - %s" % (name, ctx.get("title_cn", ctx["iso"]))
        data = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "datePublished": ctx["iso"],
            "dateModified": ctx["iso"],
            "inLanguage": "zh-CN",
            "url": url,
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "author": {"@type": "Person", "name": "张恒辰"},
            "publisher": {"@type": "Organization", "name": "TS-dinglilu 自动化日报"},
            "isPartOf": {
                "@type": "Blog",
                "name": name,
                "url": "%s/%s/" % (SITE_BASE, ctx["category"]),
            },
            "image": COVER_IMAGE,
        }
    else:
        data = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": name,
            "url": url,
            "inLanguage": "zh-CN",
            "isPartOf": {"@type": "WebSite", "name": "TS-dinglilu 自动化日报",
                         "url": SITE_BASE + "/"},
        }
    block = '<script type="application/ld+json">\n%s\n</script>' % json.dumps(
        data, ensure_ascii=False, indent=None)
    ctx["head"] = head.rstrip() + "\n" + block + "\n"
    return _reassemble(html, ctx), True


# ============================================================
# head 区操作工具
# ============================================================

def _inject_after_title(head: str, line: str) -> str:
    """把一行插到 <title> 之后；没有 title 就退化为插到 head 末尾。"""
    mt = re.search(r"</title>", head, re.I)
    if mt:
        return head[:mt.end()] + "\n" + line + head[mt.end():]
    return head.rstrip() + "\n" + line + "\n"


def _reassemble(html: str, ctx: dict) -> str:
    return html[:ctx["span"][0]] + ctx["head"] + html[ctx["span"][1]:]


def stamp_version(head: str) -> str:
    """打上版本指纹，让下一次运行知道这批已做过。"""
    if OP_TAG in head:
        return re.sub(r'<!-- optimize_site:head[^>]*-->', OP_TAG, head)
    return head.rstrip() + "\n" + OP_TAG + "\n"


def validate(original: str, new: str) -> None:
    """写回前的完整性闸门。宁可不改，也不能把站点改坏。"""
    for token in ("</head>", "</body>", "</html>"):
        if new.count(token) != original.count(token):
            raise ValueError("标签数量漂移: %s (%d -> %d)" % (
                token, original.count(token), new.count(token)))
    if not new.rstrip().endswith("</html>"):
        raise ValueError("结尾缺失 </html>")
    if len(re.findall(r"<!DOCTYPE", new, re.I)) != 1:
        raise ValueError("DOCTYPE 数量异常")
    if new.count("<div") != original.count("<div"):
        raise ValueError("<div> 数量漂移，可能误伤了正文")


PASSES = {
    "fonts": opt_fonts,
    "fontstack": opt_fontstack,
    "cache": opt_cache,
    "canonical": opt_canonical,
    "theme": opt_theme,
    "og": opt_og_tags,
    "jsonld": opt_jsonld,
}


# ============================================================
# 遍历与执行
# ============================================================

def collect_files(only_rel=None):
    if only_rel:
        return [only_rel]
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        parts = rel.split("/")
        if parts[0] in SKIP_DIRS:
            continue
        out.append(rel)
    return out


def build_ctx(rel: str, html: str) -> dict | None:
    m = re.search(r"<head[^>]*>(.*?)</head>", html, re.S | re.I)
    if not m:
        print("  [skip] 无标准 <head>: %s" % rel)
        return None
    parts = rel.split("/")
    category = parts[0] if len(parts) > 1 else ""
    kind = "page"
    iso = ""
    title_cn = ""
    dm = re.search(r"report_(\d{8})\.html", rel)
    if dm:
        kind = "report"
        d = datetime.datetime.strptime(dm.group(1), "%Y%m%d")
        iso = d.strftime("%Y-%m-%d")
        title_cn = "%d年%d月%d日" % (d.year, d.month, d.day)
    elif re.search(r"(weekly|monthly|yearly)_\d+.*\.html", rel):
        kind = "digest"
        iso = datetime.date.today().isoformat()
    return {"rel": rel, "category": category, "kind": kind, "iso": iso,
            "title_cn": title_cn, "head": m.group(1), "span": m.span(1)}


def run(apply=False, only=None, target=None, quiet=False):
    files = collect_files(target)
    wanted = [p.strip() for p in only.split(",")] if only else list(PASSES)
    unknown = [w for w in wanted if w not in PASSES]
    if unknown:
        print("[ERROR] 未知优化项: %s" % ", ".join(unknown))
        return 1

    stats = {k: 0 for k in wanted}
    touched, failed, skipped = 0, 0, 0
    for rel in files:
        path = os.path.join(ROOT, rel)
        original = open(path, encoding="utf-8").read()
        ctx = build_ctx(rel, original)
        if ctx is None:
            skipped += 1
            continue
        cur = original
        done = []
        this_failed = False
        for key in wanted:
            # head 可能已被前一个 pass 改写，需同步回 ctx
            ctx = build_ctx(rel, cur) or ctx
            try:
                cur, changed = PASSES[key](cur, ctx)
            except Exception as e:  # noqa: BLE001
                print("  [ERROR] %s 处理失败 %s: %s" % (key, rel, e))
                this_failed = True
                break
            if changed:
                stats[key] += 1
                done.append(key)
        if this_failed:
            failed += 1
            continue
        if not done:
            continue

        # 打版本指纹（幂等闸门）
        hm = re.search(r"<head[^>]*>(.*?)</head>", cur, re.S | re.I)
        head_new = stamp_version(hm.group(1))
        cur = cur[:hm.span(1)[0]] + head_new + cur[hm.span(1)[1]:]

        try:
            validate(original, cur)
        except ValueError as e:
            print("  [ERROR] 校验不过，已跳过: %s -> %s" % (rel, e))
            failed += 1
            continue

        touched += 1
        if not quiet:
            print("  [fix] %-46s %s" % (rel, ",".join(done)))
        if apply:
            open(path, "w", encoding="utf-8", newline="").write(cur)

    mode = "已改写" if apply else "预演(未写盘)"
    print("\n=== %s ===\n受影响文件 %d，跳过 %d，失败 %d" % (mode, touched, skipped, failed))
    for k in wanted:
        print("  %-10s %d 处" % (k, stats[k]))
    if not apply and touched:
        print("\n这仅是预演。确认无误后加 --apply 落盘。")
    return 0 if failed == 0 else 2


def main():
    ap = argparse.ArgumentParser(description="全站 head 层优化（幂等）")
    ap.add_argument("--apply", action="store_true", help="实际写盘（默认仅预演）")
    ap.add_argument("--only", help="只跑指定项，逗号分隔：%s" % ",".join(PASSES))
    ap.add_argument("--file", help="只处理单个文件（相对仓库根）")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    return run(apply=a.apply, only=a.only, target=a.file, quiet=a.quiet)


if __name__ == "__main__":
    sys.exit(main())
