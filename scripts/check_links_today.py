#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""外链真实性核验：抽取 content/*.html 里所有 source-link href，去重后并发 curl。
判据：200/301/302/403/401 视为「存在」；只有 000/5xx 才需处理。
https 不通但 http 可访问的，给出 http 修正建议。
用法: python scripts/check_links_today.py [--fix]
"""
import argparse
import glob
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def probe(url):
    try:
        r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                            "-L", "--max-time", "20", "-A", UA, url],
                           capture_output=True, text=True, timeout=40)
        code = (r.stdout or "000").strip()
        return url, code
    except Exception:
        return url, "000"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="把 https 不可达而 http 可达的链接改写为 http")
    args = ap.parse_args()

    files = {}
    hrefs = {}
    for p in sorted(glob.glob(os.path.join(CONTENT, "*.html"))):
        s = open(p, encoding="utf-8").read()
        for m in re.finditer(r'class="source-link"\s+href="([^"]+)"', s):
            u = m.group(1).strip()
            hrefs.setdefault(u, set()).add(os.path.basename(p))
            files.setdefault(os.path.basename(p), 0)
            files[os.path.basename(p)] += 1

    urls = sorted(hrefs)
    print("唯一外链 %d 条（来自 %d 份正文）" % (len(urls), len(files)))
    # 并发不要太高：16 路并发会让部分站点超时，误报成「不通」
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(probe, urls))

    OK = ("200", "301", "302", "403", "401", "303", "307", "308", "206")
    bad, retry_http = [], []
    for u, code in results:
        if code in OK:
            continue
        if u.startswith("https://"):
            retry_http.append((u, code))
        else:
            bad.append((u, "http=%s" % code))

    fixed = {}
    if retry_http:
        print("\n[..] %d 条 https 首轮不通，先复测一次再回退 http" % len(retry_http))
        still = []
        with ThreadPoolExecutor(max_workers=4) as ex:
            for u, c2 in ex.map(lambda x: probe(x[0]), retry_http):
                if c2 in OK:
                    continue
                still.append((u, c2))
        with ThreadPoolExecutor(max_workers=4) as ex:
            for (orig, _), (u, code) in zip(still, ex.map(
                    lambda x: probe("http://" + x[0][len("https://"):]), still)):
                if code in OK:
                    fixed[orig] = code
                else:
                    bad.append((orig, "https=%s/http=%s" % (dict(still).get(orig, "000"), code)))

    print("\n=== 结果 ===")
    print("有效: %d" % (len(urls) - len(bad)))
    if fixed:
        print("\nhttps 不通但 http 可达（建议改写为 http）: %d 条" % len(fixed))
        for u, c in sorted(fixed.items()):
            print("  [%s] %s   ← %s" % (c, "http://" + u[len("https://"):], ", ".join(sorted(hrefs[u]))))
    if bad:
        print("\n真正不通（需人工确认/替换）: %d 条" % len(bad))
        for u, c in bad:
            print("  [%s] %s   ← %s" % (c, u, ", ".join(sorted(hrefs.get(u, [])))))
    if not fixed and not bad:
        print("全部通过 ✓")

    if args.fix and fixed:
        n = 0
        for p in glob.glob(os.path.join(CONTENT, "*.html")):
            s = open(p, encoding="utf-8").read()
            o = s
            for u in fixed:
                s = s.replace('href="%s"' % u, 'href="%s"' % ("http://" + u[len("https://"):]))
            if s != o:
                open(p, "w", encoding="utf-8", newline="\n").write(s)
                n += 1
        print("\n[OK] 已改写 %d 份正文的 http 链接" % n)

    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
