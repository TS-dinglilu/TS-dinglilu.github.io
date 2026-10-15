#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assets/report.css 的现代化升级（幂等）。

三件事：
 1. **字体栈本地化** —— CSS 原本依赖 'Noto Sans SC' / 'JetBrains Mono'，
    这两个字体来自被移除的 Google Fonts 外链。此处改为按「系统原生中文字体优先、
    Noto Sans SC 作为本地后备」的顺序，观感基本无差别，但不再需要跨境请求。
 2. **prefers-reduced-motion** —— 站点用了大量「Q弹」动画（12 处 animation +
    27 处 transition + smooth 滚动）。对前庭功能敏感的用户这会造成眩晕/恶心。
    系统开启「减弱动效」时应全部关闭，这是 WCAG 2.1 的要求项。
 3. **键盘焦点可见** —— CSS 里原本一处 :focus 都没有，键盘用户按 Tab 时
    完全不知道焦点落在哪。这里补 :focus-visible 焦点环。

用法: python scripts/upgrade_css.py [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS_PATH = os.path.join(ROOT, "assets", "report.css")

MARKER = "/* === a11y-font-enhance:v1 (由 scripts/upgrade_css.py 注入，勿手工编辑) === */"

LOCAL_SANS = ("-apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang SC\", "
              "\"Hiragino Sans GB\", \"Microsoft YaHei\", \"Noto Sans SC\", sans-serif")
LOCAL_MONO = ("ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, "
              "\"Liberation Mono\", \"Courier New\", monospace")

A11Y_BLOCK = MARKER + """
/* ---- 1. 尊重「减弱动效」系统偏好 (WCAG 2.3.3) ----
   站点视觉风格偏活泼，但动画必须可被用户关掉。 */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}

/* ---- 2. 键盘焦点必须看得见 (WCAG 2.4.7) ----
   用 :focus-visible 而非 :focus：鼠标点击时不出现焦点环，键盘 Tab 时才出现。 */
:focus-visible {
  outline: 2px solid var(--accent, #00d4ff);
  outline-offset: 2px;
  border-radius: 4px;
}
a:focus-visible, button:focus-visible, [tabindex]:focus-visible {
  outline: 2px solid var(--accent, #00d4ff);
  outline-offset: 3px;
}

/* ---- 3. 跳转到正文：让键盘/读屏用户一键跳过导航 ---- */
.skip-link {
  position: absolute;
  left: -9999px;
  top: 0;
  z-index: 2147483646;
  padding: 12px 20px;
  background: var(--accent, #00d4ff);
  color: #0a0e1a;
  font-weight: 700;
  border-radius: 0 0 8px 0;
  text-decoration: none;
}
.skip-link:focus {
  left: 0;
}

/* ---- 4. 防止宽表格/长链接在窄屏把整页撑出横向滚动条 ----
   table 改 display:block 会改变列宽行为，故只在窄屏启用，桌面视觉完全不变。 */
table { max-width: 100%; }
a { overflow-wrap: anywhere; }
@media (max-width: 768px) {
  .section table { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }
}
"""


def upgrade(css: str) -> tuple[str, list]:
    changes = []
    n = css.count("'JetBrains Mono'") + css.count('"JetBrains Mono"')
    if n:
        css = css.replace("'JetBrains Mono'", LOCAL_MONO).replace('"JetBrains Mono"', LOCAL_MONO)
        changes.append("等宽字体栈 x%d" % n)

    # 整值替换，避免逐段拼接出现重复字体名
    old_sans = "'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    if old_sans in css:
        css = css.replace(old_sans, LOCAL_SANS)
        changes.append("正文字体栈（Noto Sans SC 降级为本地后备）")

    if MARKER not in css:
        css = css.rstrip() + "\n\n" + A11Y_BLOCK
        changes.append("注入可访问性增强块（减弱动效/焦点环/skip-link/溢出保护）")
    return css, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    css = open(CSS_PATH, encoding="utf-8").read()
    new, changes = upgrade(css)
    if not changes:
        print("report.css 已是最新，无需改动。")
        return 0
    print("将做以下改动：")
    for c in changes:
        print("  - " + c)
    if a.dry_run:
        print("\n[dry-run] 未写盘。")
        return 0
    open(CSS_PATH, "w", encoding="utf-8", newline="").write(new)
    print("\n[OK] 已更新 %s (%d -> %d 字节)" % (CSS_PATH, len(css), len(new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
