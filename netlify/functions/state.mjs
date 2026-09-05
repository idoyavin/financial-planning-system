/**
 * The ledger's only door.
 *
 * The dashboard is a static page on a public URL, so the figures cannot live
 * beside it — anyone could fetch the file. They live in Netlify Blobs and
 * come out only through this function, and only for a Google account on the
 * allowlist. A sign-in button that merely hid the UI would leave the data one
 * curl away; this is the version that actually holds.
 *
 * GET  /api/config  → { clientId }        public: the OAuth client id is not a secret
 * GET  /api/state   → the ledger          requires a verified, allowlisted Google token
 * PUT  /api/state   → saves the ledger    same, plus a shape check
 */

import { getStore } from "@netlify/blobs";
import { createRemoteJWKSet, jwtVerify } from "jose";
import { readFile } from "node:fs/promises";

const GOOGLE_JWKS = createRemoteJWKSet(
  new URL("https://www.googleapis.com/oauth2/v3/certs"),
);
const GOOGLE_ISSUERS = ["accounts.google.com", "https://accounts.google.com"];

const STORE = "keva-ledger";
const KEY = "state";
const BACKUP_KEY = "state-previous";

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      // The figures are per-user and must never sit in a shared cache.
      "cache-control": "no-store, private",
    },
  });

function allowlist() {
  return (process.env.ALLOWED_EMAILS || "")
    .split(",")
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean);
}

/**
 * Verify a Google ID token and decide whether it may see the ledger.
 * Returns { email, allowed } or throws for a token that is not genuine.
 */
async function identify(request) {
  const header = request.headers.get("authorization") || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : null;
  if (!token) return null;

  const clientId = process.env.GOOGLE_CLIENT_ID;
  if (!clientId) throw new Error("GOOGLE_CLIENT_ID is not set");

  const { payload } = await jwtVerify(token, GOOGLE_JWKS, {
    issuer: GOOGLE_ISSUERS,
    audience: clientId,
  });

  // Google sets email_verified; an unverified address proves nothing about
  // who is holding the token.
  if (!payload.email || payload.email_verified !== true) return null;

  const email = String(payload.email).toLowerCase();
  return { email, name: payload.name || "", allowed: allowlist().includes(email) };
}

/** The committed data/state.json, used the first time before anything is saved. */
async function seed() {
  const raw = await readFile(new URL("../../data/state.json", import.meta.url), "utf-8");
  return JSON.parse(raw);
}

/** Reject a payload that would leave the ledger unusable. */
function validate(body) {
  if (!body || typeof body !== "object") return "not an object";
  if (!body.plan || typeof body.plan !== "object") return "missing plan";
  if (!Array.isArray(body.months) || body.months.length === 0) return "months must be a non-empty array";
  for (const m of body.months) {
    if (typeof m?.m !== "string" || !/^\d{4}-\d{2}$/.test(m.m)) return `bad month key: ${m?.m}`;
    for (const f of ["bank", "analyst", "blink", "crypto", "carRem", "insPot"]) {
      if (typeof m[f] !== "number" || !Number.isFinite(m[f])) return `${m.m}: ${f} must be a number`;
    }
    if (!m.spend || typeof m.spend !== "object") return `${m.m}: missing spend`;
  }
  if (!Array.isArray(body.tasks)) return "tasks must be an array";
  return null;
}

export default async (request) => {
  const path = new URL(request.url).pathname;

  if (path.endsWith("/config")) {
    return json({ clientId: process.env.GOOGLE_CLIENT_ID || null });
  }

  let who;
  try {
    who = await identify(request);
  } catch (err) {
    return json({ error: "invalid token", detail: String(err.message || err) }, 401);
  }
  if (!who) return json({ error: "sign in required" }, 401);

  // A signed-in stranger gets a truthful, empty answer — never a number.
  if (!who.allowed) {
    return json(
      {
        error: "no ledger for this account",
        email: who.email,
        hint: "This site holds one person's ledger. Your sign-in worked; there is simply nothing here for this account.",
      },
      403,
    );
  }

  const store = getStore(STORE);

  if (request.method === "GET") {
    let state = await store.get(KEY, { type: "json" });
    let source = "blobs";
    if (!state) {
      state = await seed();
      source = "seed";
    }
    return json({ state, source, email: who.email, name: who.name });
  }

  if (request.method === "PUT") {
    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "body is not JSON" }, 400);
    }
    const problem = validate(body);
    if (problem) return json({ error: `rejected: ${problem}` }, 400);

    // Keep the version we are replacing, so a bad save is recoverable.
    const current = await store.get(KEY, { type: "json" });
    if (current) await store.setJSON(BACKUP_KEY, current);

    body.updated = new Date().toISOString().slice(0, 10);
    await store.setJSON(KEY, body);
    return json({ ok: true, state: body });
  }

  return json({ error: "method not allowed" }, 405);
};

export const config = { path: ["/api/state", "/api/config"] };
