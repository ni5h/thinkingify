# Bookaroo — an independent Thinkingify product

Neo's product. A standalone Angular 20 app that mirrors the main Thinkingify
stack and design system, built so a 9-year-old can **design** it (deciding what
to build and how it should feel) while Claude handles the **coding**.

It's a real product environment on purpose — same Angular version, same Tailwind
tokens, same fonts as `ui/` — so Neo learns the real thing, and so it can ship on
its own later with no rewrite (see the [architecture review](../)).

- **Kid-facing guide:** [`NEO-PRODUCT-WORKBOOK.md`](./NEO-PRODUCT-WORKBOOK.md) — the product-designer workbook.
- **This file:** grown-up setup, run, and deploy notes.

## Run it

```bash
cd bookaroo
npm install      # first time only
npm start        # serves at http://localhost:4200
npm run build    # production build → dist/bookaroo
```

Requires Node 20+. No backend, no database, no accounts yet — all data lives in
`src/app/core/books.service.ts` for now.

## How it's built

A deliberately small, real Angular app — standalone components, signals, lazy
routes, the Thinkingify design tokens:

```
bookaroo/
  src/app/
    app.component.ts          # the frame: header + footer + <router-outlet>
    app.routes.ts             # one route today (home); add screens here
    core/
      book.model.ts           # the shape of a Book
      books.service.ts        # holds the books (signal) + add(); starter data
    features/home/
      home.component.ts       # the home screen: hero + add-a-book form + shelf
  tailwind.config.js          # shared Thinkingify palette + the book 'spine' accent
```

Everything a kid edits is commented in plain language. Data access is behind
`BooksService` so swapping the in-memory list for a real backend later touches
one file, not the screens.

## How Neo and Claude work together

Neo is the product designer; Claude is the builder. Neo describes a change in
plain words ("each book should show Available or Swapped"), and Claude Code
implements it in this repo. The workbook teaches Neo how to frame those asks.

## Deploy later (grown-up, not needed yet)

Independently deployable, per the architecture review:

1. Build: `npm run build` → static files in `dist/bookaroo`.
2. Create a **Cloudflare Pages** project (build command `npm run build`, output
   `dist/bookaroo`), or split `bookaroo/` into its own repo first.
3. Add a custom domain such as `bookaroo.thinkingify.com` (DNS in the review).
   TLS is automatic.

No shared backend, no Supabase, no SSO is wired in yet — those switch on only
when Neo's experiment grows into something other kids will use.
