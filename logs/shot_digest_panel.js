// 一次性验证脚本：用系统 Edge 打开分类归档页，截图 digest 面板区域
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const browser = await chromium.launch({
    channel: 'msedge',
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    args: ['--headless=new', '--disable-gpu', '--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 900, height: 1000 } });
  const file = 'file:///' + path.resolve('car-recruit/index.html').replace(/\\/g, '/');
  await page.goto(file, { waitUntil: 'load' });
  await page.waitForTimeout(800);
  const el = await page.$('.digest-panel');
  if (!el) { console.log('PANEL NOT FOUND'); await browser.close(); process.exit(1); }
  await el.screenshot({ path: 'logs/digest_panel_check.png' });
  // 同时量一下面板是否溢出容器
  const box = await el.boundingBox();
  const vw = 900;
  console.log('panel box:', JSON.stringify(box), 'viewport:', vw);
  await page.screenshot({ path: 'logs/carrecruit_top_check.png', clip: { x: 0, y: 0, width: 900, height: 700 } });
  await browser.close();
  console.log('OK');
})().catch(e => { console.error('ERR', e.message); process.exit(2); });
