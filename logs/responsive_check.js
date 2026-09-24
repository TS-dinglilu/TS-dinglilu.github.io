// 检测页面在手机/电脑宽度下是否横向溢出 + 截图
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright-core");

const ROOT = "D:/研二/github.auto/repo";
const OUT = "D:/研二/github.auto/repo/logs/resp_shots";
fs.mkdirSync(OUT, { recursive: true });

const PAGES = [
  { name: "home", file: "index.html" },
  { name: "sc_archive", file: "supply-chain-recruit/index.html" },
  { name: "sc_report", file: "supply-chain-recruit/report_20260924.html" },
];

const VIEWPORTS = [
  { tag: "mobile", width: 375, height: 812 },
  { tag: "desktop", width: 1440, height: 900 },
];

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    channel: "msedge",
  });
  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: vp.tag === "mobile" ? 2 : 1,
      isMobile: vp.tag === "mobile",
      hasTouch: vp.tag === "mobile",
    });
    const page = await ctx.newPage();
    for (const p of PAGES) {
      const url = "file:///" + path.join(ROOT, p.file).replace(/\\/g, "/");
      await page.goto(url, { waitUntil: "networkidle", timeout: 60000 }).catch(() => {});
      await page.waitForTimeout(1500);
      const m = await page.evaluate(() => {
        const doc = document.documentElement;
        const offenders = [];
        document.querySelectorAll("body *").forEach((el) => {
          const r = el.getBoundingClientRect();
          if (r.width > 0 && (r.right > doc.clientWidth + 2 || r.left < -2)) {
            const cs = getComputedStyle(el);
            if (cs.position === "fixed") return;
            // 跳过可滚动容器的直接子元素误报: 只记录 body 级撑破
            if (offenders.length < 8) {
              offenders.push(
                el.tagName.toLowerCase() +
                  (el.className && typeof el.className === "string"
                    ? "." + el.className.split(" ").slice(0, 2).join(".")
                    : "") +
                  " right=" + Math.round(r.right)
              );
            }
          }
        });
        return {
          scrollW: doc.scrollWidth,
          clientW: doc.clientWidth,
          overflow: doc.scrollWidth > doc.clientWidth + 2,
          offenders,
        };
      });
      const flag = m.overflow ? "!! 溢出" : "ok";
      console.log(
        `[${vp.tag}:${vp.width}] ${p.name}: ${flag} scrollW=${m.scrollW} clientW=${m.clientW}`
      );
      if (m.offenders.length) console.log("   offenders: " + m.offenders.join(" | "));
      await page.screenshot({ path: path.join(OUT, `${p.name}_${vp.tag}.png`), fullPage: vp.tag === "mobile" ? false : true });
    }
    await ctx.close();
  }
  await browser.close();
  console.log("DONE shots -> " + OUT);
})();
