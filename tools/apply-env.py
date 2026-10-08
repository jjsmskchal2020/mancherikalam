#!/usr/bin/env python3
"""Fill the shop's contact details into the site from environment variables.

The pages carry visible tokens such as [BB_PHONE] in place of every contact
detail. This script replaces each token with the value of the environment
variable of the same name, so the phone number, address, hours and licence
numbers can be changed in GitHub (Settings > Secrets and variables > Actions >
Variables) without touching any HTML. It runs during the deploy, on the staged
copy of the site - the source files keep their tokens.

    python tools/apply-env.py _site           fill an already-staged folder (CI)
    python tools/apply-env.py --out _preview  copy the site to _preview, then fill it

Values come from the real environment first, then from a local .env file at
the repository root (see site.env.example). A variable that is unset or empty
leaves its token in place; main.js then shows the matching button as
"not added yet" instead of a dead link, so a half-filled site never breaks.

Standard library only.
"""

import html
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

VARIABLES = [
    "BB_PHONE",
    "BB_WHATSAPP",
    "BB_STREET_ADDRESS",
    "BB_PINCODE",
    "BB_HOURS_MON_SAT",
    "BB_HOURS_SUN",
    "BB_LATITUDE",
    "BB_LONGITUDE",
    "BB_MAPS_LINK",
    "BB_MAPS_EMBED",
    "BB_GSTIN",
    "BB_FSSAI",
    "BB_FACEBOOK_URL",
    "BB_WHATSAPP_GROUP",
]

HOURS = ["BB_HOURS_MON_SAT", "BB_HOURS_SUN"]

# Never copied into a local preview: repository plumbing, not site files.
# Mirrors the rsync excludes in .github/workflows/deploy.yml.
SKIP = {".git", ".github", "_site", "_preview", "tools", "README.md",
        "CNAME.example", ".gitignore", ".gitattributes", ".env",
        "site.env.example", "__pycache__"}

TOKEN = re.compile(r"\[(BB_[A-Z_]+)\]")
SCRIPT = re.compile(r"(<script\b[^>]*>)(.*?)(</script>)", re.S | re.I)
TIME = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def read_dotenv():
    path = os.path.join(ROOT, ".env")
    values = {}
    if not os.path.exists(path):
        return values

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key.strip()] = value
    return values


def twelve_hour(hhmm):
    hour, minute = (int(part) for part in hhmm.split(":"))
    suffix = "am" if hour < 12 else "pm"
    return "%d:%02d %s" % (hour % 12 or 12, minute, suffix)


def expand_hours(name, raw, values, warnings):
    """08:30-20:00 -> display text plus 24-hour opens/closes for JSON-LD."""
    text = raw.strip()

    if text.lower() == "closed":
        values[name] = "Closed"
        # schema.org's convention for "closed all day".
        values[name + "_OPENS"] = "00:00"
        values[name + "_CLOSES"] = "00:00"
        return

    parts = [part.strip() for part in re.split(r"\s*[-–]\s*", text)]
    if len(parts) == 2 and all(TIME.match(part) for part in parts):
        opens, closes = ("%02d:%s" % (int(p.split(":")[0]), p.split(":")[1]) for p in parts)
        values[name] = "%s – %s" % (twelve_hour(opens), twelve_hour(closes))
        values[name + "_OPENS"] = opens
        values[name + "_CLOSES"] = closes
        return

    # Not in the expected shape: show it as written, but leave the structured
    # data unfilled rather than publish times Google would misread.
    values[name] = text
    warnings.append("%s=%r is not HH:MM-HH:MM or 'closed'; shown as written, "
                    "opening hours left out of the structured data" % (name, raw))


def collect():
    dotenv = read_dotenv()
    values, warnings = {}, []

    for name in VARIABLES:
        value = os.environ.get(name) or dotenv.get(name) or ""
        value = value.strip()
        if not value:
            continue

        if name == "BB_WHATSAPP":
            digits = re.sub(r"\D", "", value)
            # main.js adds the 91 country code itself.
            if len(digits) == 12 and digits.startswith("91"):
                digits = digits[2:]
            if len(digits) != 10:
                warnings.append("BB_WHATSAPP should be a 10-digit mobile number; "
                                "got %r" % value)
            value = digits

        if name in HOURS:
            expand_hours(name, value, values, warnings)
            continue

        values[name] = value

    return values, warnings


def fill(text, values, counts):
    def replace(match, in_script):
        name = match.group(1)
        if name not in values:
            return match.group(0)
        counts[name] = counts.get(name, 0) + 1
        value = values[name]
        if in_script:
            # Tokens in scripts always sit inside a JSON / JS string literal.
            return json.dumps(value, ensure_ascii=False)[1:-1].replace("</", "<\\/")
        return html.escape(value, quote=True)

    out, last = [], 0
    for block in SCRIPT.finditer(text):
        out.append(TOKEN.sub(lambda m: replace(m, False), text[last:block.start()]))
        out.append(block.group(1))
        out.append(TOKEN.sub(lambda m: replace(m, True), block.group(2)))
        out.append(block.group(3))
        last = block.end()
    out.append(TOKEN.sub(lambda m: replace(m, False), text[last:]))
    return "".join(out)


def copy_site(target):
    # Empty the folder rather than deleting it: on Windows a folder that a
    # local preview server is serving from cannot itself be removed.
    if os.path.isdir(target):
        for name in os.listdir(target):
            path = os.path.join(target, name)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

    def ignore(folder, names):
        if os.path.abspath(folder) == ROOT:
            return [name for name in names if name in SKIP]
        return [name for name in names if name == "__pycache__"]

    shutil.copytree(ROOT, target, ignore=ignore, dirs_exist_ok=True)


def main(argv):
    if len(argv) == 2 and argv[0] == "--out":
        target = os.path.abspath(os.path.join(ROOT, argv[1]))
        if target == ROOT:
            sys.exit("Refusing to overwrite the source tree.")
        copy_site(target)
    elif len(argv) == 1 and not argv[0].startswith("--"):
        target = os.path.abspath(argv[0])
        if target == ROOT:
            sys.exit("Refusing to edit the source tree in place - pass a staged copy "
                     "such as _site, or use --out _preview.")
        if not os.path.isdir(target):
            sys.exit("No such folder: %s" % target)
    else:
        sys.exit(__doc__.strip())

    values, warnings = collect()
    counts, left = {}, set()

    for folder, _, files in os.walk(target):
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(folder, name)
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            updated = fill(text, values, counts)
            left.update(TOKEN.findall(updated))
            if updated != text:
                with open(path, "w", encoding="utf-8", newline="\n") as handle:
                    handle.write(updated)

    print("Filled %d token(s) in %s" % (sum(counts.values()), target))
    for name in sorted(counts):
        print("  ok    %-26s x%d" % (name, counts[name]))
    for name in sorted(left):
        print("  unset %s" % name)
    for warning in warnings:
        print("  warning: %s" % warning)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
