# 每日日报自动更新工作流

> 本文档是每日自动化任务的执行手册。站点：https://ts-dinglilu.github.io/
> 仓库：`D:\研二\github.auto\repo`（main 分支直推）｜正文草稿：`D:\研二\github.auto\content\`

## 13 个日报分类

| 分类目录 | 日报名称 |
|---|---|
| car-recruit | 车企招聘日报 |
| mechanical-recruit | 机械招聘日报（江浙沪） |
| school-news | 校园新闻日报（安工大/长工程/徐州三中/大庙中学） |
| drone-research | 无人机科研日报（arXiv/IEEE/自动驾驶） |
| ahut-campus | 安工大校园日报 |
| byd-recruit | 比亚迪招聘日报 |
| chery-recruit | 奇瑞招聘日报 |
| geely-recruit | 吉利招聘日报 |
| xiaomi-recruit | 小米汽车招聘日报 |
| weixiaoli-recruit | 蔚小理招聘日报 |
| traditional-auto | 传统车企招聘日报 |
| research-institute | 科研院所招聘日报 |
| future-planning | 未来规划日报 |

## 每日执行步骤

### 1. 准备与漏跑自查
```bash
cd D:\研二\github.auto\repo
git pull origin main                        # 同步远端（网络不通可跳过，不影响本地生成）
python scripts/publish_all.py --no-build    # 快速自查：提示最近 3 天是否有缺失日期
```
若提示有缺失日期（例如昨天没跑），**先补做缺失日期**：为缺失日期单独生成正文并构建
`python scripts/build_report.py --category <分类> --date <缺失日期> --content ../content/<分类>.html`，
再继续今天的流程。

### 2. 搜集素材 + 写正文
- **写作规范必读**：`D:\研二\github.auto\content\STYLE_GUIDE.md`
- 对每个分类：先看上一份报告的板块结构（`<分类>/report_最新.html`），再用 WebSearch 搜集
  **当天及近日**真实资讯（重点 24–48 小时内），按同样板块结构写正文，
  覆盖保存到 `D:\研二\github.auto\content\<分类>.html`
- 每个分类至少搜 5–8 次，覆盖不同角度；每份 8000–20000 字符
- 避免与上一期内容重复，聚焦最新进展
- **可用多个并行子代理分工加速**（例如 5 个代理各负责 2–3 个分类）

### 3. 一键发布
```bash
cd D:\研二\github.auto\repo
python scripts/publish_all.py --push
```
该脚本会自动完成：内容校验（禁 Markdown 链接/必需板块/文档标签/长度）→ 批量构建 13 分类报告
→ 重建各分类归档索引 → 更新主页卡片（最新日期+累计期数）与总数统计 → git 提交推送。

推送逻辑（针对本机环境定制）：**优先走"凭据直连通道"**（`scripts/export_git_cred.ps1`
从 Windows 凭据管理器导出凭据 → 用 git store 助手推送，约 15 秒完成）；失败才退回常规
`git push` 重试 3 次。原因是本机的 git 凭据助手（helper-selector → GCM）在非交互场景会挂起，
常规 `git push` 可能几分钟无响应。

只想构建不推送：去掉 `--push`。只更新主页：加 `--no-build`。

### 4. 验证
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://ts-dinglilu.github.io/car-recruit/report_<日期>.html
```
GitHub Pages 推送后 1–2 分钟生效，返回 200 即成功。

## 质量红线
- 所有链接必须真实可点击（来自搜索结果），严禁编造 URL 和精确假数据
- 历史报告只增不删
- 若某分类当天确实无素材，写近期梳理并在正文标注"今日动态较少，以下为近期梳理"
- 网络问题导致 push 失败时，本地提交会保留；网络恢复后 `git push origin main` 即可，不要重新生成

## 常见问题
| 现象 | 处理 |
|---|---|
| `git push` 报 `Failed to connect to github.com:443` | 国内网络问题。等几分钟重试；本地提交不会丢 |
| `git push` 长时间无响应（不报错也不返回） | 凭据助手挂起。直接跑 `python scripts/publish_all.py --push`，会自动走凭据直连通道；或手动 `powershell -File scripts\export_git_cred.ps1` 拿到凭据文件后按脚本注释里的命令推送 |
| 子代理报 429 频率限制 | 等额度重置，或改用 `model: lite` 的代理执行（实测 `lite` 可立即绕过） |
| Bash/Terminal 全线报 `command not found`（`dirname`/`ls`/`git` 都不识别） | 本机偶发 PATH 损坏。命令前先 `export PATH="/c/Users/dingliu/.workbuddy/binaries/PortableGit/versions/1.2.0/usr/bin:/c/Users/dingliu/.workbuddy/binaries/PortableGit/versions/1.2.0/mingw64/bin:/c/Windows/System32:/c/Windows:$PATH"`，Python 用绝对路径 `C:/Users/dingliu/.workbuddy/binaries/python/versions/3.13.12/python.exe` |
| 某分类构建报"找不到 `<main>` 区块" | 属正常（该分类用通用骨架），构建器会自动走通用路径 |
| 主页卡片「最新日期/累计期数」与「已生成日报」总数不更新 | 主页 index.html 若被设计编辑器改写，元素会带 `data-page-node-id` 等自定义属性，老版 `update_homepage.py` 的精确字符串匹配（`<div class="stat-num">` 等）会失效。2026-09-14 已改为「前缀 + 任意属性」正则，重跑 `python scripts/update_homepage.py` 即恢复。若仍不更新，先确认 `class="stat-num"` / `class="auto-meta"` / `class="auto-updated"` 的 class 名是否被改掉 |
| 提示"最近 3 天缺失报告" | 说明有漏跑。为缺失日期补生成正文后，用 `build_report.py --date <缺失日期>` 单独构建，再统一推送 |
