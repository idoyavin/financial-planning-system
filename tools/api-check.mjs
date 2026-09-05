/**
 * Exercise the API function's guards, without Google or Netlify in the loop.
 *
 * The point of these is the negative cases: the function must refuse a
 * missing token, a malformed one, and — the one that matters — a token that
 * carries all the right claims but was signed by somebody other than Google.
 *
 *   node tools/api-check.mjs
 */
import { readFile } from "node:fs/promises";

const ROOT = new URL("..", import.meta.url);
process.env.GOOGLE_CLIENT_ID = "test-client-id.apps.googleusercontent.com";
process.env.ALLOWED_EMAILS = "someone@example.com";

const handler = (await import(new URL("netlify/functions/state.mjs", ROOT))).default;
const call = (path, opts = {}) => handler(new Request("https://example.netlify.app" + path, opts));

let failures = 0;
const report = (ok, name, detail) => {
  console.log(`${ok ? "  ok  " : "  FAIL"}  ${name}${detail ? "  → " + detail : ""}`);
  if (!ok) failures++;
};

async function expect(name, res, status, needle) {
  const body = await res.clone().text();
  report(res.status === status && (!needle || body.includes(needle)), name, `${res.status} ${body.slice(0, 80)}`);
}

await expect("config exposes the client id", await call("/api/config"), 200, "test-client-id");
await expect("no token is refused", await call("/api/state"), 401, "sign in required");
await expect(
  "malformed token is refused",
  await call("/api/state", { headers: { authorization: "Bearer not.a.jwt" } }),
  401,
  "invalid token",
);

const { SignJWT, generateKeyPair } = await import("jose");
const { privateKey } = await generateKeyPair("RS256");
const forged = await new SignJWT({ email: "someone@example.com", email_verified: true })
  .setProtectedHeader({ alg: "RS256" })
  .setIssuer("https://accounts.google.com")
  .setAudience(process.env.GOOGLE_CLIENT_ID)
  .setExpirationTime("1h")
  .sign(privateKey);
await expect(
  "token with perfect claims but the wrong signer is refused",
  await call("/api/state", { headers: { authorization: "Bearer " + forged } }),
  401,
  "invalid token",
);

// The validator guards against a save that would leave the ledger unusable.
const source = await readFile(new URL("netlify/functions/state.mjs", ROOT), "utf-8");
const body = source.slice(source.indexOf("function validate")).split("\nexport default")[0];
const validate = new Function(`return ${body}`)();

const good = JSON.parse(await readFile(new URL("data/state.json", ROOT), "utf-8"));
const month = good.months[0];
for (const [name, payload, want] of [
  ["the committed state.json passes", good, null],
  ["empty months refused", { ...good, months: [] }, "non-empty"],
  ["unpadded month key refused", { ...good, months: [{ ...month, m: "2026-8" }] }, "bad month key"],
  ["non-numeric balance refused", { ...good, months: [{ ...month, bank: "lots" }] }, "bank must be a number"],
  ["missing plan refused", { months: good.months, tasks: [] }, "missing plan"],
  ["missing tasks refused", { plan: good.plan, months: good.months }, "tasks must be an array"],
]) {
  const got = validate(payload);
  report(want === null ? got === null : String(got).includes(want), name, String(got));
}

console.log(failures ? `\n${failures} FAILED` : "\nall guards hold");
process.exit(failures ? 1 : 0);
