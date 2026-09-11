# 自动化日报系统

基于 GitHub Pages 的每日自动化日报系统，为安徽工业大学机械工程硕士研究生（张恒辰）提供个性化的招聘、科研与校园资讯。

- **在线访问**：https://ts-dinglilu.github.io/
- **仓库**：TS-dinglilu/TS-dinglilu.github.io（main 分支直推，GitHub Pages 自动部署，约 1–2 分钟生效）
- **自动化时间**：每天 05:00（北京时间），由 WorkBuddy 自动化任务驱动
- **本地工作区**：`D:\研二\github.auto`（`repo/` = 本仓库克隆，`content/` = 每日正文草稿）

## 页面层级

| 层级 | URL 格式 | 说明 |
|------|---------|------|
| 主页 | `https://ts-dinglilu.github.io/` | 13 个日报系统入口，卡片显示各分类最新日期与累计期数 |
| 报告汇总 | `https://ts-dinglilu.github.io/car-recruit/` | 该日报的归档列表 |
| 报告 | `https://ts-dinglilu.github.io/car-recruit/report_20260911.html` | 具体某天的日报 |

## 13 个日报系统

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
| 12 | research-institute | 科研院所招聘日报 |
| 13 | future-planning | 未来规划日报 |

## 每日流程

完整手册见 [`scripts/DAILY_WORKFLOW.md`](scripts/DAILY_WORKFLOW.md)。核心命令：

```bash
# 1) 为 13 个分类写正文（每个分类一个文件，规范见 content/STYLE_GUIDE.md）
#    输出到 D:\研二\github.auto\content\<分类>.html

# 2) 校验 + 构建 + 更新主页 + 推送，一条命令搞定
cd D:\研二\github.auto\repo
python scripts/publish_all.py --push
```

### 脚本说明

| 脚本 | 作用 |
|------|------|
| `scripts/publish_all.py` | 一键发布：内容校验 → 批量构建 13 分类 → 更新主页 → 提交推送（带退避重试） |
| `scripts/build_report.py` | 单分类构建：以最新历史报告为模板替换正文/日期，写出 `report_YYYYMMDD.html`，重建该分类 `index.html` |
| `scripts/update_homepage.py` | 扫描各分类期数与最新日期，写回主页卡片与统计区 |
| `scripts/set_giscus_category.py` | 全站切换 giscus 评论分类（见下方"评论系统"） |
| `scripts/report_css_v9.css` | 报告页 CSS 模板参考（实际 CSS 已内联在各页面中） |

构建器兼容两种历史骨架：`<main>` 型（car-recruit）与 hero+container 型（其余 12 个），并会自动修复未闭合 `<div>`、重复 `<body>` 等历史瑕疵。

## 内容规范

- 正文只输出 `<main>` 区域内内容，分类页头由构建脚本注入
- 所有链接必须是 HTML `<a>` 标签：`<a class="source-link" href="..." target="_blank">📎 查看原文</a>`，**严禁 Markdown 链接**
- 每份报告结尾必须包含「信息来源汇总」表格 + `<div class="giscus"></div>`
- 报告命名：`report_YYYYMMDD.html`
- 内容 8000–20000 字符，关键数据用 `<strong>` 高亮
- **所有链接必须真实可点击，严禁编造 URL 与精确假数据**
- 历史报告只增不删

## 配色与设计

- 背景 `#0a0e1a`（深空蓝）｜强调色 `#00d4ff`（青色）
- 主文字 `#f0f4f8`｜正文 `#c8d4e8`｜辅助 `#90a0c0`
- 字体：JetBrains Mono + Noto Sans SC
- 13 个分类页面共用统一 CSS 变量，视觉一致

## 评论系统

使用 Giscus，配置：

- 仓库 `TS-dinglilu/TS-dinglilu.github.io`（repo-id `R_kgDOTjqaJQ`）
- 映射方式 `pathname`，主题 `dark_dimmed`
- ⚠️ **待修复**：当前分类为 `Announcements`（该分类仅维护者可发帖，访客评论实际不可用）。
  需改为 `General` 或 `Q&A`。拿到新分类 ID 后执行：
  ```bash
  python scripts/set_giscus_category.py --name General --id DIC_kwDOxxxxxxxx
  ```

## 网络注意事项

国内网络下 `github.com` 时常不可达（`api.github.com`、`*.github.io` 通常正常）。此时 `git push` 会失败：

- 本地提交不会丢失，网络恢复后 `git push origin main` 即可
- `publish_all.py` 内置 6 次退避重试，能扛过短时抖动

## 目录结构

```
D:\研二\github.auto\
├─ content\          # 每日正文草稿（各分类一个 .html）+ STYLE_GUIDE.md
├─ logs\             # 历史 TRAE 运行日志（归档，无功能作用）
└─ repo\             # TS-dinglilu.github.io 的 git 克隆（本仓库）
   ├─ scripts\       # 构建与发布脚本 + DAILY_WORKFLOW.md
   ├─ index.html     # 主页
   └─ <13 个分类目录>  # 每个目录含 index.html（归档）与 report_*.html（报告）
```
