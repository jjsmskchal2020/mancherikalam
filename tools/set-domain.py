#!/usr/bin/env python3
"""Point the site at a different base URL.

The site itself uses relative paths everywhere, so moving between hosts or
between a subpath and a domain root needs no code changes. But a handful of
things are absolute by nature - canonical links, Open Graph URLs, the JSON-LD
identifiers, sitemap.xml and robots.txt - and this rewrites all of them in one
pass. It is a one-off maintenance command, not a build step: the site is served
exactly as it sits on disk.

    python tools/set-domain.py https://mancherikalam.in
    python tools/set-domain.py https://jakee4488.github.io/mancherikalam
    python tools/set-domain.py https://shops.example.com --no-cname

Moving to a custom domain on GitHub Pages also writes the CNAME file. Moving to
a host that does not use one (Netlify, Cloudflare Pages, a VPS) takes
--no-cname, which removes it instead.

Run it from anywhere; paths are resolved relative to the repository.
"""

import os
import re
import sys

try:
    from urllib.parse import urlparse
except ImportError:                                  # Python 2 fallback
    from urlparse import urlparse                    # type: ignore

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PAGES = ["index.html", "big-bazaar/index.html"]
PLAIN = ["sitemap.xml", "robots.txt"]
NOT_FOUND = "404.html"


def read(path):
    with open(os.path.join(ROOT, path), "r", encoding="utf-8") as handle:
        return handle.read()


def save(path, text):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def current_base():
    """Read the base the site is currently pointing at, from the canonical."""
    match = re.search(r'<link rel="canonical" href="([^"]+)"', read("index.html"))
    if not match:
        sys.exit("Could not find the canonical link in index.html - has it been edited?")
    return match.group(1).rstrip("/")


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    flags = set(a for a in argv if a.startswith("--"))

    unknown = flags - {"--no-cname"}
    if unknown:
        sys.exit("Unknown option(s): %s" % ", ".join(sorted(unknown)))

    if len(args) != 1:
        sys.exit(__doc__.strip())

    new_base = args[0].rstrip("/")
    parsed = urlparse(new_base)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        sys.exit("Give a full base URL, for example https://mancherikalam.in")

    old_base = current_base()
    if old_base == new_base:
        print("Already pointing at %s - nothing to do." % new_base)
        return 0

    old_path = urlparse(old_base).path.rstrip("/")
    new_path = parsed.path.rstrip("/")

    print("  from  %s" % old_base)
    print("    to  %s\n" % new_base)

    changed = 0

    # Absolute URLs: canonical, og:url, og:image, twitter:image, JSON-LD
    # @id/url/image/logo, sitemap <loc>, robots Sitemap:.
    for path in PAGES + PLAIN:
        text = read(path)
        if old_base not in text:
            continue
        hits = text.count(old_base)
        save(path, text.replace(old_base, new_base))
        print("  %-26s %d URL%s" % (path, hits, "" if hits == 1 else "s"))
        changed += 1

    # 404.html is the one file allowed root-absolute links, because GitHub
    # Pages serves it from the site root no matter how deep the bad URL was.
    text = read(NOT_FOUND)
    pattern = re.compile(r'href="%s/' % re.escape(old_path) if old_path else r'href="/')
    replacement = 'href="%s/' % new_path if new_path else 'href="/'
    updated, hits = pattern.subn(replacement, text)

    if hits:
        save(NOT_FOUND, updated)
        print("  %-26s %d link%s" % (NOT_FOUND, hits, "" if hits == 1 else "s"))
        changed += 1

    # CNAME: GitHub Pages only, and only for a real custom domain.
    cname = os.path.join(ROOT, "CNAME")
    host = parsed.netloc

    if "--no-cname" in flags or host.endswith(".github.io"):
        if os.path.exists(cname):
            os.remove(cname)
            print("  %-26s removed" % "CNAME")
            changed += 1
    else:
        with open(cname, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(host + "\n")
        print("  %-26s %s" % ("CNAME", host))
        changed += 1

    if not changed:
        print("  nothing matched - check that index.html still has its canonical link")
        return 1

    print("\nDone. Run  python tools/check-site.py  to confirm nothing broke.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
