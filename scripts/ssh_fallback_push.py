#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
github.com:443 不可达时的兜底推送：临时部署密钥 + SSH over 443。

背景
----
国内网络下 `github.com:443` 会整段不可达（直连与本地代理都到不了），但
`ssh.github.com:443`、`github.com:22`、`api.github.com` 通常仍然可用。
此时 HTTPS 推送无路可走，改造流程如下：

  1. 从 Windows 凭据管理器导出 git 凭据（复用 scripts/export_git_cred.ps1），取出 token；
  2. `ssh-keygen` 生成一次性 ed25519 密钥（放在纯 ASCII 临时目录，中文路径会干扰 GIT_SSH_COMMAND）；
  3. 用 token 调 `POST /repos/<owner>/<repo>/keys` 把它注册为**可写**部署密钥；
  4. `GIT_SSH_COMMAND` 指定该私钥，走 `ssh://git@ssh.github.com:443/<owner>/<repo>.git` 推送；
  5. finally 中 `DELETE /repos/<owner>/<repo>/keys/<id>` 立即撤销，并删除本地私钥与凭据临时文件。

安全约定
--------
- 仅在「常规推送已失败」后作为兜底调用；先探测 `github.com:443`，**通了就直接返回不适用**，
  不会平白注册密钥。
- 不改变远端历史：走的是普通快进推送，与 HTTPS 通道等价。
- 部署密钥存活时间只有数秒，用后立即撤销，脚本会打印撤销结果以便核对。
- token 只从 export_git_cred.ps1 导出的临时文件读取，脚本结束即删除；日志中一律打码。

用法
----
  python scripts/ssh_fallback_push.py                  # 执行兜底推送（不可用时自动跳过）
  python scripts/ssh_fallback_push.py --selftest       # 自检：注册密钥 → SSH 认证 → 撤销，不推送
  python scripts/ssh_fallback_push.py --check          # 只探测通道连通性
  python scripts/ssh_fallback_push.py --force          # 跳过 github.com 探测，强制走一次
"""
import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SSH_HOST = "ssh.github.com"
SSH_PORT = 443
API_BASE = os.environ.get("GITHUB_API_BASE", "https://api.github.com")


# --------------------------------------------------------------------------- #
# 基础工具
# --------------------------------------------------------------------------- #
def _log(msg):
    print(msg, flush=True)


def tcp_open(host, port, timeout=8):
    """TCP 连通性探测（不依赖 DNS 之外的东西，失败一律返回 False）。"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def repo_slug():
    """从 origin 远端地址解析出 owner/repo。"""
    try:
        url = subprocess.run(["git", "config", "--get", "remote.origin.url"],
                             cwd=ROOT, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:  # noqa: BLE001
        url = ""
    m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", url)
    return "%s/%s" % (m.group(1), m.group(2)) if m else None


# --------------------------------------------------------------------------- #
# 凭据
# --------------------------------------------------------------------------- #
def export_cred_file():
    """调用 export_git_cred.ps1 导出凭据，返回临时文件路径（调用方负责删除）。失败抛异常。"""
    if os.name != "nt":
        raise RuntimeError("仅支持 Windows（凭据管理器导出）")
    ps1 = os.path.join(HERE, "export_git_cred.ps1")
    if not os.path.exists(ps1):
        raise RuntimeError("缺少 scripts/export_git_cred.ps1")
    tmpdir = tempfile.mkdtemp(prefix="wbcred_")
    ps_tmp = os.path.join(tmpdir, "export_git_cred.ps1")
    with open(ps1, encoding="utf-8") as f:
        content = f.read()
    # PowerShell 5.1 靠 BOM 判定 UTF-8，含中文的脚本必须带 BOM 落盘
    with open(ps_tmp, "w", encoding="utf-8-sig") as f:
        f.write(content)
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_tmp],
                           capture_output=True, timeout=120)
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
        raise RuntimeError("凭据导出失败: " + (" | ".join(lines[-2:])[:180] if lines else "(无输出)"))
    return lines[-1]


def read_token(cred_file):
    """从导出文件里解析 (user, token)。文件格式: https://<user>:<token>@github.com"""
    raw = open(cred_file, encoding="utf-8").read().strip()
    m = re.match(r"https://([^:]+):([^@]+)@", raw)
    if not m:
        raise RuntimeError("凭据格式无法解析")
    return m.group(1), m.group(2)


# --------------------------------------------------------------------------- #
# GitHub API
# --------------------------------------------------------------------------- #
def _api(method, path, token, payload=None, timeout=45):
    import json
    import urllib.error
    import urllib.request
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        API_BASE + path, data=data, method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "workbuddy-ssh-fallback-push",
        })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8")
            return r.status, (json.loads(body) if body.strip() else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def add_deploy_key(token, slug, pubkey, title):
    code, body = _api("POST", "/repos/%s/keys" % slug, token,
                      {"title": title, "key": pubkey, "read_only": False})
    if code != 201 or not isinstance(body, dict):
        raise RuntimeError("注册部署密钥失败 HTTP %s: %s" % (code, str(body)[:200]))
    return body["id"]


def delete_deploy_key(token, slug, key_id):
    code, body = _api("DELETE", "/repos/%s/keys/%s" % (slug, key_id), token)
    # 204 = 删除成功；404 = 已不存在（同样安全）
    return code in (204, 404), code


def remote_head(token, slug):
    code, body = _api("GET", "/repos/%s/commits/main" % slug, token)
    if code == 200 and isinstance(body, dict):
        return body.get("sha")
    return None


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def _git(args, timeout=60, env=None):
    e = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    if env:
        e.update(env)
    return subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True,
                          env=e, timeout=timeout)


def _ssh_env(key_path, known_hosts):
    cmd = ('ssh -i "%s" -o IdentitiesOnly=yes -o StrictHostKeyChecking=no '
           '-o UserKnownHostsFile="%s" -o BatchMode=yes -o ConnectTimeout=25 -p %d'
           % (key_path, known_hosts, SSH_PORT))
    return dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_SSH_COMMAND=cmd)


def ssh_fallback_push(branch="main", force=False, quiet=False):
    """返回提示字符串；不适用（github.com 通）时返回 None。绝不抛异常。"""
    out = (lambda m: None) if quiet else _log

    if os.name != "nt":
        return None
    if not force and tcp_open("github.com", 443, timeout=6):
        out("[..] github.com:443 可达，SSH 兜底不适用")
        return None
    if not tcp_open(SSH_HOST, SSH_PORT, timeout=10):
        return "[FAIL] ssh.github.com:443 也不可达，兜底通道不可用（本地提交已保留）"

    slug = repo_slug()
    if not slug:
        return "[FAIL] 无法解析 origin 仓库地址"

    out("[..] github.com 不通、ssh.github.com:443 可用 → 走临时部署密钥兜底")

    keydir = tempfile.mkdtemp(prefix="wbssh_")   # 纯 ASCII 路径
    cred_file = None
    key_id = None
    try:
        key_path = os.path.join(keydir, "id_ed25519")
        known_hosts = os.path.join(keydir, "known_hosts")
        kg = subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-C",
                             "temp-deploy-%d@workbuddy" % int(time.time()), "-f", key_path],
                            capture_output=True, text=True, timeout=60)
        if kg.returncode != 0 or not os.path.exists(key_path):
            return "[FAIL] 生成临时密钥失败: %s" % (kg.stderr or "")[:150]
        pubkey = open(key_path + ".pub", encoding="utf-8").read().strip()

        cred_file = export_cred_file()
        user, token = read_token(cred_file)
        out("[..] 已取到凭据（user=%s）" % user)

        key_id = add_deploy_key(token, slug, pubkey, "temp-deploy-%d-workbuddy" % int(time.time()))
        out("[..] 临时部署密钥已注册 id=%s（用完立即撤销）" % key_id)

        # SSH 认证自检，早失败早退出（避免无谓的 push 尝试）
        chk = subprocess.run(
            ["ssh", "-i", key_path, "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=no",
             "-o", "UserKnownHostsFile=" + known_hosts, "-o", "BatchMode=yes",
             "-o", "ConnectTimeout=25", "-p", str(SSH_PORT), "-T", "git@" + SSH_HOST],
            capture_output=True, text=True, timeout=90)
        if "successfully authenticated" not in (chk.stdout + chk.stderr):
            return "[FAIL] SSH 认证未通过: %s" % (chk.stdout + chk.stderr).strip()[:160]

        url = "ssh://git@%s:%d/%s.git" % (SSH_HOST, SSH_PORT, slug)
        r = _git(["push", url, "%s:%s" % (branch, branch)], timeout=600,
                 env=_ssh_env(key_path, known_hosts))
        tail = (r.stdout or r.stderr or "").strip().splitlines()
        tail = tail[-1] if tail else ""
        if r.returncode != 0:
            return "[FAIL] SSH 兜底推送失败: " + re.sub(r":[^:@\s]*@", ":***@", tail)[:200]

        head = _git(["rev-parse", "--short", "HEAD"]).stdout.strip()
        rsha = remote_head(token, slug)
        ok = bool(rsha) and rsha.startswith(head)
        return ("[OK] 已推送 GitHub Pages（SSH 兜底通道）远端=%s%s"
                % (rsha[:7] if rsha else "?", "" if ok else " ⚠ 与本地 HEAD 不一致，请核对"))
    except Exception as e:  # noqa: BLE001 兜底通道绝不能把主流程带崩
        return "[FAIL] SSH 兜底通道异常: %s: %s" % (type(e).__name__, e)
    finally:
        # 铁律：无论成败都要撤销密钥、删私钥与凭据文件
        try:
            if key_id is not None and cred_file:
                _, token = read_token(cred_file)
                done, code = delete_deploy_key(token, slug, key_id)
                _log("[OK] 临时部署密钥已撤销 id=%s (HTTP %s)" % (key_id, code) if done
                     else "[WARN] 撤销临时部署密钥失败 id=%s HTTP %s，请手动检查仓库 Deploy keys" % (key_id, code))
        except Exception as e:  # noqa: BLE001
            _log("[WARN] 撤销临时部署密钥异常: %s，请手动检查仓库 Deploy keys" % e)
        shutil.rmtree(keydir, ignore_errors=True)
        if cred_file:
            try:
                os.remove(cred_file)
            except OSError:
                pass


def selftest():
    """自检：不推送，只验证「取凭据 → 注册密钥 → SSH 认证 → 撤销」全链路。"""
    slug = repo_slug()
    _log("仓库        : %s" % slug)
    _log("api.github.com   : %s" % ("通" if tcp_open("api.github.com", 443) else "不通"))
    _log("github.com:443   : %s" % ("通" if tcp_open("github.com", 443, 6) else "不通"))
    _log("ssh.github.com:443: %s" % ("通" if tcp_open(SSH_HOST, SSH_PORT) else "不通"))
    keydir = tempfile.mkdtemp(prefix="wbssh_")
    cred_file = key_id = None
    try:
        key_path = os.path.join(keydir, "id_ed25519")
        known_hosts = os.path.join(keydir, "known_hosts")
        subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-f", key_path],
                       capture_output=True, text=True, timeout=60, check=True)
        cred_file = export_cred_file()
        user, token = read_token(cred_file)
        _log("凭据        : 已导出 (user=%s)" % user)
        key_id = add_deploy_key(token, slug, open(key_path + ".pub", encoding="utf-8").read().strip(),
                                "selftest-%d-workbuddy" % int(time.time()))
        _log("部署密钥    : 已注册 id=%s" % key_id)
        chk = subprocess.run(
            ["ssh", "-i", key_path, "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=no",
             "-o", "UserKnownHostsFile=" + known_hosts, "-o", "BatchMode=yes", "-p", str(SSH_PORT),
             "-T", "git@" + SSH_HOST], capture_output=True, text=True, timeout=90)
        auth_out = chk.stdout + chk.stderr
        msg = [l for l in auth_out.strip().splitlines() if "authenticated" in l or "denied" in l.lower()]
        _log("SSH 认证    : %s" % (msg[-1] if msg else (auth_out.strip().splitlines() or ["(无输出)"])[-1]))
        ls = _git(["ls-remote", url_of(slug)], timeout=180, env=_ssh_env(key_path, known_hosts))
        _log("ls-remote   : %s" % ("成功" if ls.returncode == 0 else "失败 " + (ls.stderr or "")[:120]))
        return 0 if (ls.returncode == 0 and "successfully authenticated" in auth_out) else 1
    finally:
        try:
            if key_id is not None and cred_file:
                _, token = read_token(cred_file)
                done, code = delete_deploy_key(token, slug, key_id)
                _log("撤销密钥    : %s (HTTP %s)" % ("成功" if done else "失败", code))
        except Exception as e:  # noqa: BLE001
            _log("撤销密钥    : 异常 %s" % e)
        shutil.rmtree(keydir, ignore_errors=True)
        if cred_file:
            try:
                os.remove(cred_file)
            except OSError:
                pass


def url_of(slug):
    return "ssh://git@%s:%d/%s.git" % (SSH_HOST, SSH_PORT, slug)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="只验证全链路，不推送")
    ap.add_argument("--check", action="store_true", help="只探测通道连通性")
    ap.add_argument("--force", action="store_true", help="跳过 github.com 探测，强制走兜底")
    ap.add_argument("--branch", default="main")
    args = ap.parse_args()

    if args.check:
        _log("api.github.com    : %s" % ("通" if tcp_open("api.github.com", 443) else "不通"))
        _log("github.com:443    : %s" % ("通" if tcp_open("github.com", 443, 6) else "不通"))
        _log("ssh.github.com:443: %s" % ("通" if tcp_open(SSH_HOST, SSH_PORT) else "不通"))
        return 0
    if args.selftest:
        return selftest()

    res = ssh_fallback_push(branch=args.branch, force=args.force)
    if res is None:
        _log("[SKIP] 兜底通道不适用")
        return 0
    _log(res)
    return 0 if res.startswith("[OK]") else 1


if __name__ == "__main__":
    sys.exit(main())
