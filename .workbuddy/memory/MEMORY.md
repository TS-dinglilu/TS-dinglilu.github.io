# 项目长期备忘 — github.auto

> 史实与事故经过见 `memory/YYYY-MM-DD.md`；本文件只留**仍生效的规则与索引**。
> 操作细节 `scripts/DAILY_WORKFLOW.md`｜内容规范 `content/STYLE_GUIDE.md`。

## 1. 站点与真源
- 线上 https://ts-dinglilu.github.io/ ｜仓库 `TS-dinglilu/TS-dinglilu.github.io`（main 直推，Pages 1–3 分钟生效）。
- `D:\研二\github.auto\repo` = 站点根 = 发布源 = **唯一真源**；**命令一律在 `repo/` 下执行**。仓库 public（`.workbuddy/` 记忆随之上公开）。
- 布局：`content/` 草稿、`content/deep/` 深度档案、`logs/` 日志、`.workbuddy/` 记忆（目录联接，实体在工作区根）；工作区根另有 `backups/`（不入 git）。换机器 `git clone` 即可续接。
- 34 分类：招聘/资讯 15（car-recruit / mechanical-recruit / school-news / drone-research / ahut-campus / byd-recruit / chery-recruit / chery-insider / geely-recruit / xiaomi-recruit / weixiaoli-recruit / traditional-auto / supply-chain-recruit / research-institute / future-planning / company-reputation，chery-insider=职场口碑，与 chery-recruit 分工「打工体验 vs 招聘新闻」）＋ 地区动态 9 ＋ 地区招聘 9（xuzhou / nanjing / shanghai / hangzhou / jiangzhehu / hefei / anhui / jiangsu / shenzhen 各 `-news` / `-recruit`）。
- 主页筛选标签 8 个：全部/企业招聘/地区招聘/地区动态/校园/科研/企业口碑/个人规划；**只改显示文字，`data-cat` 键名永不动**（JS/digest/audit 靠键名联动）；地区两类各挂 9 卡，chery-insider 归口碑组；与 build_digest.py GROUPS 一一对应；两类地区日报正文 8000–20000 字（strict_check 按 REGION_CATS 判下限）。
- 全站密码门 `guard.js`（密码 0，localStorage 免输）；`password_gate.py` 幂等注入 + 构建时自动注入。
- `digest/` 周记·月记·年记：`build_digest.py` 每周一/1 日/1 月 2 日生成（自动化 f7c42b9c…，每日 06:30 判断触发），不参与每日 publish_all，由 digest 自动化自推；audit VALID 已含 "digest"。**入口只在 34 个分类归档页顶部「📊 周记·月记·年记」面板**（最新一期 chip + 全部归档），由 `update_category_digest_entries()` 幂等维护，`digest-entry` marker 区间整体替换、`rebuild_index` 不碰；主页仅页脚文字链接 —— 用户明确要求主页不放汇总标签/卡片。

## 2. 日常命令（都在 `repo/scripts/`）
- **一条命令**：写完 `content/<分类>.html` → `python scripts/publish_all.py --push`（校验→构建 34 分类→更新主页→发布前自查→提交推送；步骤 3.2–3.4 幂等跑 optimize_site / build_search / build_feed；内置三级推送、漏跑自查、退避重试）。
  ⚠️ 按**当下日期**构建：跨天会话（19 点跑到凌晨）会以新一天为「今天」给全部分类建报告，防重复。
  ⚠️ **content 草稿必须是当天新闻**：拿旧草稿直接发布 = 日期与内容不符的假日报。
- 步骤 4.5 `deep_inject.py`：幂等注入招聘深度档案（真源 `content/deep/<分类>.html` ×19，内容固定=待遇/几险几金/本科·硕士税前税后/班车/人才补贴/福利/加班/事业部数/在招岗位与城市分布/≥3 平台口碑正反并陈），注入在第一个 section 前；正文草稿**不要**手写深度板块；chery-insider / company-reputation 本身是口碑专刊，不注入。税后统一口径（正文必须写明）：月薪×12、个人五险一金约 17.5%（公积金按 7% 估）、免征额 5000 元/月；薪资数字必须有来源链接，查不到写「暂无可靠公开数据」。
- 单分类 `build_report.py --category --date --content`｜补漏 `build_backfill.py --date <日> --dir content/backfill<MMDD>`。
- 外链核验 `check_links_today.py`（`--fix` 自动把 https 不通改写成 http）：抽 `source-link` href → 去重 → 6 路并发（**别调高**，16 路会把 arXiv 打成超时、误报 32 条死链）→ 首轮不通复测 → 回退 http。判据：`403/401/412` 反爬不算死链；**必须带浏览器 UA** `curl -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'`（不带 UA 时 news.qq.com 501、cnyouth 404、163/sohu 403 全是假死链）；只有 `000` 且站点根也 `000` 才算不可达；`xxx.edu.cn/info/<栏目>/<文章>.htm` 返回 404 = 编号是编的，回栏目列表页找真号；**host 与内容语种/主题不符 → 直接判伪造，HTTP 200 也不算数**。部分中文站（`*.cas.cn`、`m.yingjiesheng.com`）https 不通但 http 200。
- 体检三件套：`audit_site.py`（结构/评论区/死链/索引/主页数字/漏期；退出码非 0 = 有 ERROR；漏期 `[ERROR]` 部分分类缺 / `[WARN]` 13 类全缺）｜`fix_site.py`（幂等修历史缺陷，先 `--dry-run`）｜`unify_style.py`（尾部回溯）。**改历史 HTML 前先跑 audit，别对几百个文件盲改。** `update_homepage.py` 主页卡片（幂等）｜`set_giscus_category.py --name <分类> --id DIC_...`。
- **单一真源** `scripts/tail_template.py`：尾部结构（评论区 + 页脚 + 回到顶部 + giscus）与 `CATEGORY_NAMES`（标准日报名），由 build_report.py / unify_style.py 共用 —— **改尾部只改这一处**；`normalize_footer_name()` 构建时强制标准名，根治页脚名漂移。`<title>` 仍从 `<h1>` 派生，别过度修正。

## 3. 内容红线
- 正文只含 `<main>` 内部 HTML；链接一律 `<a class="source-link" href="..." target="_blank">📎 查看原文</a>`，**禁 Markdown 链接**；结尾必须有「信息来源汇总」表格 + `<div class="giscus"></div>`。
- **严禁编造 URL 与精确假数据**；历史报告只增不删；命名 `report_YYYYMMDD.html`；深色主题（#0a0e1a + #00d4ff）。
- 超长压缩优先级（写手初稿常 22K–30K，上限 8000–20000 字）：① 删与专属分类重复的整块（如 car-recruit 的「新能源与新势力」与 weixiaoli/byd 重叠）→ ② 删汇总表同源冗余行 → ③ 删编辑说明框；**正文条目与链接尽量保住**，删完重排「板块N」编号。
- **月度销量年份错配拦截**：搜索常把上一年同月销量当现闻（吉利 273,125=2025-09 被当成 2026-09）。必须用同比/环比与上月、去年同月锚点交叉验算；页面落款或 URL 含上一年份的一律不得标成本年新闻。
- 写手会抄上一期塞 `<div class="report-header">`：car-recruit 属 `<main>` 型骨架**必须保留**；通用型骨架叠加成重复标题块是**站点既有现象**（mechanical/chery/school-news 历史上有 2–4 对），audit 不报，**不要全站修复**。
- 骨架不统一（仅 car-recruit 用 `<main>`），构建器按 `.section/.stats-grid/.nav-links/.card` 锚点切分。老报告（07/08 月）尾部写法不同（内联 style 评论区 / `<div class="footer">` / 来源无标题）属**风格差异非缺陷**，判据看 giscus 能否真加载，不看 class 名。

## 4. 推送与网络
- `github.com:443` 常不可达；`api.github.com`、`*.github.io` 通常正常。**push 失败本地提交不丢，勿重生成内容**。
- **三级推送**（`publish_all.push_with_retry()` 内置）：① 凭据直连（`export_git_cred.ps1` 导出凭据 + store 助手，约 15s；因 `credential.helper=helper-selector` 非交互会静默挂起，需重试 3–4 轮、间隔 ≥25s）→ ② 常规 push 退避重试 → ③ 临时部署密钥 + SSH over 443（`ssh_fallback_push.py`）；禁用兜底 `--no-ssh-fallback`。
  ⚠️ push_with_retry 卡住 >3 分钟别干等，直接跑 `python logs/push_manual.py`（凭据导出 + store helper 限时 push 一步到位，实测一次成功）。
- **配置陷阱**：git 全局 `http.https://github.com.proxy` 是**空值**（禁代理），故 curl 通而 git 不通，别误判「网络全断」。
- **别用 `git status` 判断推送成败**（本机 `origin/main` 跟踪引用长期陈旧）：验远端用 `curl -s https://api.github.com/repos/TS-dinglilu/TS-dinglilu.github.io/commits/main` 或 curl 页面看 200；`git update-ref` 对 packed-refs 无效，需写 loose ref。
- **开工第一件事看 `git status` + `git log -3`**：中断的会话可能已写好正文甚至构建好报告但**没提交**，这种先 `git add -A` + commit + push 抢救，**不要重写正文**（publish_all 内部 `git add -A` 会自然带上）。同时查 `logs/push_YYYYMMDD*.log` 防两个会话并行重复跑。
- Pages 部署延迟：推送后新文件可能晚 1–3 分钟才 200（首查 404、约 2 分钟后 200），此时 contents API 已能查到 → **轮询重试，别重复推送**。⚠️ REST API 不能推此仓库（单次 17MB+/200 文件，`push_files` 会造分叉 SHA）。
- `git commit` 需内联身份：`git -c user.name=TS-dinglilu -c user.email=workbuddy@local commit`。

## 5. Windows / Git Bash 环境坑
- **Bash 偶发 PATH 损坏**（dirname/ls/git/date 全 not found）：前置 `/c/Users/dingliu/.workbuddy/binaries/PortableGit/versions/1.2.0/{cmd,usr/bin,mingw64/bin}` + `System32` + `Windows`；**必须含 PortableGit 的 `cmd`**（git.exe 在那），且写脚本时把这几个目录前置到子进程 `env["PATH"]`（见 `ssh_fallback_push._child_env()`），仅 `which` 定位不够。Python 用绝对路径 `C:/Users/dingliu/.workbuddy/binaries/python/versions/3.13.12/python.exe`。
- **Bash 里 `timeout` 是 Windows `timeout.exe`**（语法 `/T n`），传 GNU 风格参数会直接报无效语法而根本不执行命令 —— 别用它兜底，靠脚本自身超时逻辑。
- **PowerShell**：① 本环境不返回 stdout，要 `Out-File` 再读；② 默认 Restricted，跑 ps1 前 `Set-ExecutionPolicy -Scope Process Bypass -Force`；③ **不能从 Bash 调 powershell.exe**（安全策略拒绝），走 Python 子进程。ps1 中文须 `utf-8-sig` 落盘（否则 PS 5.1 按 GBK 解析报错）；`$Host` 保留变量；git config 路径用正斜杠。
- 跑 `publish_all.py --push` **别管到 `tail`**（缓冲 + SIGTERM = 输出全丢），落盘 `> logs/push_YYYYMMDD.log 2>&1`。
- Windows 临时清单 CRLF 会毁 shell 循环：读前 `tr -d '\r'`（或 Python 写 `newline="\n"`）。判据：单条 200、循环全 000 → 查数据而非网络。
- 浏览器自动化：`agent-browser` 下 Chrome 会失败（源被墙），用系统 Edge + 隔离目录的 `playwright-core`。子代理 429 限流 → `model: "lite"` 绕过。

## 6. 站点基建层（2026-10-15 全站优化）
- **禁再引入 Google Fonts**（link/@import 都禁）：已全站移除（report.css 的 @import 是首屏白屏根源），用本地系统字体栈；audit 抓不到，靠 review。
- **canonical 新约定**：报告页 og:url/canonical 指向报告自身（og:type=article）；只有归档页/主页指向目录/站点根；audit_site 判据已同步，勿改回。
- 幂等工具链（publish_all 步骤 3.2–3.4 自动跑，日常勿手动）：`optimize_site.py`（head 收敛，指纹 `optimize_site:head`，改 head 规则升 `OP_VERSION` 即可全站重收敛）、`build_search.py`（索引 803 条 + `search-entry` marker）、`build_feed.py`（RSS 60 期）；`fix_meta.py` 已弃用。
- 功能页 `/search.html`（索引只存板块名/h3 条目/摘要，刻意不存全文防 JSON 膨胀）、`/feed.xml`、`/manifest.webmanifest`、og 封面 `/assets/cover.png`（改版重跑 make_cover.py，需 venv Pillow：`C:/Users/dingliu/.workbuddy/binaries/python/envs/default/Scripts/python.exe`）。CSS 可访问性固化在 assets/report.css 尾部（marker `a11y-font-enhance:v1`：reduced-motion / :focus-visible / skip-link / 窄屏表格滚动）。
- audit_site 白名单/判定：`SITE_RESOURCE_SEGS`（assets/search/feed/manifest）、根绝对路径 href 相对仓库根解析、`_page_expected_url` 报告页指向自身。
- **主页数字静默不更新**：index.html 曾被编辑器批量加 `data-page-node-id`，已改「前缀 + 任意属性」正则；跑完务必核对主页数字真变了。主页只有 `repo/index.html`；旧 `homepage_index.html` 已归档 `logs/archive/`，**别再放回 repo**。
- giscus 已切 `General`（`DIC_kwDOTjqaJc4DCIL2`），访客可评论；分类 Announcements …DCIL1｜General …DCIL2｜Q&A …DCIL3｜Ideas …DCIL4｜Show and tell …DCIL5｜Polls …DCIL6。查 ID：`curl -s "https://giscus.app/api/discussions/categories?repo=<owner/repo>"`。
- 自动化「每日自动化新闻推送-13分类日报」每天 05:00，id `6c0d7c75-5de1-4573-84d2-a50b7870b3d9`，工作空间 `D:\研二\github.auto\repo`；**机器/应用不在线不会补跑，需人工补做**。跨天恢复执行先 `git log` + `ls <分类>/report_*.html` 核实上轮建到哪天，避免重做/漏做。

## 7. 用户背景
张恒辰（称「恒辰」），安徽工业大学机械工程硕士（研二），四旋翼无人机飞行控制与仿真（MATLAB/Simulink + Python 强化学习），徐州人，求职车企/机械/研究院，正赶毕业论文开题报告。内容要贴这些背景。
