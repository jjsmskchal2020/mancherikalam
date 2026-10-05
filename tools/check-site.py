#!/usr/bin/env python3
"""Structural checks for the Mancherikalam site. Standard library only.

    python tools/check-site.py

Catches the things that actually break this particular site:

  * root-absolute internal paths, which work at a domain root and silently
    break under a /subpath/ - the main hazard given the site has to run both
    on jakee4488.github.io/mancherikalam/ and later on its own domain
    (404.html is exempt; see the comment in that file)
  * relative links and assets that do not resolve to a file on disk
  * #fragment links with no matching id, and duplicate ids
  * unbalanced or unclosed tags
  * <img> missing alt, width or height (alt for screen readers, the
    dimensions to stop the page jumping about while images load)
  * Malayalam spans missing lang="ml"
  * JSON-LD that is not valid JSON, or that uses a schema.org type that
    does not exist
  * pages over the first-load byte budget

It also counts the [PLACEHOLDER] tokens still waiting to be filled in, which
is a progress report rather than a failure.

Exit code is 0 when every check passes, 1 otherwise.
"""

import json
import os
import re
import sys

from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

HTML_BUDGET = 60 * 1024          # generous; the pages sit far below this
EXEMPT_ROOT_ABSOLUTE = {"404.html"}

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}

# Types actually used by this site's structured data. Anything outside this
# set is almost certainly a typo or an invented type (WholesaleStore, say,
# which looks plausible but does not exist in the schema.org vocabulary).
SCHEMA_TYPES = {
    "Organization", "GroceryStore", "Store", "PostalAddress", "GeoCoordinates",
    "OpeningHoursSpecification", "Place", "AdministrativeArea",
}

EXTERNAL = ("http://", "https://", "mailto:", "tel:", "data:", "//")


class Page(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.stack = []
        self.ids = []
        self.links = []          # (attr, value, line)
        self.images = []         # (attrs dict, line)
        self.ml_spans = []       # (classes, lang, line)
        self.jsonld = []
        self.errors = []
        self.html_lang = None
        self._script_type = None
        self._script_buf = []

    # -- tags --

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        line = self.getpos()[0]

        if tag not in VOID:
            self.stack.append((tag, line))

        self._record(tag, attrs, line)

        if tag == "script":
            self._script_type = attrs.get("type", "")
            self._script_buf = []

    def handle_startendtag(self, tag, attrs):
        self._record(tag, dict(attrs), self.getpos()[0])

    def handle_endtag(self, tag):
        if tag in VOID:
            return

        if not self.stack:
            self.errors.append("line %d: stray </%s>" % (self.getpos()[0], tag))
            return

        if self.stack[-1][0] == tag:
            self.stack.pop()
            return

        for depth in range(len(self.stack) - 1, -1, -1):
            if self.stack[depth][0] == tag:
                unclosed = self.stack[depth + 1:]
                self.errors.append(
                    "line %d: </%s> closed while %s still open"
                    % (self.getpos()[0], tag,
                       ", ".join("<%s> from line %d" % (t, n) for t, n in unclosed))
                )
                del self.stack[depth:]
                return

        self.errors.append("line %d: </%s> never opened" % (self.getpos()[0], tag))

    def handle_data(self, data):
        if self._script_type == "application/ld+json":
            self._script_buf.append(data)

    def close(self):
        HTMLParser.close(self)
        for tag, line in self.stack:
            self.errors.append("<%s> opened on line %d is never closed" % (tag, line))

    # -- collection --

    def _record(self, tag, attrs, line):
        if tag == "html":
            self.html_lang = attrs.get("lang")

        if "id" in attrs:
            self.ids.append((attrs["id"], line))

        for name in ("href", "src"):
            if name in attrs:
                self.links.append((name, attrs[name], line))

        if tag == "img":
            self.images.append((attrs, line))

        if tag == "span" and "bi-ml" in (attrs.get("class") or "").split():
            self.ml_spans.append((attrs.get("lang"), line))

        if tag == "script" and attrs.get("type") == "application/ld+json":
            self._script_type = "application/ld+json"
            self._script_buf = []

    def handle_endtag_script(self):
        pass


def collect_jsonld(text):
    """Pull every JSON-LD block out with a regex.

    HTMLParser's CDATA handling makes capturing script bodies fiddly, and the
    blocks are easy to find directly.
    """
    return re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', text, re.S
    )


def walk_types(node, found):
    if isinstance(node, dict):
        value = node.get("@type")
        if isinstance(value, str):
            found.add(value)
        elif isinstance(value, list):
            found.update(v for v in value if isinstance(v, str))
        for child in node.values():
            walk_types(child, found)
    elif isinstance(node, list):
        for child in node:
            walk_types(child, found)


def resolves(page_path, target):
    """Does a relative href/src land on something that exists?"""
    base = os.path.dirname(os.path.join(ROOT, page_path))
    path = os.path.normpath(os.path.join(base, target.split("#")[0].split("?")[0]))

    if os.path.isdir(path):
        return os.path.exists(os.path.join(path, "index.html"))
    return os.path.exists(path)


def check(page_path):
    full = os.path.join(ROOT, page_path)
    with open(full, "r", encoding="utf-8") as handle:
        text = handle.read()

    size = os.path.getsize(full)
    problems = []
    placeholders = len(re.findall(r"\[[A-Z][^\]]*\]", text))

    parser = Page()
    parser.feed(text)
    parser.close()
    problems.extend(parser.errors)

    # -- ids --

    seen = {}
    for name, line in parser.ids:
        if name in seen:
            problems.append(
                "duplicate id=\"%s\" on lines %d and %d" % (name, seen[name], line)
            )
        seen[name] = line

    # -- links --

    for attr, value, line in parser.links:
        if not value or value.startswith(EXTERNAL):
            continue

        if "[" in value:
            continue                                   # unfilled placeholder

        if value.startswith("#"):
            if value[1:] and value[1:] not in seen:
                problems.append(
                    'line %d: %s="%s" has no matching id' % (line, attr, value)
                )
            continue

        if value.startswith("/"):
            if page_path not in EXEMPT_ROOT_ABSOLUTE:
                problems.append(
                    'line %d: %s="%s" is root-absolute and will break under a '
                    "/subpath/ deployment" % (line, attr, value)
                )
            continue

        if not resolves(page_path, value):
            problems.append('line %d: %s="%s" does not resolve' % (line, attr, value))

    # -- images --

    for attrs, line in parser.images:
        # alt="" is a decision, not an omission: it marks an image as
        # decorative so screen readers skip it, which is right for the brand
        # mark sitting next to the word "Mancherikalam". A missing alt
        # attribute is the actual bug.
        if "alt" not in attrs:
            problems.append("line %d: <img> has no alt attribute" % line)
        if "width" not in attrs or "height" not in attrs:
            problems.append(
                "line %d: <img> missing width/height, so the page will jump "
                "about as it loads" % line
            )

    # -- language --

    if not parser.html_lang:
        problems.append("<html> has no lang attribute")

    for lang, line in parser.ml_spans:
        if lang != "ml":
            problems.append('line %d: .bi-ml span is missing lang="ml"' % line)

    # -- structured data --

    blocks = collect_jsonld(text)
    for index, block in enumerate(blocks, 1):
        try:
            data = json.loads(block)
        except ValueError as error:
            problems.append("JSON-LD block %d is not valid JSON: %s" % (index, error))
            continue

        if "@context" not in data:
            problems.append("JSON-LD block %d has no @context" % index)

        found = set()
        walk_types(data, found)

        if not found:
            problems.append("JSON-LD block %d declares no @type" % index)

        for name in sorted(found - SCHEMA_TYPES):
            problems.append(
                "JSON-LD block %d uses @type \"%s\", which is not a schema.org "
                "type this site knows about" % (index, name)
            )

    if size > HTML_BUDGET:
        problems.append(
            "%d bytes is over the %d byte budget" % (size, HTML_BUDGET)
        )

    return problems, size, placeholders, len(blocks)


def main():
    pages = ["index.html", "supermarket/index.html", "big-bazaar/index.html",
             "404.html"]

    missing = [p for p in pages if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        sys.exit("Missing page(s): %s" % ", ".join(missing))

    failures = 0
    total_placeholders = 0

    print("Checking %d pages in %s\n" % (len(pages), ROOT))

    for page in pages:
        problems, size, placeholders, blocks = check(page)
        total_placeholders += placeholders

        status = "FAIL" if problems else "ok"
        print("%-4s %-24s %6d bytes  %d JSON-LD  %d placeholders"
              % (status, page, size, blocks, placeholders))

        for problem in problems:
            print("       - %s" % problem)
            failures += 1

    # Supporting files that are easy to forget when the domain changes.
    print("")
    for name in (".nojekyll", "robots.txt", "sitemap.xml",
                 "assets/css/styles.css", "assets/js/main.js"):
        exists = os.path.exists(os.path.join(ROOT, name))
        print("%-4s %s" % ("ok" if exists else "FAIL", name))
        if not exists:
            failures += 1

    print("\n%d problem(s). %d [PLACEHOLDER] token(s) still to fill in."
          % (failures, total_placeholders))

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
