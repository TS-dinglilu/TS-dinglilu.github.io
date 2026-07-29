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
- 正文: `#f0f4f8`（明亮）
- 次要文字: `#e8eef5`（明亮）
- 辅助文字: `#e0e8f2`（明亮）
- 字体: JetBrains Mono + Noto Sans SC

## 评论系统

使用 Giscus 评论系统，配置如下：
- 仓库: `TS-dinglilu/TS-dinglilu.github.io`
- 仓库ID: `R_kgDOTjqaJQ`
- 分类: Announcements
- 分类ID: `DIC_kwDOTjqaJc4DCIL1`
- 映射方式: pathname
- 主题: dark_dimmed
