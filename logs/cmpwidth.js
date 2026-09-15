const { chromium } = require('playwright-core');
const { pathToFileURL } = require('url');
(async () => {
  const b = await chromium.launch({ executablePath: 'C://Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', headless: true });
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  for (const f of ['ahut-campus/report_20260914.html','ahut-campus/report_20260915.html']) {
    await p.goto(pathToFileURL('D://研二//github.auto//repo//'+f.replace('/','\\')).href, { waitUntil: 'load' });
    await p.waitForTimeout(600);
    const r = await p.evaluate(() => {
      const c = document.querySelector('.comments-section');
      const f = document.querySelector('footer.footer');
      const cc = c.getBoundingClientRect();
      const ff = f.getBoundingClientRect();
      return { cmtW: Math.round(cc.width), cmtX: Math.round(cc.left), footW: Math.round(ff.width), footX: Math.round(ff.left), bodyW: document.body.getBoundingClientRect().width };
    });
    console.log(f, JSON.stringify(r));
  }
  await b.close();
})();
