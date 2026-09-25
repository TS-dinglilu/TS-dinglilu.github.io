# -*- coding: utf-8 -*-
"""手动凭据导出 + 推送（publish_all.push_via_exported_cred 的独立版，带显式输出）。"""
import os
import re
import shutil
import subprocess
import tempfile

HERE = r"D:\研二\github.auto\repo\scripts"
ROOT = r"D:\研二\github.auto\repo"
ps1 = os.path.join(HERE, "export_git_cred.ps1")

tmpdir = tempfile.mkdtemp(prefix="wbcred_")
ps_tmp = os.path.join(tmpdir, "export_git_cred.ps1")
with open(ps1, encoding="utf-8") as f:
    content = f.read()
with open(ps_tmp, "w", encoding="utf-8-sig") as f:
    f.write(content)
try:
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", ps_tmp], capture_output=True, timeout=120)
finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

raw = (r.stdout or b"") + b"\n" + (r.stderr or b"")
text = ""
for enc in ("utf-8", "gbk", "mbcs", "latin-1"):
    try:
        text = raw.decode(enc)
        break
    except Exception:
        continue
lines = [l.strip() for l in text.splitlines() if l.strip()]
if not lines or not os.path.exists(lines[-1]):
    print("CRED FAIL:", " | ".join(lines[-3:])[:300])
    raise SystemExit(1)

cred_file = lines[-1]
print("CRED OK")
p = subprocess.run(["git", "-c", "credential.helper=",
                    "-c", "credential.helper=store --file=%s" % cred_file.replace("\\", "/"),
                    "push", "origin", "main"],
                   cwd=ROOT, capture_output=True, text=True, timeout=240,
                   env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
out = re.sub(r":[^:@\s]*@", ":***@", (p.stdout or "") + (p.stderr or ""))
print("RC:", p.returncode)
print(out.strip()[-400:])
try:
    os.remove(cred_file)
except OSError:
    pass
