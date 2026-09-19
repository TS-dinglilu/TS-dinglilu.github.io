# 日报正文 HTML 写作规范

你写的 HTML 会被直接插入 `<main class="container"> ... </main>` 内部。
不要输出 `<!DOCTYPE>`、`<head>`、`<style>`、`<main>` 标签，只输出 main 的内部内容。

## 硬约束
- 所有链接必须是 HTML `<a class="source-link" href="..." target="_blank">📎 查看原文</a>`，严禁 Markdown 链接语法。
- 不要写内联 `style="..."`，一律用下面的 class。
- 中文全角标点。数字、薪资、日期等关键数据用 `<strong>` 高亮。
- 结尾必须包含信息来源汇总板块 + `<div class="giscus"></div>`。

## 可用结构

### 板块
```html
<div class="section">
  <div class="section-title">板块一 · 今日招聘新闻动态</div>
  ...cards...
</div>
```

### 卡片 + 新闻条目（最常用）
```html
<div class="card">
  <h3>比亚迪：郑州基地计划招聘5300人</h3>
  <div class="news-item">
    <div class="news-meta">
      <span class="tag tag-byd">比亚迪</span>
      <span class="badge hot">🔥 大规模招聘</span>
      <span>2026年9月</span>
    </div>
    <p>正文段落，<strong>关键数据</strong>加粗。</p>
    <a class="source-link" href="https://..." target="_blank">📎 查看原文</a>
  </div>
  <div class="news-item">...</div>
</div>
```

### 徽章 badge
`badge hot` / `badge new` / `badge-info` / `badge-success` / `badge-warn` / `badge-danger` / `badge-high` / `badge-mid` / `badge-low` / `badge-purple`

### 标签 tag
`tag tag-byd` `tag tag-chery` `tag tag-geely` `tag tag-faw` `tag tag-vw` `tag tag-tesla`
通用：`tag-accent` `tag-green` `tag-purple` `tag-orange` `tag-teal` `tag-pink` `tag-info` `tag-amber` `tag-red`

### 提示框
```html
<div class="highlight-box"><div class="highlight-title">💡 建议</div><p>...</p></div>
<div class="info-box"><div class="info-title">ℹ️ 说明</div><p>...</p></div>
<div class="tip-box"><div class="tip-title">✅ 提示</div><p>...</p></div>
<div class="warning-box"><div class="warning-title">⚠️ 注意</div><p>...</p></div>
```

### 表格
```html
<div class="table-wrap">
  <table class="summary-table">
    <thead><tr><th>企业</th><th>岗位</th><th>薪资</th><th>地点</th></tr></thead>
    <tbody>
      <tr><td>比亚迪</td><td>结构工程师</td><td>15-25万</td><td>深圳</td></tr>
    </tbody>
  </table>
</div>
```

### 网格布局
`card-grid` `card-grid-2` `card-grid-3` 包住多个 `<div class="card">`。

### 岗位卡
```html
<div class="job-card">
  <div class="job-title">高级结构工程师</div>
  <div class="job-meta"><span class="pill pill-location">合肥</span><span class="pill pill-salary">20-35万</span></div>
  <div class="job-desc">岗位描述...</div>
</div>
```

### 讨论/热议条目
```html
<div class="discussion-item">
  <div class="discussion-title">话题标题</div>
  <div class="discussion-meta"><span class="discussion-author">来源</span><span class="discussion-time">2026-09</span></div>
  <p>观点摘要...</p>
</div>
```

### 统计
```html
<div class="stats-grid">
  <div class="stat-box"><div class="count-badge">1123</div><div class="label">在招职位</div></div>
</div>
```

### 其他工具类
排版：`text-center` `text-sm` `text-lg` `text-xl` `text-muted` `muted` `font-bold` `font-semibold`
颜色：`text-accent` `text-accent-green` `text-accent-orange` `text-accent-purple` `text-danger` `text-warning`
间距：`mt-1`~`mt-6` `mb-1`~`mb-6` `gap-sm` `gap-md` `gap-lg`
布局：`flex` `flex-between` `flex-center` `items-center` `justify-between` `flex-wrap` `flex-col`
其它：`divider` `separator` `note-box` `timeline-item` `salary-grid` `salary-item` `progress-bar` `progress-fill` `emoji-list`

## 结尾模板（每个报告都必须有）
```html
<div class="section">
  <div class="section-title">信息来源汇总</div>
  <div class="table-wrap">
    <table class="summary-table">
      <thead><tr><th>来源标题</th><th>链接</th><th>时间</th></tr></thead>
      <tbody>
        <tr><td>xxx</td><td><a class="source-link" href="https://..." target="_blank">📎 查看原文</a></td><td>2026-09</td></tr>
      </tbody>
    </table>
  </div>
</div>

<div class="giscus"></div>
```

## 篇幅要求
每个报告正文 8000–20000 **字符**（约 4–8 个板块、15–40 个条目）。宁可内容扎实，不要注水空话。

> ⚠️ **「字符」不是「字节」**：用 `len(open(路径, encoding='utf-8').read())` 计量。
> 中文正文约 1.6 字节/字符 —— 30K 字节 ≈ 19K 字符，**不要拿字节数当字数**，
> 否则会写出 3–4 万字符的超标文章（2026-09-19 有 7/13 分类因此超标、事后整批压缩）。
> 落笔前先定目标：**12000–19000 字符**，写完用 `python scripts/strict_check.py` 自查。
