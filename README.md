# financial-planning-system

Keva Ledger — קבע, the standing order: the thing that runs every month whether
or not anyone is watching.

```
data/state.json          the ledger — one file, read by everything below
keva-ledger/             Python package: the arithmetic, under test
site/                    the dashboard, deployed to Netlify
netlify/functions/       the API that guards the data
tools/                   end-to-end checks
```

## The site

A static page plus one serverless function. The page holds no figures of its
own — it is served from a public URL, so it cannot. Everything arrives from
`/api/state`, which releases the ledger only to a verified Google account on
the allowlist and stores it in Netlify Blobs.

`data/state.json` is the seed and the way back. It is deliberately **outside**
`site/`: anything in the publish directory is world-readable.

### Deploying

1. **Create a Google OAuth client** — [console.cloud.google.com](https://console.cloud.google.com/apis/credentials)
   → *Create credentials* → *OAuth client ID* → *Web application*.
   Under **Authorised JavaScript origins** add your Netlify URL
   (`https://your-site.netlify.app`) and, if you use one, your custom domain.
   No redirect URI is needed — Google Identity Services posts the token back
   to the page. Copy the client ID.

2. **Point Netlify at this repo.** `netlify.toml` already sets the publish
   directory and bundles the seed with the function; there is nothing to
   configure by hand.

3. **Set two environment variables** in *Site configuration → Environment
   variables*:

   | Variable | Value |
   | --- | --- |
   | `GOOGLE_CLIENT_ID` | the client ID from step 1 |
   | `ALLOWED_EMAILS` | `idoyavin023@gmail.com` (comma-separated for more) |

   Redeploy after setting them — functions read env vars at deploy time.

Anyone may sign in. Only an address in `ALLOWED_EMAILS` is served the ledger;
everyone else gets a 403 that contains no figures at all. If you never set
`ALLOWED_EMAILS`, nobody is allowed in — the list is empty, not open.

### Using it

Sign in, and the page shows the current position. **Log a month** writes
through the function to Netlify Blobs, so a month logged on your phone is
there on your laptop. **Download backup** saves the current ledger as
`state.json` for committing over `data/state.json`.

If a save fails, the entry stays on screen and in the tab, and a banner offers
Retry — a dropped connection never costs you what you just typed.

## The Python package

```sh
cd keva-ledger
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
make test      # 47 tests
make summary   # headline figures in the terminal
make serve     # a local read-only dashboard on 127.0.0.1:8000
```

`make serve` is for working offline; the Netlify site is the one you browse.

## Checks

```sh
npm install
npm run check:api       # the function's guards, including forged tokens
npm run check:browser   # drives the real page in Chromium
```

`check:browser` stubs Google sign-in — it cannot run headless — but everything
after the callback is the real code path: the gate closing, the fetch, every
number, and a month logged through the dialog reaching the server.

## Two decisions worth knowing

**Transfers sit outside the spending target.** bit and PAYBOX payments leave
the card and come back within days — you front the table, friends settle up.
They inflate the statement without being consumption.

**The satellite cap is measured against invested capital, not net worth.**
Otherwise a fat bank balance quietly licenses a bigger speculative position,
which is exactly backwards.

Not financial advice. This is one person's own data, organised, with the
reasoning shown so it can be checked.
