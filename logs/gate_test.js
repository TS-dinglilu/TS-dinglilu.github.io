// 密码守卫功能实测：遮罩出现 -> 错误密码拒绝 -> 正确密码通过 -> 刷新免输 -> 报告页直链也被拦
const path = require("path");
const { chromium } = require("playwright-core");

const ROOT = "D:/研二/github.auto/repo";
const url = (f) => "http://127.0.0.1:8899/" + f;

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    channel: "msedge",
  });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  // 1) 首次打开主页 -> 应出现遮罩
  await page.goto(url("index.html"), { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#wb-gate", { timeout: 8000 });
  console.log("[1] 遮罩出现 OK");

  // 2) 错误密码 -> 报错
  await page.fill("#wb-gate-pass", "1");
  await page.click("#wb-gate-btn");
  await page.waitForTimeout(300);
  const err = await page.textContent("#wb-gate-err");
  console.log("[2] 错误密码提示:", JSON.stringify(err.trim()), err.includes("不正确") ? "OK" : "FAIL");

  // 3) 正确密码 0 -> 遮罩消失，正文可见
  await page.fill("#wb-gate-pass", "0");
  await page.click("#wb-gate-btn");
  await page.waitForTimeout(300);
  const gateGone = (await page.$("#wb-gate")) === null;
  const vis = await page.evaluate(() => getComputedStyle(document.documentElement).visibility);
  const hasTitle = (await page.textContent("body")).includes("自动化系统");
  console.log("[3] 密码 0 通过:", gateGone && vis === "visible" && hasTitle ? "OK" : "FAIL",
    "(gateGone=%s vis=%s content=%s)", gateGone, vis, hasTitle);

  // 4) 刷新 -> 免输密码直接看
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(500);
  const gateAfterReload = (await page.$("#wb-gate")) !== null;
  console.log("[4] 刷新免输:", gateAfterReload ? "FAIL" : "OK");

  // 5) 报告页直链（新 context 模拟陌生访客）-> 也被拦
  const ctx2 = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const p2 = await ctx2.newPage();
  await p2.goto(url("byd-recruit/report_20260924.html"), { waitUntil: "domcontentloaded" });
  await p2.waitForSelector("#wb-gate", { timeout: 8000 });
  const bodyHidden = await p2.evaluate(() => {
    const el = [...document.querySelectorAll("h1")].find((h) => h.textContent.includes("比亚迪"));
    return el ? getComputedStyle(el).visibility === "hidden" : "no-h1";
  });
  console.log("[5] 报告页直链拦截+正文隐藏:", bodyHidden === true ? "OK" : "FAIL " + bodyHidden);

  await browser.close();
  console.log("DONE");
})().catch((e) => { console.error("TEST ERROR:", e.message); process.exit(1); });
