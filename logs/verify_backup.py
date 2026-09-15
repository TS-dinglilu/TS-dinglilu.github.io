#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验备份完整性：逐文件比对 sha256 与文件数。"""
import hashlib
import os
import sys

SRC = r"D:\研二\github.auto"
BK = r"D:\研二\github.auto\backups\20260914_2052_pre-visual-unify"
PARTS = ["content", "logs", "repo", ".workbuddy"]
# 备份之后才创建的临时脚本，不应计入差异
SKIP = {"logs/verify_backup.py"}


def walk(base):
    out = {}
    for root, dirs, files in os.walk(base):
        for f in files:
            p = os.path.join(root, f)
            rel = os.path.relpath(p, base).replace("\\", "/")
            out[rel] = p
    return out


def sha(p, chunk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


total = 0
mismatch = []
missing = []
extra = []

for part in PARTS:
    s_base = os.path.join(SRC, part)
    b_base = os.path.join(BK, part)
    if not os.path.isdir(s_base):
        print("跳过（源不存在）: %s" % part)
        continue
    sf = walk(s_base)
    bf = walk(b_base)
    total += len(sf)
    for rel, sp in sf.items():
        if ("%s/%s" % (part, rel)) in SKIP:
            continue
        if rel not in bf:
            missing.append("%s/%s" % (part, rel))
            continue
        if sha(sp) != sha(bf[rel]):
            mismatch.append("%s/%s" % (part, rel))
    for rel in bf:
        if rel not in sf:
            extra.append("%s/%s" % (part, rel))
    print("%-12s 源 %5d 文件 / 备份 %5d 文件  %s"
          % (part, len(sf), len(bf), "一致 ✓" if len(sf) == len(bf) else "数量不符 ✗"))

print("\n" + "=" * 58)
print("源文件总数: %d" % total)
print("内容不一致: %d" % len(mismatch))
print("备份中缺失: %d" % len(missing))
print("备份多出的: %d" % len(extra))
for x in (missing + mismatch + extra)[:20]:
    print("   ! " + x)
print("=" * 58)
if not (mismatch or missing):
    print("备份完整性校验通过 ✓")
    sys.exit(0)
print("备份存在问题，请勿继续！")
sys.exit(1)
