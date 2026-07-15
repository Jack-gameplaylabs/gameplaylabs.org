# gameplaylabs.org

Static website for **Gameplay Labs LLC** (GenPlay). Jekyll on GitHub Pages — no build step, no server, no subscription.

Replaces the previous Notion + super.so setup.

---

## Why this exists

1. **`app-ads.txt` must be served as plain text from the domain root.** Since January 2025, AdMob requires app-ads.txt verification for new apps. super.so could not reliably serve a root text file — the likely cause of GenPlay's blocked app verification.
2. **Crawlers were being served a stale policy.** Without JavaScript, super.so returned the **2025-05-16** Privacy Policy, which says advertising IDs are *not* used for ads — the opposite of current practice. Review bots read without JavaScript. Every page here is complete HTML with zero JavaScript, so this class of bug is structurally impossible now.
3. **Cost** — super.so subscription cancelled; GitHub Pages is free.
4. **Freedom to add pages** — `/delete-account` and `/dmca` were awkward in super.so.

---

## Editing content

**All content is markdown.** You never need to touch HTML.

| Page | File |
|---|---|
| `/` | `index.md` |
| `/terms-of-service` | `terms-of-service.md` |
| `/privacy-policy` | `privacy-policy.md` |
| `/community-guideline` | `community-guideline.md` |
| `/faq` | `faq.md` |
| `/contact` | `contact.md` |
| `/dmca` | `dmca.md` |
| `/delete-account` | `delete-account.md` |
| `/app-ads.txt` | `app-ads.txt` |

Two ways to edit:

- **On github.com** — open the file, click the pencil, edit the text, commit. The site rebuilds and deploys in ~1 minute.
- **Ask Claude** — "update the privacy policy to say X" in the GenPlay project.

When you change a policy, bump the `updated:` line at the top of the file:

```yaml
---
layout: default
title: Privacy Policy
updated: June 13th 2026   # ← change this
---
```

Email addresses and the Play Store ID live in `_config.yml` — change them once there and every page updates.

**Do not rename or move the page files.** The filename determines the URL, and these URLs are embedded in the app and in the Play Store listing. A rename means a 404, which is a store policy violation.

---

## Deploying (one-time setup)

1. Create a GitHub repo (e.g. `gameplaylabs/website`) and push the contents of this folder to the `main` branch.
2. **Settings → Pages** → Source: **Deploy from a branch** → Branch: `main` / `(root)` → Save.
3. **Settings → Pages → Custom domain** → `gameplaylabs.org` → Save. (The `CNAME` file in this repo already declares it.)
4. At your DNS provider, point the apex domain at GitHub Pages:

   | Type | Name | Value |
   |---|---|---|
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | CNAME | `www` | `<org>.github.io` |

   (`apps.gameplaylabs.org` is a separate GitHub Pages site and is unaffected.)
5. Wait for the certificate, then tick **Enforce HTTPS**.

Note: `_config.yml` sets `permalink: pretty`, so `privacy-policy.md` is published at `/privacy-policy/`, and GitHub Pages redirects `/privacy-policy` → `/privacy-policy/` automatically. Existing links keep working.

---

## Before you flip DNS — checklist

- [x] **Real AdMob publisher ID in `app-ads.txt`** — done 2026-07-14 (`pub-4168186842451542`).
- [x] Deletion steps in `delete-account.md` — confirmed with the dev partner 2026-07-15 and corrected to the actual flow (Home → Settings → Delete Account → Delete; immediate hard delete, no grace period).
- [x] DMCA agent registration statement in `dmca.md` and `terms-of-service.md` §7.3 — confirmed accurate by Jack 2026-07-14.
- [ ] Flip DNS at a time when **no AdMob review or Appodeal application is in flight** — the site may be unreachable for a few hours.
- [ ] Verify on the staging URL (`<org>.github.io/<repo>/`) first — see below.

## After you flip DNS — same day

- [ ] `curl https://gameplaylabs.org/app-ads.txt` → plain text, `Content-Type: text/plain`.
- [ ] `curl -L https://gameplaylabs.org/privacy-policy` → contains **"June 13th 2026"** and **not** "May. 16th 2025".
- [ ] Every path returns 200: `/`, `/terms-of-service`, `/privacy-policy`, `/community-guideline`, `/faq`, `/contact`, `/dmca`, `/delete-account`.
- [ ] **Re-save the Play Store listing** (even with the same URL) to trigger a re-crawl. Crawler refresh can take up to a week.
- [ ] Request re-indexing in Google Search Console.
- [ ] Only then: cancel the super.so subscription.

One week later: check AdMob console for app-ads.txt recognition. If it passes → start the Appodeal track.

---

## Known content issues (deferred, on purpose)

These were found in the 2026-07-13 audit and **intentionally left as-is** — Jack's call is to fix them once the app is republished, so the copy matches shipped behaviour:

1. **Reporting feature described inconsistently.** `index.md` and `faq.md` say in-app reporting exists ("Tap the report button on any video"); `community-guideline.md` says "use the in-app reporting feature **when it is implemented in the future**." A UGC-app reviewer will read both. Pick one and make it true.
2. **Age rating mismatch.** Play listing is 12+; `terms-of-service.md` §2.1 requires 13+.
3. **Nocturne not covered.** These policies are GenPlay-only. Nocturne ships from the same company (`apps.gameplaylabs.org`). Either extend the scope to Gameplay Labs LLC generally, or add per-app sections.
4. **UK/EEA.** `privacy-policy.md` states the Service does not target the EEA or UK. Deferred for GenPlay; revisit before any UK launch (UK GDPR wording + a consent management platform).
5. **Video files are not physically deleted on account deletion** (confirmed by dev 2026-07-15). `user.delete()` hard-deletes DB records (CASCADE), but there is no hook that deletes the mp4 files from server disk — they become inaccessible but persist indefinitely. The in-app dialog says data "will be permanently deleted". Ask dev to add a file-deletion (or scheduled purge) hook before republish; then tighten the "Residual copies" wording in `delete-account.md`.

---

## History

Content history lives in **git** from now on — `git log --follow <file>`, or the "History" button on any file on github.com. Pre-migration snapshots are in [`archive/`](archive/).
