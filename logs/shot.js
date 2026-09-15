// 渲染若干报告尾部，截图核对视觉是否统一
const { chromium } = require('playwright-core');
const { pathToFileURL } = require('url');
const path = require('path');
const fs = require('fs');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const ROOT = 'D:\\研二\\github.auto\\repo';
const OUT = 'D:\\研二\\github.auto\\logs\\visual';
fs.mkdirSync(OUT, { recursive: true });

const files = [
  'school-news/report_20260725.html',
  'car-recruit/report_20260803.html',
  'car-recruit/report_20260914.html',
  'weixiaoli-recruit/report_20260806.html',
  'mechanical-recruit/report_20260807.html',
];

(async () => {
  const browser = await chromium.launch({ executablePath: EDGE, headless: true });
  const page = await browser.newPage({ viewport: { width: 1200, height: 900 } });
  for (const rel of files) {
    const url = pathToFileURL(path.join(ROOT, rel)).href;
    await page.goto(url, { waitUntil: 'load', timeout: 30000 }).catch(e => console.log('goto warn', rel, e.message));
    await page.waitForTimeout(1500);
    // 滚到底部，确保尾部进入视口
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(600);
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(600);
    const sy = await page.evaluate(() => window.scrollY);
    console.log('  scrollY=', sy);
    const name = rel.replace(/[\\/]/g, '__').replace('.html', '.png');
    await page.screenshot({ path: path.join(OUT, name) });
    // 统计关键结构
    const stat = await page.evaluate(() => ({
      cmt: document.querySelectorAll('.comments-section').length,
      footer: document.querySelectorAll('.footer, footer.footer').length,
      scrollTop: document.querySelectorAll('.scroll-top').length,
      giscus: document.querySelectorAll('.giscus').length,
      docH: document.body.scrollHeight,
    }));
    console.log(rel, JSON.stringify(stat));
  }
  await browser.close();
})();
