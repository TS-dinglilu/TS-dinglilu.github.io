# 每日日报自动更新工作流

> 本文档是每日自动化任务的执行手册。站点：https://ts-dinglilu.github.io/
> 仓库：`D:\研二\github.auto\repo`（main 分支直推）｜正文草稿：`D:\研二\github.auto\repo\content\`

## 0. 工作区与仓库的对应关系（2026-09-15 起）

**仓库是唯一真源**：所有资产都在 git 里，换机器 clone 仓库即可完整续接工作流，
不再依赖工作区根目录下散落的文件夹。

```
D:\研二\github.auto\        ← 工作区（本身不是仓库）
├─ repo\                    ← git 仓库根 = 站点根 = GitHub Pages 发布源
│  ├─ content\              ← 13 分类正文草稿 + STYLE_GUIDE.md（原工作区根的 content，已迁入）
│  ├─ logs\                 ← 推送日志 / 审计记录 / 归档页（原工作区根的 logs，已迁入）
│  ├─ .workbuddy\           ← 目录联接 → 工作区根的 .workbuddy（记忆与工作日志）
│  ├─ scripts\              ← 构建 / 发布 / 体检脚本
│  └─ <13 个分类目录>\      ← 已生成的日报
└─ backups\                 ← 历史快照，体积大，不入 git（见 §0.1）
```

**所有命令一律在 `repo\` 目录下执行**，相对路径以仓库根为基准：

| 用途 | 路径 |
|---|---|
| 写正文 | `content\<分类>.html` |
| 写作规范 | `content\STYLE_GUIDE.md` |
| 补漏正文 | `content\backfill<MMDD>\` |
| 日志落盘 | `logs\push_YYYYMMDD.log` |

### 0.1 backups\ 为什么不进仓库
`backups\` 存的是历史快照（如 `20260914_2052_pre-visual-unify`），压缩后仍有 17MB，
放进 git 会让每次 clone 都多下十几 MB，因此**不纳入版本库**，改用网盘归档。
日常要恢复某份历史报告，直接用 git 历史即可，不必依赖 backups\：
```bash
git log --oneline -- car-recruit/report_20260914.html   # 找到那次提交
git checkout <sha> -- car-recruit/report_20260914.html  # 取回该版本
```

### 0.2 换机器 / 重装后如何续接
```bash
git clone https://github.com/TS-dinglilu/TS-dinglilu.github.io.git repo
cd repo
python scripts/audit_site.py          # 确认站点完整
python scripts/publish_all.py --push  # 照常跑当日流程（推送兜底见 §1.7）
```
记忆目录（`.workbuddy\`）是可选的：它是 WorkBuddy 的工作记忆，本地会重新积累，
需要恢复时从仓库对应路径取回即可。

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
python scripts/audit_site.py                # 全站体检：结构/死链/索引/主页/漏期
```
体检报告里 `[ERROR] 漏期` 段会直接列出「哪天缺哪些分类」。**先补做缺失日期**，
再继续今天的流程。补做用专用工具（自动校验正文 → 批量构建 → 重建索引）：

> **全天缺失也要看 `[WARN] 漏期`**：`[ERROR] 漏期` 只能发现「某天部分分类缺」，
> 如果某一天 **13 个分类全都没有报告**，就没有参照物、老逻辑查不出来
> （2026-09-16 就是这样被静默漏掉的）。2026-09-18 起 `audit_site.py` 增加了连续区间检查，
> 会以 `[WARN]` 打出「13 个分类全部没有该日报告（全天缺失）」。
> 另外**开工前务必先看 `git status`**：中断的会话可能已经写好正文、甚至构建好报告但**没提交**
> （2026-09-17 就是这种状态，报告在本地躺着、线上仍是 09-15）。
> 这种情况先 `git add -A && git commit && git push` 抢救，**不要重写正文**。

```bash
python scripts/build_backfill.py --date 2026-09-10 --dir content/backfill0910 --check  # 先校验
python scripts/build_backfill.py --date 2026-09-10 --dir content/backfill0910          # 再构建
```
正文按 `<分类>.html` 命名放在 `--dir` 目录里；缺失的分类会被列出（需补写正文），
已存在的报告默认跳过（加 `--force` 才覆盖）。`--push` 可一步完成构建 + 更新主页 + 推送。

### 1.5 全站修复（出现结构/链接问题时）
```bash
python scripts/fix_site.py --dry-run        # 先看将要改什么
python scripts/fix_site.py                  # 实际修复（幂等，可重复跑）
```
自动修掉：指向不存在路径的死链、残留的旧品牌名、缺失的 giscus 评论区、
重复 `<body>` 标签、指向已归档页面的返回链接。

### 1.6 全站视觉统一（尾部结构不一致时）
```bash
python scripts/unify_style.py --dry-run      # 预演：列出每份文件的替换判断
python scripts/unify_style.py                # 执行（幂等，重复跑不改动已统一的文件）
python scripts/unify_style.py --show car-recruit/report_20260914.html   # 预览单份替换后的尾部
```
把所有历史报告的**结尾区块**统一成标准结构（评论区卡片 + 页脚 + 返回顶部按钮 + giscus 脚本）。
标准尾部定义在 `scripts/tail_template.py`，是**唯一真源**，`build_report.py`（每日新建）也用它，
因此新老报告天然一致。要点：
- 只认「注释 / 容器 class / 页脚标签」这类可靠标记，**不会**把正文里的「评论区」字样当标记；
- 区间内若含真实「信息来源汇总」板块，会原样保留（若外层是页脚标签则降级为 `<div class="section">`，避免双页脚）；
- 替换前会清掉区间**之外**残留的旧评论区与内联 giscus 脚本（含被误放进 `<head>` 的）；
- 逐份校验 `<div>` 配平 / 单一 `</body>`、`</html>` / 结尾 `</html>` / 含 giscus，不通过则跳过不写。

### 1.7 推送兜底：github.com:443 整段不可达时（SSH over 443）
```bash
python scripts/ssh_fallback_push.py --check     # 只探测各通道连通性
python scripts/ssh_fallback_push.py --selftest  # 自检：取凭据→注册密钥→SSH 认证→撤销（不推送）
python scripts/ssh_fallback_push.py             # 执行兜底推送（通道不适用会自动跳过）
```
国内网络下 `github.com:443` 会**直连和本地代理都到不了**（`curl` 走环境变量代理能通、`git` 不能，
因为 git 全局配置里 `http.https://github.com.proxy` 是空值 = 显式禁用代理）。
但 `ssh.github.com:443`、`github.com:22`、`api.github.com` 通常仍然可用，所以：

`publish_all.py --push` 现在会自动兜底，常规通道全失败后会调 `ssh_fallback_push.py`：
生成一次性 ed25519 密钥 → 用凭据里的 token 注册为**可写临时部署密钥** → 走
`ssh://git@ssh.github.com:443/<owner>/<repo>.git` 快进推送 → **finally 里立即撤销密钥**并删除私钥/凭据文件。
- 自带开关：先探测 `github.com:443`，**通了就直接跳过**，不会平白注册密钥；
- 想禁用：`python scripts/publish_all.py --push --no-ssh-fallback`；
- 密钥只存活数秒，脚本会打印撤销结果（HTTP 204）；收尾可 `--selftest` 或查仓库 Deploy keys 确认无残留。
- **注意**：GitHub REST API 虽然通，但**不能用来推这个仓库** —— 一次改动动辄 17MB+/197 文件，
  `push_files` 的内容要由模型当参数传入（量级不可行），且无法指定提交者/时间，会造出不同 SHA 产生分叉。

### 2. 搜集素材 + 写正文
- **写作规范必读**：`content\STYLE_GUIDE.md`（仓库内，已随仓库同行）
- 对每个分类：先看上一份报告的板块结构（`<分类>/report_最新.html`），再用 WebSearch 搜集
  **当天及近日**真实资讯（重点 24–48 小时内），按同样板块结构写正文，
  覆盖保存到 `content\<分类>.html`
- 每个分类至少搜 5–8 次，覆盖不同角度；每份 8000–20000 字符
- 避免与上一期内容重复，聚焦最新进展
- **可用多个并行子代理分工加速**（例如 5 个代理各负责 2–3 个分类）

### 3. 一键发布
```bash
cd D:\研二\github.auto\repo
python scripts/publish_all.py --push
```
该脚本会自动完成：内容校验（禁 Markdown 链接/必需板块/文档标签/长度）→ 批量构建 13 分类报告
→ 重建各分类归档索引 → 更新主页卡片（最新日期+累计期数）与总数统计 → **全站自查**
→ git 提交推送。自查失败会打出 `[WARN]` 但仍继续推送，收工前请按提示修掉。

推送逻辑（针对本机环境定制）：**优先走"凭据直连通道"**（`scripts/export_git_cred.ps1`
从 Windows 凭据管理器导出凭据 → 用 git store 助手推送，约 15 秒完成）；失败才退回常规
`git push` 重试 3 次。原因是本机的 git 凭据助手（helper-selector → GCM）在非交互场景会挂起，
常规 `git push` 可能几分钟无响应。

只想构建不推送：去掉 `--push`。只更新主页：加 `--no-build`。

### 4. 验证
```bash
python scripts/audit_site.py                                             # 本地全站体检，应输出「全部通过 ✓」
curl -s -o /dev/null -w "%{http_code}\n" https://ts-dinglilu.github.io/car-recruit/report_<日期>.html
```
GitHub Pages 推送后 1–2 分钟生效，返回 200 即成功。

**外链真实性核验（每轮必做，一条命令）**：
```bash
python scripts/check_links_today.py          # 只报告
python scripts/check_links_today.py --fix    # 顺带把 https 不通的链接改写成 http
```
它会抽取 `content/*.html` 里所有 `class="source-link"` 的 href、去重后并发探测，
返回 `200/301/302/403/401` 视为有效（`403/401/412` 多为反爬，不算死链），
**只有 `000` / `404` 才需要处理**；https 首轮不通的会自动复测一次，仍不通再试 http，
http 可达的直接给出改写建议（`--fix` 会写回 `href`）。
- ⚠️ **并发不要调高**：16 路并发会让 arXiv 等站点大面积超时、误报成「不通」
  （实测 arXiv 单条复测全是 200）。脚本已固定为 6 路，别擅自加大。
- ⚠️ 少数站点**整站对本机不可达**（实测 `www.nowcoder.com`，连站点根都是 `000`），
  这属站点级屏蔽而非死链：用检索核验页面是否真实存在（如 `WebFetch` 打开一次）再决定去留。
- 仍有个别中文站 **https 不可达但 http 可访问**（实测 `finance.people.com.cn`、`campus.nio.com`、
  `24365.ah.smartedu.cn`、`m.yingjiesheng.com`、`www.nssc.cas.cn`），改 `http://` 即可。

arXiv 类链接可以直接验真：`curl -s -o /dev/null -w "%{http_code}" https://arxiv.org/abs/<编号>`，200 = 编号真实存在。
**注意**：搜索引擎/代理给出的编号也可能是模型顺推的假号，务必抽验若干条；
某分类若引用 `xxx.edu.cn/info/<栏目>/<文章>.htm` 这类深链，`404` 就说明编号是编的 —— 
去该站栏目列表页（如 `https://sxy.ahut.edu.cn/index/ltjz.htm`）找真实文章，或改为引用栏目列表页。


## 质量红线
- 所有链接必须真实可点击（来自搜索结果），严禁编造 URL 和精确假数据
- 历史报告只增不删
- 若某分类当天确实无素材，写近期梳理并在正文标注"今日动态较少，以下为近期梳理"
- 网络问题导致 push 失败时，本地提交会保留；网络恢复后 `git push origin main` 即可，不要重新生成

## 常见问题
| 现象 | 处理 |
|---|---|
| `git push` 报 `Failed to connect to github.com:443` | 国内网络问题。跑 `python scripts/publish_all.py --push` 会自动兜底（临时部署密钥 + SSH over 443，见 §1.7）；也可先 `python scripts/ssh_fallback_push.py --check` 看哪条通道通。本地提交不会丢 |
| `git push` 长时间无响应（不报错也不返回） | 凭据助手挂起。直接跑 `python scripts/publish_all.py --push`，会自动走凭据直连通道；或手动 `powershell -File scripts\export_git_cred.ps1` 拿到凭据文件后按脚本注释里的命令推送 |
| 子代理报 429 频率限制 | 等额度重置，或改用 `model: lite` 的代理执行（实测 `lite` 可立即绕过） |
| Bash/Terminal 全线报 `command not found`（`dirname`/`ls`/`git` 都不识别） | 本机偶发 PATH 损坏。命令前先 `export PATH="/c/Users/dingliu/.workbuddy/binaries/PortableGit/versions/1.2.0/usr/bin:/c/Users/dingliu/.workbuddy/binaries/PortableGit/versions/1.2.0/mingw64/bin:/c/Windows/System32:/c/Windows:$PATH"`，Python 用绝对路径 `C:/Users/dingliu/.workbuddy/binaries/python/versions/3.13.12/python.exe` |
| 某分类构建报"找不到 `<main>` 区块" | 属正常（该分类用通用骨架），构建器会自动走通用路径 |
| 主页卡片「最新日期/累计期数」与「已生成日报」总数不更新 | 主页 index.html 若被设计编辑器改写，元素会带 `data-page-node-id` 等自定义属性，老版 `update_homepage.py` 的精确字符串匹配（`<div class="stat-num">` 等）会失效。2026-09-14 已改为「前缀 + 任意属性」正则，重跑 `python scripts/update_homepage.py` 即恢复。若仍不更新，先确认 `class="stat-num"` / `class="auto-meta"` / `class="auto-updated"` 的 class 名是否被改掉 |
| 提示某某日期缺失报告（漏跑） | 说明自动化当天没跑（机器/应用离线不会补跑）。为缺失日期写好正文放到一个目录（如 `content/backfill0910/`），再 `python scripts/build_backfill.py --date 2026-09-10 --dir content/backfill0910` 批量补构建；缺的分类会被列出 |
| 想批量清理历史报告的坏链接 / 缺评论区 | `python scripts/fix_site.py --dry-run` 先看清单，去掉 `--dry-run` 执行。幂等，重复跑不会重复改 |
| 历史报告尾部样式不统一（评论区/页脚五花八门） | `python scripts/unify_style.py --dry-run` 先看清单，再去掉 `--dry-run` 执行。标准尾部由 `scripts/tail_template.py` 定义，`build_report.py` 共用同一真源 |
| 想快速知道站点哪里坏了 | `python scripts/audit_site.py`（加 `--quiet` 只输出问题；退出码非 0 表示有 ERROR） |
| **Bash 里调 `powershell.exe` 被拒**（提示 bypasses PowerShell security checks） | 这是安全策略，不是脚本坏了。手动导出 git 凭据走不通，**直接用 `python scripts/publish_all.py --push`**（Python 子进程里调 ps1 是允许的），或改用 PowerShell 工具执行 `scripts/export_git_cred.ps1` |
| 跑 `publish_all.py --push` 后**输出为空 / 看不出进度** | 不要 `\| tail`：管道缓冲 + 进程被 SIGTERM 时输出全丢，看起来像静默失败。改成重定向落盘：`python scripts/publish_all.py --push > logs/push_$(date +%Y%m%d).log 2>&1`，再读日志 |
| 外链批量 curl 全部返回 `000`，但单独 curl 又正常 | 两种原因：① URL 清单是 Windows CRLF，`while read` 带出尾部 `\r` 把 URL 弄坏了 —— 读前 `tr -d '\r'`；② **并发过高**（16 路以上）把站点打成超时，看起来像全站断网。用 `python scripts/check_links_today.py`（已固定 6 路并发 + 自动复测）代替手写循环 |
| 某一天的报告一个都没有，`audit_site.py` 却不报漏期 | 老逻辑只比对「其它分类有的日期」，全天缺失无参照物。2026-09-18 起已补上连续区间检查，会打 `[WARN] 漏期 …全天缺失`。补做方式同上（写 `content/backfill<MMDD>/` → `build_backfill.py`） |
| 推送成功、`contents` API 也能查到文件，但线上页面 404 | GitHub Pages 部署有延迟，新文件可能比同批的其它文件晚 1–3 分钟生效。**轮询重试**即可（实测 `report_20260918.html` 首查 404、约 2 分钟后 200），不要因此重复推送 |
| 主页出现两份 `index.html` / `homepage_index.html` | 后者是个人主页的旧版本，已被 `index.html` 取代，已归档到 `logs/archive/`。不要再往 repo 里放第二份主页，否则 `update_homepage.py` 只改 `index.html`，两份会逐渐不一致 |
