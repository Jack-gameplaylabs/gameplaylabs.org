#!/usr/bin/env python3
"""
Build a browsable, offline copy of the site into ../_preview/ for eyeballing in a
browser (file:// links). Rewrites absolute hrefs to relative ones so navigation works
without a web server. This is a PREVIEW ONLY — production is Jekyll on GitHub Pages,
which serves the real absolute paths (/privacy-policy etc.).
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_preview as bp  # noqa: E402

ROOT = bp.ROOT
PREVIEW = os.path.join(ROOT, "_preview")

PAGES = {
    "/": "index.html",
    "/terms-of-service": "terms-of-service.html",
    "/privacy-policy": "privacy-policy.html",
    "/community-guideline": "community-guideline.html",
    "/faq": "faq.html",
    "/contact": "contact.html",
    "/mission": "mission.html",
    "/team": "team.html",
    "/value": "value.html",
    "/support-reporting": "support-reporting.html",
    "/dmca": "dmca.html",
    "/delete-account": "delete-account.html",
}

BANNER = (
    '<div style="background:#5eead4;color:#0d0f14;padding:10px 16px;'
    'font:500 13px/1.5 -apple-system,sans-serif;text-align:center">'
    'LOCAL PREVIEW — links are rewritten for offline browsing. '
    'Live URLs will be gameplaylabs.org/privacy-policy etc.</div>'
)


def main():
    site, built = bp.build()

    if os.path.isdir(PREVIEW):
        shutil.rmtree(PREVIEW, ignore_errors=True)
    os.makedirs(PREVIEW, exist_ok=True)

    for path, filename in PAGES.items():
        key = path if path == "/" else path + "/"
        html = built.get(key)
        if html is None:
            print(f"  MISSING {path}")
            continue

        # rewrite absolute internal links -> flat local filenames
        for p, f in sorted(PAGES.items(), key=lambda kv: -len(kv[0])):
            html = html.replace(f'href="{p}"', f'href="{f}"')
        html = html.replace('href="/"', 'href="index.html"')
        html = html.replace('src="/assets/', 'src="assets/')
        html = re.sub(r'<link rel="canonical"[^>]*>', "", html)
        html = html.replace("<body>", "<body>" + BANNER, 1)

        with open(os.path.join(PREVIEW, filename), "w") as fh:
            fh.write(html)
        print(f"  {filename}")

    shutil.copy(os.path.join(ROOT, "app-ads.txt"), os.path.join(PREVIEW, "app-ads.txt"))
    src_assets = os.path.join(ROOT, "assets")
    if os.path.isdir(src_assets):
        shutil.copytree(src_assets, os.path.join(PREVIEW, "assets"), dirs_exist_ok=True)
    print("\nOpen _preview/index.html in a browser.")


if __name__ == "__main__":
    main()
