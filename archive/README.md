# Archive

Historical snapshots of gameplaylabs.org content, preserved from the Notion/super.so era.

**From this point forward, history lives in git.** Every edit to a page in this repo is a commit — use `git log --follow <file>` or the GitHub "History" button on any file to see what changed, when, and why. No separate archive page is needed.

## Contents

| File | What it is | Source |
|---|---|---|
| `2025-05-16-privacy-policy.md` | The superseded Privacy Policy. Notably says advertising IDs are **not** used for personalized advertising — the opposite of current practice. | Recovered from the raw (JavaScript-disabled) super.so response on 2026-07-13 |
| `2026-06-14-home.md` | Earlier home page copy, before the "See it, know it — real gameplay, no fake ads." rewrite. | Notion archive page |

## Why the 2025-05-16 policy matters

Until this migration, super.so served the **2025-05-16 version to any client that did not execute JavaScript** — which includes most review crawlers and ad-network verification bots. The live, JavaScript-rendered site showed the correct 2026-06-13 version. Crawlers therefore saw a policy that contradicted the app's actual data practices.

This is the suspected hidden cause of the AdMob rejection, and it is the reason the site was moved to fully static hosting: every page here is complete HTML with no JavaScript required.

## Original Notion archive

<https://app.notion.com/p/gamepl/Archrive-20260614-37f4e7166bb580cda61de5f33d5eaa7e>

Kept for reference only. Safe to leave behind once this repo is live.
