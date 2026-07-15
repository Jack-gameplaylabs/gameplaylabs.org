#!/usr/bin/env python3
"""
Convert the Notion export into the Jekyll site — VERBATIM.

The first attempt at this migration re-typed the site from scraped text and silently
dropped four pages, five images and two whole sections. So this script does not
paraphrase anything: it copies the exported markdown body byte-for-byte, only
(a) stripping Notion's leading "# Title" line, since the layout renders the title,
(b) rewriting inter-page links to real site paths, and
(c) rewriting image paths to /assets/.

Anything it cannot map, it fails on. Silence is what caused the last bug.

Usage:  python3 _tools/import_from_notion.py <path-to-unzipped-export>
"""
import os
import re
import sys
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# Notion page title -> (output file, url slug, page title, has "Last updated" line)
PAGES = {
    "GenPlay":              ("index.md",               "/",                   "GenPlay",             False),
    "Mission":              ("mission.md",             "/mission",            "Mission",             False),
    "Team":                 ("team.md",                "/team",               "Team",                False),
    "Value":                ("value.md",               "/value",              "Value",               False),
    "Contact":              ("contact.md",             "/contact",            "Contact",             False),
    "Support & Reporting":  ("support-reporting.md",   "/support-reporting",  "Support & Reporting", False),
    "FAQ":                  ("faq.md",                 "/faq",                "FAQ",                 False),
    "Terms of Service":     ("terms-of-service.md",    "/terms-of-service",   "Terms of Service",    True),
    "Privacy Policy":       ("privacy-policy.md",      "/privacy-policy",     "Privacy Policy",      True),
    "Community Guideline":  ("community-guideline.md", "/community-guideline","Community Guideline", True),
}

IMAGES = {
    "GetItOnGooglePlay_Badge_Web_color_English.png": "google-play-badge.png",
    "KakaoTalk_Photo_2026-06-14-23-06-43_002.png":   "app-screenshot-1.png",
    "KakaoTalk_Photo_2026-06-14-23-06-45_003.png":   "app-screenshot-2.png",
}

DESCRIPTIONS = {
    "/": "GenPlay shows you authentic gameplay videos from real players, so you can find your next mobile game in seconds — then download it in a tap.",
    "/mission": "The Gameplay Labs mission.",
    "/team": "The team behind GenPlay.",
    "/value": "The values we build by.",
    "/contact": "Get in touch with Gameplay Labs.",
    "/support-reporting": "How to contact GenPlay support and report content that violates our Community Guidelines.",
    "/faq": "Frequently asked questions about GenPlay.",
    "/terms-of-service": "The terms governing your access to and use of the GenPlay mobile application and related services.",
    "/privacy-policy": "How GenPlay collects, uses, shares, and protects your personal information.",
    "/community-guideline": "The rules for sharing gameplay video content and interacting on GenPlay.",
}


def notion_title(path):
    """Notion filenames are '<Title> <32-hex-id>.md'."""
    base = os.path.basename(path)[:-3]
    return re.sub(r"\s+[0-9a-f]{32}$", "", base)


def find_pages(export_root):
    found = {}
    for dirpath, _dirnames, filenames in os.walk(export_root):
        for fn in filenames:
            if fn.endswith(".md"):
                p = os.path.join(dirpath, fn)
                found[notion_title(p)] = p
    return found


def convert(body, title):
    # 1. drop Notion's own "# Title" heading — the layout prints the title
    body = re.sub(r"^#\s+" + re.escape(title) + r"\s*\n+", "", body, count=1)

    # 2. images -> /assets/
    def img(m):
        alt, src = m.group(1), m.group(2)
        fn = os.path.basename(src).replace("%20", "_").replace(" ", "_")
        if fn not in IMAGES:
            raise SystemExit(f"FAIL: unmapped image {fn!r} in {title!r}")
        return f"![{alt}](/assets/{IMAGES[fn]})"

    body = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", img, body)

    # 3. inter-page links -> site paths. mailto/http links are left alone.
    def link(m):
        text, href = m.group(1), m.group(2)
        if href.startswith(("http", "mailto:", "/", "#")):
            return m.group(0)
        target = notion_title(href.replace("%20", " ").replace("%26", "&"))
        for ntitle, (_f, url, *_r) in PAGES.items():
            if ntitle == target:
                return f"[{text}]({url})"
        raise SystemExit(f"FAIL: unmapped link {href!r} (target {target!r}) in {title!r}")

    body = re.sub(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)", link, body)

    # 4. Heading levels are left exactly as Notion exported them — matching the current
    #    live site is what matters here, not the one-h1-per-page convention.

    # 5. "**Last updated: June 13th 2026**" moves into front matter
    updated = None
    m = re.search(r"^\*\*Last updated:\s*([^*]+?)\s*\*\*\s*$", body, flags=re.M)
    if m:
        updated = m.group(1)
        body = body[:m.start()] + body[m.end():]

    return body.strip() + "\n", updated


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: import_from_notion.py <unzipped-export-dir>")
    export = sys.argv[1]

    found = find_pages(export)
    missing = [t for t in PAGES if t not in found]
    if missing:
        raise SystemExit(f"FAIL: export is missing pages: {missing}")

    os.makedirs(ASSETS, exist_ok=True)
    for dirpath, _d, filenames in os.walk(export):
        for fn in filenames:
            if fn in IMAGES:
                shutil.copy(os.path.join(dirpath, fn), os.path.join(ASSETS, IMAGES[fn]))
                print(f"  asset  {IMAGES[fn]}")

    for ntitle, (outfile, url, ptitle, _has_date) in PAGES.items():
        src = found[ntitle]
        body, updated = convert(open(src).read(), ntitle)

        fm = ["---", "layout: default"]
        if ptitle:
            fm.append(f"title: {ptitle}")
        if updated:
            fm.append(f"updated: {updated}")
        fm.append(f"description: {DESCRIPTIONS[url]}")
        fm.append("---\n")

        with open(os.path.join(ROOT, outfile), "w") as f:
            f.write("\n".join(fm) + "\n" + body)
        words = len(re.sub(r"[#*\[\]()!]", " ", body).split())
        print(f"  page   {url:22s} {words:5d} words  <- {os.path.basename(src)}")

    print("\nImported verbatim from the Notion export.")


if __name__ == "__main__":
    main()
