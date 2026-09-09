# 每日日报自动更新工作流

> 本文档是每日自动化任务的执行手册。站点：https://ts-dinglilu.github.io/
> 仓库本地路径：`D:\研二\github.auto\repo`（main 分支，直接 push）

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

### 1. 准备
```bash
cd D:\研二\github.auto\repo
git pull origin main        # 同步远端（若有云端改动）
```
日期 = 今天（YYYY-MM-DD）。

### 2. 搜集素材 + 写正文
- **写作规范必读**：`D:\研二\github.auto\content\STYLE_GUIDE.md`
  （只输出 `<main>` 内部内容；链接一律 `<a class="source-link" href="..." target="_blank">📎 查看原文</a>`；
  结尾必须有「信息来源汇总」表格 + `<div class="giscus"></div>`）
- 对每个分类：先看上一份报告的板块结构（`<分类>/report_最新.html`），再用 WebSearch 搜集**当天/近期**真实资讯，
  按同样板块结构写正文，保存到 `D:\研二\github.auto\content\<分类>.html`
- 每份 8000–20000 字符；关键数据加粗；禁止 Markdown 链接；不得编造精确数字和假链接
- 可用多个并行子代理分工（例如 4-5 个代理各负责 3-4 个分类），加快速度

### 3. 构建报告 + 更新索引
```bash
cd D:\研二\github.auto\repo
python scripts/build_report.py --category <分类> --date <YYYY-MM-DD> --content ../content/<分类>.html
```
对 13 个分类逐一执行。脚本会自动：以最新历史报告为模板 → 替换正文和日期 → 写 `report_YYYYMMDD.html` →
重建该分类 `index.html` 归档列表/统计/最后更新时间 → 自动修复未闭合 div 和重复 body 标签。

### 4. 更新主页统计（可选）
`index.html` 中 `stat-num">NNN+` 为报告总数，可按实际总数更新。

### 5. 提交推送
```bash
git add -A
git commit -m "每日日报自动更新 <YYYY-MM-DD>"
git push origin main
```
push 失败时重试 3 次；仍失败则保留本地提交，报告给用户。

## 质量红线
- 所有链接必须真实可点击（来自搜索结果），严禁编造 URL
- 网站部署在 GitHub Pages，push 后 1-2 分钟自动生效
- 历史报告只增不删
- 若某个分类当天实在搜不到素材，可以写行业分析向内容，但必须在正文标注"今日动态较少，以下为近期梳理"
