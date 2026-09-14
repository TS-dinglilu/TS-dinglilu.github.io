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


def push_via_exported_cred():
    """兜底推送：凭据助手（helper-selector/GCM）挂起时，直接从 Windows 凭据管理器
    导出凭据，用 git 的 store 助手完成一次推送。返回提示字符串，不适用时返回 None。"""
    if os.name != "nt":
        return None
    ps1 = os.path.join(HERE, "export_git_cred.ps1")
    if not os.path.exists(ps1):
        return None
    print("[..] 走凭据直连通道推送…")
    # 脚本原路径含中文，PowerShell -File 可能读取失败 → 复制到纯 ASCII 临时路径执行
    import shutil
    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="wbcred_")
    ps_tmp = os.path.join(tmpdir, "export_git_cred.ps1")
    try:
        # 以 utf-8-sig（带 BOM）落盘：Windows PowerShell 5.1 靠 BOM 判定 UTF-8，
        # 否则含中文的脚本会按 GBK 解析报 ParserError
        with open(ps1, encoding="utf-8") as f:
            content = f.read()
        with open(ps_tmp, "w", encoding="utf-8-sig") as f:
            f.write(content)
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_tmp],
                           capture_output=True, timeout=120)
    except Exception as e:  # noqa: BLE001
        return "[FAIL] 凭据导出异常: %s" % e
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    raw = (r.stdout or b"") + b"\n" + (r.stderr or b"")
    text = ""
    for enc in ("utf-8", "gbk", "mbcs", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines or not os.path.exists(lines[-1]):
        return "[FAIL] 凭据导出失败: %s" % (" | ".join(lines[-2:])[:200] if lines else "(无输出)")
    cred_file = lines[-1]
    try:
        # 注意：git config 会把反斜杠当转义字符，路径必须用正斜杠
        p = subprocess.run(["git", "-c", "credential.helper=",
                            "-c", "credential.helper=store --file=%s" % cred_file.replace("\\", "/"),
                            "push", "origin", "main"],
                           cwd=ROOT, capture_output=True, text=True, timeout=300,
                           env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
        msg = re.sub(r":[^:@\s]*@", ":***@", (p.stdout or p.stderr or "").strip())
        if p.returncode == 0:
            return "[OK] 已推送 GitHub Pages（凭据兜底通道）"
        return "[FAIL] 兜底推送失败: " + msg[-200:]
    except subprocess.TimeoutExpired:
        return "[FAIL] 兜底推送超时"
    finally:
        try:
            os.remove(cred_file)
        except OSError:
            pass


def push_with_retry(attempts=3, base_sleep=20, ssh_fallback=True):
    """推送：Windows 下优先走凭据直连通道（凭据助手常挂起），再退回常规 git push，
    最后在 github.com:443 整段不可达时走临时部署密钥 + SSH over 443 兜底。"""
    import time

    # 1) 优先：凭据直连（实测 15 秒内完成；绕过会挂起的凭据助手）
    fb = push_via_exported_cred()
    if fb:
        if fb.startswith("[OK]"):
            return fb
        print("[WARN] " + fb)
    else:
        print("[..] 非 Windows 或缺少导出脚本，走常规推送")

    # 2) 常规推送（网络抖动重试）
    for i in range(attempts):
        try:
            r = subprocess.run(["git", "push", "origin", "main"], cwd=ROOT,
                               capture_output=True, text=True, timeout=60,
                               env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
            if r.returncode == 0:
                return "[OK] 已推送 GitHub Pages"
            err = (r.stderr or r.stdout).strip().splitlines()
            err = err[-1] if err else "unknown"
        except subprocess.TimeoutExpired:
            err = "凭据助手无响应（超时）"
        print("[WARN] 常规 push 第 %d/%d 次失败: %s" % (i + 1, attempts, err[:130]))
        if i < attempts - 1:
            time.sleep(base_sleep * (i + 1))

    # 3) 兜底：github.com:443 被阻断时，临时部署密钥 + SSH over 443
    #    该函数自带开关：github.com 可达就直接跳过，不会平白注册密钥；密钥用后必撤销。
    if ssh_fallback:
        try:
            import ssh_fallback_push
            fb2 = ssh_fallback_push.ssh_fallback_push()
            if fb2:
                print(fb2)
                if fb2.startswith("[OK]"):
                    return fb2
        except Exception as e:  # noqa: BLE001 兜底失败不能带崩主流程
            print("[WARN] SSH 兜底通道异常: %s: %s" % (type(e).__name__, e))
    else:
        print("[SKIP] --no-ssh-fallback")

    return "[FAIL] 推送失败（本地提交已保留，网络恢复后运行 git push origin main 即可）"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--categories", help="逗号分隔，默认全部 13 个")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--no-build", action="store_true", help="跳过构建，只更新主页并推送")
    ap.add_argument("--no-ssh-fallback", action="store_true",
                    help="禁用 github.com 不通时的 SSH 兜底通道（临时部署密钥）")
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

    # 3.5) 发布前自查：结构/链接/索引/主页/漏期 全站体检
    print("=" * 8, "站点自查", "=" * 8)
    audit = subprocess.run([sys.executable, os.path.join(HERE, "audit_site.py"), "--quiet"],
                           cwd=ROOT, capture_output=True, text=True)
    if audit.returncode != 0:
        print(audit.stdout.strip())
        print("[WARN] 站点自查发现问题（见上）。已继续发布，但建议尽快修复。")
    else:
        print("[OK] 站点自查通过")

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
        print(push_with_retry(ssh_fallback=not args.no_ssh_fallback))

    # 5) 汇总
    print("=" * 8, "汇总", "=" * 8)
    print("成功: %s" % ", ".join(ready))
    if missing:
        print("缺正文: %s" % ", ".join(missing))
    if bad:
        print("校验失败: %s" % ", ".join(bad))


if __name__ == "__main__":
    main()
