# Book Swap — Neo's starter project

A deliberately simple, **no-build** static website for Neo (age 9, new to
coding) to work on independently. Plain HTML, CSS and JavaScript — no
framework, no bundler, no `npm install`. Edit a file, refresh the browser,
see the change.

This is the kid-facing playground layer of the "book community" product from
the [platform architecture review](../). It is intentionally *not* the
Angular/Supabase stack — that would block a beginner. When Neo builds
something worth shipping, these same static files deploy as-is (see below),
so there's no rewrite to go from "Neo's experiment" to "a real page on a
subdomain."

## Files

| File | What it is | Who edits it |
|---|---|---|
| `index.html` | The page structure | Neo (rarely) |
| `books.js` | The list of books — **the main thing to edit** | Neo (often) |
| `app.js` | Renders the book list into cards | mostly leave alone |
| `styles.css` | Colors, fonts, layout | Neo (for fun) |
| `NEO-START-HERE.md` | Kid-friendly guide | — |

## Run it locally

Just **open `index.html` in a browser** (double-click it). There is no server
and no build step — `books.js` is loaded with a `<script>` tag, so it works
straight off the filesystem (`file://`), which keeps things frictionless for a
9-year-old.

## Deploy it later (grown-up step — not needed yet)

Because it's plain static files, it drops onto **Cloudflare Pages** with no
build:

1. (Optional) split `bookswap/` into its own `book-community-web` repo.
2. Create a Cloudflare Pages project from the repo.
   - **Build command:** *(leave empty)*
   - **Output directory:** `bookswap` (or the repo root if split out)
3. Add the custom domain `community.thinkingify.com` (see the architecture
   review for DNS). TLS is automatic.

No backend, no Supabase, no account system is wired in yet — that's all
deferred until Neo's experiment turns into something he wants other kids to
use. Keeping it this simple is the point.

## Design intent

- **Immediate feedback** — edit, refresh, done. No tooling between Neo and the
  result.
- **Hard to break badly** — the starter already works; he modifies rather than
  starts from blank, and `Ctrl`+`Z` always saves him.
- **Readable** — every file is commented in plain language aimed at a beginner.
- **Portable** — same files power the local playground and the eventual
  Cloudflare Pages deploy, matching the review's "no rewrite" migration path.
