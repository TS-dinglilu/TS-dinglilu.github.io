# 自动化日报系统

基于 GitHub Pages 的每日自动化日报系统，为安徽工业大学机械工程硕士研究生（张恒辰）提供个性化的招聘、科研与校园资讯。

- **在线访问**：https://ts-dinglilu.github.io/
- **仓库**：TS-dinglilu/TS-dinglilu.github.io（main 分支直推，GitHub Pages 自动部署，约 1–2 分钟生效）
- **自动化时间**：每天 05:00（北京时间），由 WorkBuddy 自动化任务驱动
- **本地工作区**：`D:\研二\github.auto`（`repo/` = 本仓库克隆 = 唯一真源，`repo/content/` = 每日正文草稿）

## 页面层级

| 层级 | URL 格式 | 说明 |
|------|---------|------|
| 周记月记年记 | `https://ts-dinglilu.github.io/digest/` | 站级汇总：每周/月/年自动生成动态与数据统计报告，可按大类筛选 |
| 主页 | `https://ts-dinglilu.github.io/` | 23 个日报系统入口，卡片显示各分类最新日期与累计期数 |
| 报告汇总 | `https://ts-dinglilu.github.io/car-recruit/` | 该日报的归档列表 |
| 报告 | `https://ts-dinglilu.github.io/car-recruit/report_20260911.html` | 具体某天的日报 |

## 23 个日报系统

| 序号 | 子目录 | 日报名称 |
|------|--------|----------|
| 1 | car-recruit | 车企招聘日报 |
| 2 | mechanical-recruit | 机械招聘日报 |
| 3 | school-news | 校园新闻日报 |
| 4 | drone-research | 无人机科研日报 |
| 5 | ahut-campus | 安工大校园日报 |
| 6 | byd-recruit | 比亚迪招聘日报 |
| 7 | chery-recruit | 奇瑞招聘日报 |
| 8 | geely-recruit | 吉利招聘日报 |
| 9 | xiaomi-recruit | 小米汽车招聘日报 |
| 10 | weixiaoli-recruit | 蔚小理招聘日报 |
| 11 | traditional-auto | 传统车企招聘日报 |
| 12 | supply-chain-recruit | 车企供应链招聘日报 |
| 13 | research-institute | 科研院所招聘日报 |
| 14 | future-planning | 未来规划日报 |
| 15 | xuzhou-news | 徐州汽车机械日报 |
| 16 | nanjing-news | 南京汽车机械日报 |
| 17 | shanghai-news | 上海汽车机械日报 |
| 18 | hangzhou-news | 杭州汽车机械日报 |
| 19 | jiangzhehu-news | 江浙沪汽车机械日报 |
| 20 | hefei-news | 合肥汽车机械日报 |
| 21 | anhui-news | 安徽汽车机械日报 |
| 22 | jiangsu-news | 江苏汽车机械日报 |
| 23 | shenzhen-news | 深圳汽车机械日报 |

## 周记 / 月记 / 年记

`scripts/build_digest.py` 在每周一（周记）、每月 1 日（月记）、每年 1 月 2 日（年记）自动生成站级汇总报告到 `digest/`，聚合页带「招聘 / 校园科研 / 地区 / 规划」大类筛选标签。手动生成：

```bash
python scripts/build_digest.py --type weekly   # 月记 monthly / 年记 yearly
```

## 每日流程

完整手册见 [`scripts/DAILY_WORKFLOW.md`](scripts/DAILY_WORKFLOW.md)。核心命令：

```bash
cd D:\研二\github.auto\repo

# 0) 先同步仓库（仓库是唯一真源；网络不通可跳过，本地数据是完整的）
git pull origin main

# 1) 体检（可选但推荐）：确认没有漏跑的日期、坏链接或索引不一致
python scripts/audit_site.py

# 2) 为 23 个分类写正文（每个分类一个文件，规范见 content/STYLE_GUIDE.md）
#    输出到 content/<分类>.html（仓库内路径）

# 3) 校验 + 构建 + 更新主页 + 全站自查 + 推送，一条命令搞定
python scripts/publish_all.py --push
```

### 脚本说明

| 脚本 | 作用 |
|------|------|
| `scripts/publish_all.py` | 一键发布：内容校验 → 批量构建 14 分类 → 更新主页 → 全站自查 → 提交推送（凭据直连优先，常规 push 兜底） |
| `scripts/build_report.py` | 单分类构建：以最新历史报告为模板替换正文/日期，写出 `report_YYYYMMDD.html`，重建该分类 `index.html` |
| `scripts/build_backfill.py` | 补做漏跑日期：从指定正文目录批量构建某历史日期的报告，缺失分类会列出 |
| `scripts/audit_site.py` | 全站体检：结构完整性 / 评论区 / 死链 / 索引一致性 / 主页数字 / 漏期检测 |
| `scripts/fix_site.py` | 全站修复（幂等）：坏链接、旧品牌名、缺失评论区、重复 `<body>`、废弃页引用 |
| `scripts/update_homepage.py` | 扫描各分类期数与最新日期，写回主页卡片与统计区 |
| `scripts/tail_template.py` | 报告尾部（评论区 + 页脚 + 返回顶部 + giscus）与 14 个标准日报名的**唯一真源**，构建与统一共用 |
| `scripts/export_git_cred.ps1` | 从 Windows 凭据管理器导出 Git 凭据，供推送兜底通道使用（用完即删临时文件） |
| `scripts/set_giscus_category.py` | 全站切换 giscus 评论分类（见下方"评论系统"） |
| `scripts/report_css_v9.css` | 报告页 CSS 模板参考（实际 CSS 已内联在各页面中） |

构建器兼容两种历史骨架：`<main>` 型（car-recruit）与 hero+container 型（其余 13 个），并会自动修复未闭合 `<div>`、重复 `<body>` 等历史瑕疵。

发布后想单独体检或排障：
```bash
python scripts/audit_site.py          # 应输出「全部通过 ✓」，退出码 0
python scripts/fix_site.py --dry-run  # 出现结构/链接问题时，先看将要改什么
```

## 内容规范

- 正文只输出 `<main>` 区域内内容，分类页头由构建脚本注入
- 所有链接必须是 HTML `<a>` 标签：`<a class="source-link" href="..." target="_blank">📎 查看原文</a>`，**严禁 Markdown 链接**
- 每份报告结尾必须包含「信息来源汇总」表格 + `<div class="giscus"></div>`
- 报告命名：`report_YYYYMMDD.html`
- 内容 8000–20000 字符（用 `python scripts/strict_check.py` 自查），关键数据用 `<strong>` 高亮
- **所有链接必须真实可点击，严禁编造 URL 与精确假数据**
- 历史报告只增不删

## 配色与设计

- 背景 `#0a0e1a`（深空蓝）｜强调色 `#00d4ff`（青色）
- 主文字 `#f0f4f8`｜正文 `#c8d4e8`｜辅助 `#90a0c0`
- 字体：JetBrains Mono + Noto Sans SC
- 14 个分类页面共用统一 CSS 变量，视觉一致

## 评论系统

使用 Giscus，配置：

- 仓库 `TS-dinglilu/TS-dinglilu.github.io`（repo-id `R_kgDOTjqaJQ`）
- 分类 `General`（category-id `DIC_kwDOTjqaJc4DCIL2`）—— 访客可正常评论
- 映射方式 `pathname`，主题 `dark_dimmed`

> 2026-09-11 已从 `Announcements` 切换到 `General`：`Announcements` 分类只有维护者能发帖，
> 访客评论实际不可用。如需再次切换：
> ```bash
> python scripts/set_giscus_category.py --name General --id DIC_kwDOxxxxxxxx
> ```
> 查分类 ID 的公开接口：`curl -s "https://giscus.app/api/discussions/categories?repo=TS-dinglilu/TS-dinglilu.github.io"`

## 网络与推送注意事项

- 国内网络下 `github.com` 时常不可达（`api.github.com`、`*.github.io` 通常正常）。此时 `git push` 会失败；本地提交不会丢失，网络恢复后 `git push origin main` 即可。
- 本机 git 凭据助手（`helper-selector` → GCM）在非交互场景可能挂起，导致 `git push` 长时间无响应。
  `publish_all.py` 因此**默认优先走凭据直连通道**（`export_git_cred.ps1` 导出凭据 → git store 助手推送，约 15 秒），
  常规 `git push` 仅作兜底。手动推送遇到卡死时，可：
  ```powershell
  powershell -File scripts\export_git_cred.ps1     # 输出临时凭据文件路径
  git -c credential.helper= -c "credential.helper=store --file=<上面的路径>" push origin main
  ```
  推送完成后删除该临时文件。凭据不会写入仓库。

## 新增日报分类

新增分类需要**同时**改动 6 处（漏一处就会出现「脚本里没有这个分类」或「新分类被判天天漏期」）：

1. `scripts/tail_template.py` 的 `CATEGORY_NAMES`（标准日报名唯一真源）
2. `scripts/publish_all.py`、`update_homepage.py`、`audit_site.py`、`strict_check.py`、`fix_site.py` 的 `CATEGORIES`
3. `scripts/audit_site.py` 的 `START_DATES` 登记建号日期（避免新分类被判定为「自 20260901 起每天都缺」）
4. 新建 `<分类>/` 目录 + `content/<分类>.html`，用一次性引导脚本借壳生成首期报告
5. `index.html` 主页加卡片（`data-cat` 与筛选分组一致）与底部导航链接
6. 本文件与 `scripts/DAILY_WORKFLOW.md` 的分类数

## 目录结构

```
D:\研二\github.auto\
├─ backups\              # 历史快照，体积大，不入 git（用网盘归档）
└─ repo\                 # TS-dinglilu.github.io 的 git 克隆（本仓库 = 站点根）
   ├─ content\           # 每日正文草稿（各分类一个 .html）+ STYLE_GUIDE.md
   │  └─ backfill<MMDD>\ # 漏跑日期的补做正文（按 <分类>.html 命名，供 build_backfill.py 消费）
   ├─ logs\              # 推送日志 / 审计记录 / 归档页（archive\）+ 一次性脚本
   ├─ scripts\           # 构建、发布、体检、修复脚本 + DAILY_WORKFLOW.md
   ├─ index.html         # 站点主页（个人主页 + 14 日报入口）
   └─ <14 个分类目录>     # 每个目录含 index.html（归档）与 report_*.html（报告）
```

> 注意：站点主页只有 `repo/index.html` 一份。历史遗留的 `homepage_index.html` 已归档到
> `logs/archive/`，不要再放第二份主页，否则 `update_homepage.py` 只更新 `index.html`，两份会不一致。
