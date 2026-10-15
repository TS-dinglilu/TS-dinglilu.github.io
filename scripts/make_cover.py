#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成站点社交分享封面图 assets/cover.png（1200x630，OG 标准尺寸）。

为什么需要：所有报告页都注入了 og:image 指向这张图。没有它，分享链接到
微信/QQ/微博时只会显示一段无图的纯文字卡片，观感很差。

依赖 Pillow（仅生成时需要，站点本身是纯静态、不需要它）：
  C:/Users/dingliu/.workbuddy/binaries/python/envs/default/Scripts/python.exe scripts/make_cover.py

用法: python scripts/make_cover.py [--out assets/cover.png]
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[ERROR] 需要 Pillow。请用装有 Pillow 的解释器运行，例如：\n"
          "  C:/Users/dingliu/.workbuddy/binaries/python/envs/default/Scripts/python.exe "
          "scripts/make_cover.py")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1200, 630
BG_TOP, BG_BOTTOM = (10, 14, 26), (17, 23, 38)     # #0a0e1a → #111726
ACCENT = (0, 212, 255)                              # #00d4ff
TEXT, SUB = (240, 244, 248), (144, 160, 192)

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",   # 微软雅黑 Bold
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\Dengb.ttf",
    r"C:\Windows\Fonts\simhei.ttf",
]


def load_font(size: int):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:  # noqa: BLE001
                continue
    return ImageFont.load_default()


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def build(out_path: str) -> str:
    img = Image.new("RGB", (W, H), BG_TOP)
    d = ImageDraw.Draw(img)

    # 1) 垂直背景渐变
    for y in range(H):
        d.line([(0, y), (W, y)], fill=lerp(BG_TOP, BG_BOTTOM, y / H))

    # 2) 右上角的青色光晕（营造层次，避免整块死板）
    g = Image.new("L", (256, 256), 0)
    gd = ImageDraw.Draw(g)
    gd.ellipse([0, 0, 255, 255], fill=255)
    g = g.resize((900, 900), Image.LANCZOS)
    halo = Image.new("RGB", (900, 900), ACCENT)
    halo.putalpha(g.point(lambda v: int(v * 0.28)))
    img.paste(halo, (W - 620, -260), halo)

    d = ImageDraw.Draw(img)

    # 3) 顶部渐变装饰条
    for x in range(150):
        t = x / 150
        col = lerp(ACCENT, (129, 140, 248), t)
        d.line([(90 + x, 96), (90 + x, 102)], fill=col)

    f_title = load_font(88)
    f_sub = load_font(34)
    f_small = load_font(26)

    # 4) 主标题
    d.text((90, 150), "自动化日报", font=f_title, fill=TEXT)
    tw = d.textlength("自动化日报", font=f_title)
    d.rectangle([90, 108, 90 + int(tw), 112], fill=ACCENT)

    # 5) 站点标识与副标题
    d.text((90, 272), "TS-dinglilu", font=f_sub, fill=ACCENT)
    d.text((90, 326), "车企 · 机械 · 科研 · 校园 · 地区 · 口碑", font=f_sub, fill=SUB)
    d.text((90, 380), "34 个分类，每日 05:00 自动更新，累计 800+ 期", font=f_small, fill=SUB)

    # 6) 底部装饰点阵
    dots = [(90 + i * 26, 520) for i in range(12)]
    for i, (x, y) in enumerate(dots):
        d.ellipse([x, y, x + 8, y + 8], fill=lerp(ACCENT, SUB, i / max(1, len(dots) - 1)))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, optimize=True)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "assets", "cover.png"))
    a = ap.parse_args()
    p = build(a.out)
    print("[OK] 封面已生成: %s (%d 字节)" % (p, os.path.getsize(p)))


if __name__ == "__main__":
    main()
