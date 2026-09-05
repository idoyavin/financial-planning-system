/**
 * Drive the real page in Chromium.
 *
 * Google sign-in cannot run headless, so the GIS script is intercepted and
 * replaced with a stub that fires the page's own callback. Everything after
 * that — the gate closing, the fetch to /api/state, every number on the
 * dashboard — is the real code path.
 */
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { chromium } from "playwright-core";

const ROOT = new URL("..", import.meta.url).pathname.replace(/\/$/, "");
const state = JSON.parse(await readFile(`${ROOT}/data/state.json`, "utf-8"));
let lastPut = null;

const server = createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  const send = (code, body, type = "application/json") => {
    res.writeHead(code, { "content-type": type });
    res.end(body);
  };
  if (url.pathname === "/api/config") return send(200, JSON.stringify({ clientId: "stub.apps.googleusercontent.com" }));
  if (url.pathname === "/api/state") {
    if (req.method === "PUT") {
      let body = "";
      for await (const c of req) body += c;
      lastPut = JSON.parse(body);
      return send(200, JSON.stringify({ ok: true, state: lastPut }));
    }
    if ((req.headers.authorization || "") !== "Bearer stub-token")
      return send(401, JSON.stringify({ error: "sign in required" }));
    return send(200, JSON.stringify({ state, source: "test", email: "idoyavin023@gmail.com", name: "Ido" }));
  }
  if (url.pathname === "/" || url.pathname === "/index.html")
    return send(200, await readFile(`${ROOT}/site/index.html`, "utf-8"), "text/html; charset=utf-8");
  send(404, "not found", "text/plain");
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const base = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
const page = await browser.newPage({ viewport: { width: 1180, height: 1000 } });

const errors = [];
page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
page.on("console", (m) => { if (m.type() === "error") errors.push("console: " + m.text()); });

// Google Fonts is unreachable from CI sandboxes; the page has real fallback
// stacks, so stub it out rather than let a blocked request read as a failure.
await page.route("https://fonts.googleapis.com/**", (route) =>
  route.fulfill({ status: 200, contentType: "text/css", body: "" }),
);

// Stand in for Google Identity Services.
await page.route("https://accounts.google.com/gsi/client", (route) =>
  route.fulfill({
    status: 200,
    contentType: "application/javascript",
    body: `window.google={accounts:{id:{
      initialize:function(o){window.__cb=o.callback;},
      renderButton:function(el){el.innerHTML='<button id="stub-signin">Sign in with Google</button>';},
      prompt:function(){}, disableAutoSelect:function(){}
    }}};`,
  }),
);

await page.goto(base, { waitUntil: "networkidle" });

const gateVisible = await page.locator("#gate").isVisible();
const appHiddenBefore = await page.locator("#app").isHidden();
console.log(`gate shown before sign-in: ${gateVisible}`);
console.log(`dashboard hidden before sign-in: ${appHiddenBefore}`);

await page.screenshot({ path: `${ROOT}/.shot-login.png` });

// Fire the page's own credential callback, exactly as Google would.
await page.evaluate(() => window.__cb({ credential: "stub-token" }));
await page.waitForSelector("#bar button", { timeout: 10000 });
await page.waitForTimeout(400);

const text = await page.locator("#app").innerText();
const checks = [
  ["net worth headline", "₪29,203"],
  ["projection", "₪606,015"],
  ["car remaining", "₪54,000"],
  ["payoff month corrected to April 2027", "April 2027"],
  ["satellite share", "7.2%"],
  ["core spending", "₪2,037"],
  ["insurance next bill", "₪309"],
  ["twelve-month insurance total", "₪8,946"],
  ["signed-in email shown", "idoyavin023@gmail.com"],
  ["Hebrew renders", "אנליסט"],
  ["tasks", "0 of 8 done"],
];
let bad = 0;
for (const [name, needle] of checks) {
  const ok = text.includes(needle);
  console.log(`${ok ? "  ok  " : "  FAIL"}  ${name} (${needle})`);
  if (!ok) bad++;
}

// account identifiers must not appear anywhere
for (const secret of ["256970", "1133", "76100059"]) {
  const leaked = text.includes(secret);
  console.log(`${leaked ? "  FAIL" : "  ok  "}  identifier ${secret} absent`);
  if (leaked) bad++;
}

await page.screenshot({ path: `${ROOT}/.shot-dashboard.png`, fullPage: true });

// Exercise a real save through the dialog.
await page.click("#logbtn");
await page.fill("#f-bank", "9400");
await page.click("button.primary[type=submit]");
await page.waitForTimeout(600);
const saved = lastPut && lastPut.months.some((m) => m.bank === 9400);
console.log(`${saved ? "  ok  " : "  FAIL"}  logging a month PUTs to the server`);
if (!saved) bad++;
const nowShows = (await page.locator("#app").innerText()).includes("2 months logged");
console.log(`${nowShows ? "  ok  " : "  FAIL"}  new month appears on the page`);
if (!nowShows) bad++;

await page.screenshot({ path: `${ROOT}/.shot-after-log.png`, fullPage: true });

if (errors.length) { console.log("\nJS errors:"); errors.forEach((e) => console.log("  " + e)); bad += errors.length; }
console.log(bad ? `\n${bad} PROBLEM(S)` : "\nbrowser check clean");

await browser.close();
server.close();
process.exit(bad ? 1 : 0);
