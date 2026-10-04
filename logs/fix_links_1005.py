# -*- coding: utf-8 -*-
import io

def rep(path, pairs):
    with io.open(path, encoding='utf-8') as f:
        t = f.read()
    for old, new, cnt in pairs:
        n = t.count(old)
        assert n == cnt, "%s: expect %d got %d for: %s..." % (path, cnt, n, old[:60])
        t = t.replace(old, new)
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)
    print("OK %s (%d replacements)" % (path, len(pairs)))

# A. jiangsu-recruit: cqu.cqbys -> job.byd.com (table row first, then body anchor)
rep('content/jiangsu-recruit.html', [
    ('<tr><td>比亚迪27届秋招正式批（重庆大学毕业生就业信息网）</td><td><a class="source-link" href="https://cqu.cqbys.com/campus/view/id/734787" target="_blank">📎 查看原文</a></td><td>2026-10 在招</td></tr>',
     '<tr><td>比亚迪校招官方门户·27届秋招正式批进行中</td><td><a class="source-link" href="https://job.byd.com/portal/pc" target="_blank">📎 查看原文</a></td><td>2026-10 在招</td></tr>', 1),
    ('据重庆大学毕业生就业信息网发布的转帖，比亚迪27届秋招<strong>正式批正在进行中</strong>，热招岗位归为六类：',
     '比亚迪官方校招门户显示，27届秋招<strong>正式批正在进行中</strong>，在招岗位归为六大类：', 1),
    ('<a class="source-link" href="https://cqu.cqbys.com/campus/view/id/734787" target="_blank">📎 查看原文</a>',
     '<a class="source-link" href="https://job.byd.com/portal/pc" target="_blank">📎 查看原文（比亚迪校招官方门户）</a>', 1),
])

# B. car-recruit: zccareer.zufe -> niuqizp
rep('content/car-recruit.html', [
    ('<tr><td>蔚来2027届全国区域公司秋季校园招聘（浙江财经大学）</td><td><a class="source-link" href="https://zccareer.zufe.edu.cn/campus/view/id/869977" target="_blank">📎 查看原文</a></td><td>2026-12-21 有效期</td></tr>',
     '<tr><td>蔚来27届区域公司秋招专场·全国100+城市（牛企直聘）</td><td><a class="source-link" href="https://jobs.niuqizp.com/schedule-7smkNNtNz.html" target="_blank">📎 查看原文</a></td><td>2026-10 在招</td></tr>', 1),
    ('浙江财经大学就业网另挂出<strong>蔚来 2027 届全国区域公司秋季校招</strong>（有效期至 12 月 21 日），覆盖全国 49 家区域公司、100+ 城市的销售顾问、交付运营、空间运营、售后服务岗。',
     '牛企直聘同步挂出<strong>蔚来 27 届区域公司秋招专场</strong>，覆盖全国 100+ 城市的蔚来顾问、乐道顾问、交付运营、区域市场、空间运营、售后服务、能源运营岗，2027 届应届生（2026 年 9 月—2027 年 8 月毕业）可投。', 1),
    ('<a class="source-link" href="https://zccareer.zufe.edu.cn/campus/view/id/869977" target="_blank">📎 查看原文（区域公司通道）</a>',
     '<a class="source-link" href="https://jobs.niuqizp.com/schedule-7smkNNtNz.html" target="_blank">📎 查看原文（区域公司通道）</a>', 1),
])

# C. anhui-recruit: wsyu.91wllm + www.cqbys (table rows first)
rep('content/anhui-recruit.html', [
    ('        <tr><td>奇瑞汽车股份有限公司2027届校园招聘·岗位与流程（武昌首义学院就业信息网）</td><td><a class="source-link" href="https://wsyu.91wllm.cn/en/campus/view/id/1003576" target="_blank">📎 查看原文</a></td><td>2026-10 在招</td></tr>\n',
     '', 1),
    ('<tr><td>芜湖埃科动力系统有限公司展位·七岗位（重庆城市科技学院双选会）</td><td><a class="source-link" href="https://www.cqbys.com/jobfair91/stand/sid/297927" target="_blank">📎 查看原文</a></td><td>2026-10-21 举办</td></tr>',
     '<tr><td>芜湖埃科动力系统有限公司在招主页·七岗位（重庆市智慧就业平台）</td><td><a class="source-link" href="https://24365.cq.smartedu.cn/companydetail/view/id/780431/tab/1" target="_blank">📎 查看原文</a></td><td>2026-10 在招</td></tr>', 1),
    ('反向提醒：<strong>AI算法、智能驾驶两档对机械背景命中率低，不要占用志愿</strong>；另据武昌首义学院就业网转载的简章，职能类岗位需求专业也含机械类，但岗位量小、竞争集中，仅作为保底认知。',
     '反向提醒：<strong>AI算法、智能驾驶两档对机械背景命中率低，不要占用志愿</strong>；职能与支持类岗位量小、竞争集中，仅作为保底认知。', 1),
    ('<a class="source-link" href="https://wsyu.91wllm.cn/en/campus/view/id/1003576" target="_blank">📎 查看原文</a>',
     '<a class="source-link" href="https://jdjyw.jlu.edu.cn/portal/recruit/details?id=6cd2ea0843124463a7d73d7751a92d4c" target="_blank">📎 查看原文（2027届校招简章·吉林大学就业网）</a>', 1),
    ('重庆城市科技学院10月21日「周三相约·职为你来」专场招聘会展位信息显示，<strong>芜湖埃科动力系统有限公司</strong>（繁昌经济开发区，1000-5000人规模，注册资本7.2亿元）挂出七个岗位',
     '重庆市智慧就业平台收录的该公司在招主页显示，<strong>芜湖埃科动力系统有限公司</strong>（繁昌经济开发区，1000-5000人规模）挂出七个岗位', 1),
    ('异地读者不必赴重庆参会，按页面岗位口径直接在芜湖本地渠道投递即可。',
     '读者不必等双选会，按平台岗位口径直接在芜湖本地渠道投递即可。', 1),
    ('② 芜湖埃科动力系统：总装工艺/机加工工艺工程师岗位落地，10-21重庆双选会展位可查',
     '② 芜湖埃科动力系统：总装工艺/机加工工艺工程师岗位落地，智慧就业平台在招主页可查', 1),
    ('<span class="badge-info">📊 工艺序列</span><span>2026-10-21 双选会</span>',
     '<span class="badge-info">📊 工艺序列</span><span>2026-10 在招</span>', 1),
    ('<a class="source-link" href="https://www.cqbys.com/jobfair91/stand/sid/297927" target="_blank">📎 查看原文</a>',
     '<a class="source-link" href="https://24365.cq.smartedu.cn/companydetail/view/id/780431/tab/1" target="_blank">📎 查看原文（公司主页·重庆市智慧就业平台）</a>', 1),
])

# D. xiaomi-recruit: quanzhi -> niuxiaoer + aiqicha (table row first)
rep('content/xiaomi-recruit.html', [
    ('<tr><td>小米江城新厂长白班275元/天·25元/时高价档至10-21（全职招聘网·劳务口径）</td><td><a class="source-link" href="https://www.quanzhi.com/job/6a787f7df87cf99210bc231d" target="_blank">📎 查看原文</a></td><td>2026-10 行情</td></tr>',
     '<tr><td>武汉小米线束厂普工·25元/时高价档期满回落（牛小二·劳务口径）</td><td><a class="source-link" href="https://www.niuxiaoer.cn/zhaopininfo/2080197564330856450.html" target="_blank">📎 查看原文</a></td><td>2026-10 行情</td></tr>\n        <tr><td>武汉小米工厂普工待遇汇总口径（爱企查·u知识）</td><td><a class="source-link" href="https://aiqicha.baidu.com/details/ugknowledge?id=3df429716a479d92840e19fbdb897cf4" target="_blank">📎 查看原文</a></td><td>2026-10</td></tr>', 1),
    ('全职招聘网挂出的武汉蔡甸区岗位信息显示，<strong>与小米产线相关的普工/操作工岗位给出「25 元/时高价档（持续至 10 月 21 日）、10 月 22 日起 22.5 元/时（含 0.5 元工龄补贴）」的报价</strong>，工作地址位于武汉经开区「经开·智造 2045 创新谷」，长白班、包吃、湖景房双人间、每月 5 号发薪，年龄放宽到 23—50 岁。',
     '劳务招聘平台牛小二挂出的武汉小米线束厂岗位信息显示，<strong>普工给出「25 元/时高价档、期满回落至 22.5 元/时（含 0.5 元工龄补贴）」的报价结构</strong>，年龄 23—40 岁、包两餐、宿舍 6—8 人间（178—220 元/月）；爱企查「u 知识」汇总口径为武汉小米普工时薪约 20—28 元、综合月薪 6000—10000 元档。', 1),
    ('<h3>② 武汉一线用工观察：劳务高价档抢人与「经开智造 2045」园区</h3>',
     '<h3>② 武汉一线用工观察：劳务高价档抢人与产线旺季信号</h3>', 1),
    ('<a class="source-link" href="https://www.quanzhi.com/job/6a787f7df87cf99210bc231d" target="_blank">📎 查看原文</a>',
     '<a class="source-link" href="https://www.niuxiaoer.cn/zhaopininfo/2080197564330856450.html" target="_blank">📎 查看原文（牛小二·劳务口径）</a>\n      <a class="source-link" href="https://aiqicha.baidu.com/details/ugknowledge?id=3df429716a479d92840e19fbdb897cf4" target="_blank">📎 查看原文（爱企查·武汉小米普工待遇口径）</a>', 1),
])

# E. byd-recruit: qcgys -> asianev (table row first)
rep('content/byd-recruit.html', [
    ('<tr><td>汽车产业一周要闻速览：比亚迪硫化物全固态电池2027年Q1千台级示范装车（汽车供应商网）</td><td><a class="source-link" href="https://www.qcgys.com/show_article-92834.html" target="_blank">📎 查看原文</a></td><td>2026-09-17</td></tr>',
     '<tr><td>比亚迪全固态电池通过车规级验证·400Wh/kg/CLTC 1218km（亚洲新能源汽车网）</td><td><a class="source-link" href="https://www.asianev.com/news/show-23181.html" target="_blank">📎 查看原文</a></td><td>2026-09</td></tr>', 1),
    ('行业周报补充了技术档案：', '亚洲新能源汽车网的报道补充了技术档案：', 1),
    ('<a class="source-link" href="https://www.qcgys.com/show_article-92834.html" target="_blank">📎 查看原文</a>',
     '<a class="source-link" href="https://www.asianev.com/news/show-23181.html" target="_blank">📎 查看原文</a>', 1),
])

# F. chery-recruit: drop qcgys (table row first, then body link line)
rep('content/chery-recruit.html', [
    ('        <tr><td>智界RX获批L3级自动驾驶道路测试牌照（汽车供应商网周报）</td><td><a class="source-link" href="https://www.qcgys.com/show_article-92834.html" target="_blank">📎 查看原文</a></td><td>2026-09-16</td></tr>\n', '', 1),
    ('      <a class="source-link" href="https://www.qcgys.com/show_article-92834.html" target="_blank">📎 查看原文</a>\n', '', 1),
])

# G. shenzhen-news: bastillepost /hongkong/ -> /nls/ (search-confirmed path)
rep('content/shenzhen-news.html', [
    ('https://www.bastillepost.com/hongkong/article/16894493-', 'https://www.bastillepost.com/nls/article/16894493-', 2),
])

print("ALL DONE")
