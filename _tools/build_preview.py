#!/usr/bin/env python3
"""
Local preview builder + pre-flight check for gameplaylabs.org.

This is NOT the production build — GitHub Pages runs Jekyll. This script renders a
close-enough local preview so you can eyeball the site, and it runs the checks that
actually matter before a DNS cutover:

  1. every legacy URL path still exists (store/app links must not 404)
  2. no page ships JavaScript (this is what broke us on super.so)
  3. the CURRENT policy text is present and the SUPERSEDED text is not
  4. app-ads.txt still has a placeholder publisher ID (blocks cutover)

Usage:
    python3 _tools/build_preview.py            # build + check
    python3 _tools/build_preview.py --serve    # ...then serve on :8000
"""
import os
import re
import sys
import shutil
import datetime

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("OUT") or os.path.join(ROOT, "_site")

# Paths that are baked into the app + the Play Store listing. Breaking one is a
# store policy violation, so they are asserted, not assumed.
LEGACY_PATHS = [
    "/",
    "/terms-of-service",
    "/privacy-policy",
    "/community-guideline",
    "/faq",
    "/contact",
    # These four are linked from the old home page and were missed by the first
    # inventory — the rebuilt site 404'd on all of them. Asserted so it cannot recur.
    "/mission",
    "/team",
    "/value",
    "/support-reporting",
]
NEW_PATHS = ["/dmca", "/delete-account"]

# Every asset the pages reference must actually exist in assets/.
REQUIRED_ASSETS = [
    "logo.png",
    "hero-cover.webp",
    "google-play-badge.png",
    "app-screenshot-1.png",
    "app-screenshot-2.png",
]

CURRENT_POLICY_DATE = "June 13th 2026"
SUPERSEDED_MARKERS = [
    "May. 16th 2025",
    "we do not use these for personalized advertising",
    "Under no circumstances do we sell your personal information",
]


# ---------------------------------------------------------------- tiny liquid
def load_config():
    """Parse the flat/2-level YAML we actually use. No PyYAML dependency."""
    cfg, section = {}, None
    with open(os.path.join(ROOT, "_config.yml")) as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if not line.startswith(" ") and line.rstrip().endswith(":"):
                section = line.split(":")[0].strip()
                cfg[section] = {}
                continue
            if line.startswith("  ") and section and ":" in line:
                k, v = line.strip().split(":", 1)
                cfg[section][k.strip()] = v.strip().strip('"')
                continue
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                cfg[k.strip()] = v.strip().strip('"')
                section = None
    return cfg


def split_front_matter(text, path):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        raise SystemExit(f"FAIL {path}: front matter never closes")
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, text[end + 4:]


def render_liquid(text, site, page):
    """Handles exactly the subset of Liquid used in these templates."""
    ctx = {"site": site, "page": page}

    def lookup(expr):
        expr = expr.strip()
        if expr.startswith("'") or expr.startswith('"'):
            return expr.strip("'\"")
        cur = ctx
        for part in expr.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur

    # {% if page.x %}...{% else %}...{% endif %}
    def resolve_ifs(s):
        pattern = re.compile(r"\{%\s*if\s+([\w.]+)\s*%\}(.*?)\{%\s*endif\s*%\}", re.S)

        def one(m):
            body = m.group(2)
            parts = re.split(r"\{%\s*else\s*%\}", body, maxsplit=1)
            truthy, falsy = parts[0], (parts[1] if len(parts) > 1 else "")
            return truthy if lookup(m.group(1)) else falsy

        while pattern.search(s):
            s = pattern.sub(one, s)
        return s

    text = resolve_ifs(text)

    # {{ expr }} and {{ expr | filter }}
    def sub_var(m):
        expr = m.group(1).strip()
        if "|" in expr:
            base, filt = expr.split("|", 1)
            if "date" in filt:
                return str(datetime.date.today().year)
            expr = base.strip()
        val = lookup(expr)
        return "" if val is None else str(val)

    return re.sub(r"\{\{(.+?)\}\}", sub_var, text)


# ---------------------------------------------------------------- build
def build():
    site = load_config()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    layout = open(os.path.join(ROOT, "_layouts", "default.html")).read()
    built = {}

    for name in sorted(os.listdir(ROOT)):
        if not name.endswith(".md") or name == "README.md":
            continue
        fm, body = split_front_matter(open(os.path.join(ROOT, name)).read(), name)
        if not fm.get("layout"):
            continue

        slug = "" if name == "index.md" else name[:-3]
        url = "/" if not slug else f"/{slug}/"
        fm["url"] = url

        body_html = markdown.markdown(
            render_liquid(body, site, fm), extensions=["tables", "attr_list"]
        )

        # Shield the layout's {{ content }} from render_liquid — otherwise it resolves
        # to the (nonexistent) variable `content` and the whole page body is silently
        # replaced with an empty string. That is exactly the bug that produced eight
        # blank pages, so the sentinel is asserted below rather than trusted.
        SENTINEL = "@@PAGE_BODY@@"
        shielded = re.sub(r"\{\{\s*content\s*\}\}", SENTINEL, layout)
        if SENTINEL not in shielded:
            raise SystemExit("FAIL: _layouts/default.html has no {{ content }} placeholder")

        page_html = render_liquid(shielded, site, fm)
        if SENTINEL not in page_html:
            raise SystemExit(f"FAIL {name}: body placeholder lost during render")
        page_html = page_html.replace(SENTINEL, body_html)

        outdir = OUT if not slug else os.path.join(OUT, slug)
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "index.html"), "w") as f:
            f.write(page_html)
        built[url] = page_html

    for extra in ("app-ads.txt", "robots.txt", "CNAME"):
        src = os.path.join(ROOT, extra)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(OUT, extra))

    return site, built


# ---------------------------------------------------------------- checks
EXPECTED_TEXT = {
    "/": "See it in action",
    "/terms-of-service": "Repeat Infringer Policy",
    "/privacy-policy": "Advertising and Your Choices",
    "/community-guideline": "Prohibited Content and Behavior",
    "/faq": "How do I upload gameplay videos?",
    "/contact": "business@gameplaylabs.org",
    "/mission": "the true essence of play",
    "/team": "EA, Kakao, Nexon",
    "/value": "Fail Fast",
    "/support-reporting": "How to Write Your Email",
    "/dmca": "Designated Copyright Agent",
    "/delete-account": "Request deletion by email",
}

# The home page lost its cover image, both app screenshots and the Play badge in the
# first rebuild because nothing checked for them. Now they are checked.
EXPECTED_IMAGES = {
    "/": ["hero-cover.webp", "google-play-badge.png", "app-screenshot-1.png", "app-screenshot-2.png"],
}


def check(site, built):
    failures, warnings = [], []

    # A blank page passes every other check trivially — "no old policy text" is true of
    # an empty file. So prove the body is really there, and that it is the RIGHT body,
    # before anything else runs.
    for path, needle in EXPECTED_TEXT.items():
        key = path if path == "/" else path + "/"
        html = built.get(key)
        if html is None:
            continue
        m = re.search(r"<main>(.*?)</main>", html, re.S)
        inner = m.group(1) if m else ""
        text = re.sub(r"<[^>]+>", " ", inner)
        # /contact and /mission are genuinely one-liners in the source, so the floor is
        # low. The real guard is the per-page needle below.
        if len(text.split()) < 5:
            failures.append(f"{path} body is empty ({len(text.split())} words)")
        if needle not in inner:
            failures.append(f"{path} is missing expected content: {needle!r}")

    for path, imgs in EXPECTED_IMAGES.items():
        key = path if path == "/" else path + "/"
        html = built.get(key, "")
        for img in imgs:
            if img not in html:
                failures.append(f"{path} is missing image: {img}")

    for asset in REQUIRED_ASSETS:
        if not os.path.exists(os.path.join(ROOT, "assets", asset)):
            failures.append(f"assets/{asset} does not exist — a page references it")

    for path in LEGACY_PATHS + NEW_PATHS:
        key = path if path == "/" else path + "/"
        tag = "LEGACY" if path in LEGACY_PATHS else "new"
        if key not in built:
            failures.append(f"{tag} path missing: {path}")

    # no JavaScript, anywhere. this is the whole point of the migration.
    for url, html in built.items():
        if re.search(r"<script|onclick=|javascript:", html, re.I):
            failures.append(f"JavaScript found on {url} — crawlers must see full HTML")

    pp = built.get("/privacy-policy/", "")
    if CURRENT_POLICY_DATE not in pp:
        failures.append(f"/privacy-policy is missing the current date '{CURRENT_POLICY_DATE}'")
    for marker in SUPERSEDED_MARKERS:
        if marker in pp:
            failures.append(f"/privacy-policy still contains SUPERSEDED text: {marker!r}")

    for url, html in built.items():
        if "{{" in html or "{%" in html:
            failures.append(f"unrendered template tag left on {url}")

    ads = open(os.path.join(OUT, "app-ads.txt")).read()
    real = [l for l in ads.splitlines() if l.strip() and not l.startswith("#")]
    if not real:
        failures.append("app-ads.txt has no records")
    if "REPLACE_WITH_ADMOB_PUBLISHER_ID" in ads:
        warnings.append(
            "app-ads.txt still holds a PLACEHOLDER publisher ID — "
            "verification WILL fail. Replace before DNS cutover."
        )
    for line in real:
        if not re.match(r"^[\w.-]+,\s*pub-[\w-]+,\s*(DIRECT|RESELLER)(,\s*\w+)?$", line.strip()):
            warnings.append(f"app-ads.txt line does not match IAB format: {line.strip()!r}")

    return failures, warnings


if __name__ == "__main__":
    site, built = build()
    failures, warnings = check(site, built)

    print(f"\nBuilt {len(built)} pages → _site/\n")
    for url in sorted(built):
        print(f"  200  {url}")

    if warnings:
        print("\n⚠️  WARNINGS")
        for w in warnings:
            print(f"  · {w}")

    if failures:
        print("\n❌ FAILURES")
        for f_ in failures:
            print(f"  · {f_}")
        sys.exit(1)

    print("\n✅ All checks passed. No JavaScript. All legacy paths intact.\n")

    if "--serve" in sys.argv:
        import http.server, socketserver, functools
        os.chdir(OUT)
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=OUT)
        print("Serving http://localhost:8000 (Ctrl+C to stop)")
        socketserver.TCPServer(("", 8000), handler).serve_forever()
