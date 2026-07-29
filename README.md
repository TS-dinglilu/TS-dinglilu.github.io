# TRAE 自动化日报系统

基于 GitHub Pages 的自动化日报系统，为安徽工业大学机械工程硕士研究生提供个性化招聘信息和行业资讯推荐。

## 系统架构

- **主仓库**: [TS-dinglilu/TS-dinglilu.github.io](https://github.com/TS-dinglilu/TS-dinglilu.github.io)
- **在线访问**: [https://ts-dinglilu.github.io/](https://ts-dinglilu.github.io/)
- **自动化时间**: 每天早上5点（北京时间）自动执行
- **部署方式**: 统一部署到主仓库子目录，通过 `deploy_github_pages.ps1` 脚本管理

## 页面层级

| 层级 | URL格式 | 说明 |
|------|---------|------|
| 主页 | `https://ts-dinglilu.github.io/` | 13个日报系统入口 |
| 报告汇总 | `https://ts-dinglilu.github.io/car-recruit/` | 某个日报的归档列表 |
| 报告 | `https://ts-dinglilu.github.io/car-recruit/report_20260728.html` | 具体某天的日报 |

## 13个日报系统

| 序号 | 子目录 | 日报名称 | 在线地址 |
|------|--------|----------|----------|
| 1 | car-recruit | 车企招聘日报 | https://ts-dinglilu.github.io/car-recruit/ |
| 2 | mechanical-recruit | 机械招聘日报 | https://ts-dinglilu.github.io/mechanical-recruit/ |
| 3 | school-news | 校园新闻日报 | https://ts-dinglilu.github.io/school-news/ |
| 4 | drone-research | 无人机科研日报 | https://ts-dinglilu.github.io/drone-research/ |
| 5 | ahut-campus | 安工大校园日报 | https://ts-dinglilu.github.io/ahut-campus/ |
| 6 | byd-recruit | 比亚迪招聘日报 | https://ts-dinglilu.github.io/byd-recruit/ |
| 7 | chery-recruit | 奇瑞招聘日报 | https://ts-dinglilu.github.io/chery-recruit/ |
| 8 | geely-recruit | 吉利招聘日报 | https://ts-dinglilu.github.io/geely-recruit/ |
| 9 | xiaomi-recruit | 小米汽车招聘日报 | https://ts-dinglilu.github.io/xiaomi-recruit/ |
| 10 | weixiaoli-recruit | 蔚小理招聘日报 | https://ts-dinglilu.github.io/weixiaoli-recruit/ |
| 11 | traditional-auto | 传统车企招聘日报 | https://ts-dinglilu.github.io/traditional-auto/ |
| 12 | research-institute | 科研院所招聘日报 | https://ts-dinglilu.github.io/research-institute/ |
| 13 | future-planning | 未来规划日报 | https://ts-dinglilu.github.io/future-planning/ |

## 部署脚本使用

```powershell
.\deploy_github_pages.ps1 -SubDir "car-recruit" -ReportFile "report_20260728.html" -ReportDate "2026-07-28" -SiteTitle "车企招聘日报" -SiteDesc "比亚迪/奇瑞/吉利等车企招聘信息与岗位分析"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-SubDir` | 子目录名（如 car-recruit） |
| `-ReportFile` | 本地报告HTML文件路径 |
| `-ReportDate` | 报告日期 YYYY-MM-DD |
| `-SiteTitle` | 站点标题（XX日报格式） |
| `-SiteDesc` | 站点描述 |

## 统一工作流

1. 信息收集（WebSearch + WebFetch）
2. 生成自包含HTML报告（使用统一CSS模板）
3. 保存到本地 `d:\BaiduNetdiskDownload\trae自动化\<子目录>\report_YYYYMMDD.html`
4. 使用 `deploy_github_pages.ps1` 部署到GitHub子目录
5. 推送飞书摘要

## 配色方案

- 背景: `#0a0e1a`（深空蓝）
- 强调色: `#00d4ff`（青色）
- 主文字: `#f0f4f8`（最亮 - 标题、重要内容）
- 次要文字: `#c8d4e8`（中等 - 正文、段落）
- 辅助文字: `#90a0c0`（较暗 - 元数据、时间戳）
- 字体: JetBrains Mono + Noto Sans SC

> 三种页面类型（主页/报告汇总/报告页）使用统一的CSS变量，确保视觉一致性。

## 评论系统

使用 Giscus 评论系统，配置如下：
- 仓库: `TS-dinglilu/TS-dinglilu.github.io`
- 仓库ID: `R_kgDOTjqaJQ`
- 分类: Announcements
- 分类ID: `DIC_kwDOTjqaJc4DCIL1`
- 映射方式: pathname
- 主题: dark_dimmed

## 设计规范

报告CSS使用统一模板（`report_css_template.css`），部署脚本自动应用。

- 配色方案：深空蓝(#0a0e1a)背景 + 青色(#00d4ff)强调色
- 不同板块间使用渐变分割线清晰分隔，确保相邻板块一目了然
- 所有文字颜色需高对比度，确保在暗色背景上清晰可读
- 报告标题统一使用"XX日报"格式
- 报告汇总页面的"点击查看"链接位于卡片右侧

## 重要约定

- HTML报告中所有链接必须使用HTML `<a>`标签格式，严禁使用Markdown链接格式
- 报告文件命名：`report_YYYYMMDD.html`
- 部署脚本内置重试机制，自动验证上传成功
- 部署脚本使用动态临时目录，执行完毕自动清理
- 所有历史报告归档保留（不删除）
- 自动化任务运行时间：每天早上5点（北京时间）
- 所有页面包含 `<link rel="preconnect">` 优化字体加载
- 所有页面包含 `<meta name="description">` SEO描述

## 项目文件说明

| 文件 | 说明 |
|------|------|
| `deploy_github_pages.ps1` | 统一部署脚本v3.0（上传报告+生成索引+配置评论区+动态临时目录） |
| `report_css_template.css` | 报告页统一CSS模板 v8.0 |
| `replace_css.py` | CSS模板替换工具（部署脚本调用） |
| `homepage_index.html` | 主页源文件 |
| `export_trae_memory.ps1` | TRAE记忆导出脚本 |
| `export_trae_tasks.ps1` | TRAE任务导出脚本 |
| `export_trae_tasks.py` | TRAE任务导出Python后端 |
| `future-planning/future_planning_config.txt` | 未来规划任务配置文件 |
