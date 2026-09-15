# 自动化执行记录 — 每日自动化新闻推送（13 分类日报）

> 站点：https://ts-dinglilu.github.io/ ｜ 仓库：`D:\研二\github.auto\repo`（main 直推）
> 仅记录高层结果，正文内容不入档。

## 2026-09-14（周一）
- **实际执行日 09-14**：本会话在 09-13 启动、跨天到 09-14 被恢复执行。
- **核实历史**：09-12、09-13 已由中断前的会话完成并推送（commit `695a0c0` / `0697ac7`），本轮仅核实，未重做。
- **本轮产出**：13 分类 09-14 正文（content/<分类>.html，逐条真实链接），构建 `report_20260914.html` ×13 + 13 个归档索引 + 主页统计。
- **推送结果**：09-14 报告（`1fb5aab`）与主页修复（`15f50f2`）**已上线并验证**（各分类 09-14 页面 HTTP 200，主页显示 13 张卡片「最新 09-14」、总数 180+）。
  文档提交 `9a35044` 一度因 `github.com:443` 中断暂留本地；**当晚重试凭据直连通道第 3 次成功，`9a35044` 已推送**，
  远端 main = `9a35044`，13 个 09-14 页面 curl 全 200（无需再带出）。
- **关键修复（重要）**：主页 index.html 被设计编辑器改写，元素被批量加上 `data-page-node-id` 属性，
  导致 `update_homepage.py` 三处精确字符串匹配失效（`<div class="stat-num">` / `auto-meta` / `auto-updated`），
  于是 **09-12、09-13、09-14 连续三次运行主页其实都没真正更新**（卡片停在 09-11、总数停在 141+）。
  已改为「前缀 + 任意属性」正则并保留元素原有属性，重跑后恢复（13 张卡片刷新、总数 180+）。
- **环境坑**：① Bash PATH 偶发损坏（`dirname`/`ls`/`git` 全不识别）→ 命令前 `export PATH` 指向 PortableGit 的 `usr/bin` 与 `mingw64/bin`；② 子代理 429 限流 → 换 `model: "lite"` 立即绕过。
- **仍缺日期**：09-10（`content/backfill0910/` 草稿仅 11/13，缺 byd-recruit、traditional-auto），距今 4 天，本轮未补。

### 同日续跑补充（第二轮，09-14 下午）
- **核实结果**：09-12 / 09-13 / 09-14 三天各 13/13 报告齐备，远端 main = `9a35044`，本轮无漏跑告警。
- **正文产出核对**：本轮另派 5 个并行子代理写 13 分类正文（3+2+3+3+2 分工）。
  **其中研究「research-institute + future-planning」的代理零产出**，已重派；
  `future-planning` 重派时撞 429，换 `model: "lite"` 成功。
  ⚠️ **教训：每轮写完必须逐个核对文件 mtime/大小，不能只信代理的回报文字。**
- **本轮新增踩坑**：
  1. **`git status` 显示 "ahead 15 commits"、`git rev-parse origin/main` 停在很旧的 `cdb3b4c`，但远端其实已收到推送**
     —— 本地 `origin/main` 跟踪引用陈旧，**不能据此判断推送失败**。
     查真实远端用 `curl -s https://api.github.com/repos/TS-dinglilu/TS-dinglilu.github.io/commits/main`（api 域通常可达）。
  2. **Bash PATH 修复要连带 PortableGit 的 `cmd` 目录**：只 `export PATH="/usr/bin:/bin:$PATH"` 会让
     `publish_all.py` 里的 `subprocess.run(["git", ...])` 抛 `WinError 2`（构建全成功、提交推送直接崩）。
     完整前缀：`/usr/bin:/bin:/c/Users/dingliu/.workbuddy/binaries/PortableGit/versions/1.2.0/cmd`。
  3. **凭据直连通道要重试足 3–4 轮、间隔 ≥25 秒**：本轮第 1、2 次 "Connection was reset"，第 3 次成功；
     常规 `git push` 三次全败（github.com:443 不可达）。
  4. 校验可加一道**更严的自查**（正则扫 doc 标签 / Markdown 链接 / giscus / 信息来源 / inline style / 8000 字符下限），
     比 `publish_all.py` 自带的 3000 字符下限严格。

## 2026-09-15（周二）
- **执行日 09-15**：前置体检通过（13 分类 / 193 报告 / 无漏期），`git pull` 已最新（`7b321f4`）。
- **正文**：5 个并行子代理分工（2+3+2+3+3）写 13 分类，**13/13 一次成功**，无需重派、无 429。
- **新增「外链真实性核验」环节**：206 条唯一外链全量 curl，204 条 200/302；
  2 条修正为 `http://`（`m.yingjiesheng.com` 搜索页、`www.nssc.cas.cn` —— 二者 https 不可达但 http 200）；arXiv 抽验全 200。
- **构建**：`publish_all.py` 一次通过，13/13 生成、索引与主页同步，总数 193 → **206+**，站点自查通过。
- **推送**：提交 `b61b51f`，凭据直连通道**一次成功**；远端 main 已核验为 `b61b51f`，
  线上 13 个 09-15 页面 curl 全 200，主页 13 张卡片均「最新 09-15 · 累计 N 期」。
- **本轮踩坑（已写入项目 MEMORY.md）**：
  1. **Bash 调 `powershell.exe` 被安全策略直接拒绝** → 手动导凭据走不通，用 `publish_all.py --push`；
  2. **`publish_all.py --push` 输出管到 `tail` 会因 SIGTERM 丢掉全部输出** → 必须重定向到日志文件；
  3. **Windows CRLF 临时文件让 shell 循环里的 curl 全返回 `000`** → `tr -d '\r'` 后再读，
     判据是「单条 200、循环全 000 就查数据不查网络」。
