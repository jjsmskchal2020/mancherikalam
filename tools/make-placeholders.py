#!/usr/bin/env python3
"""Generate the placeholder artwork for the Mancherikalam shops site.

Every image in assets/img/ is produced by this script, so the placeholders are
reproducible and obviously temporary. Run it from anywhere:

    python tools/make-placeholders.py

SVGs (hero art, landing cards, wordmark, favicon) need nothing but the standard
library. The PNGs (Open Graph share images, apple-touch-icon) need Pillow; if
Pillow is missing the script skips them and tells you which files were not made.

NOTE ON MALAYALAM: Pillow only shapes complex scripts when it is built with
libraqm. This machine's Pillow reports raqm=False, so Malayalam text in a PNG
would render as broken, unjoined glyphs. The generated PNGs are therefore
English-label only. This does not affect the website itself, which renders
Malayalam with a real webfont in the browser.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(os.path.dirname(HERE), "assets", "img")

# Keep these in sync with the --accent tokens in assets/css/styles.css.
SHOPS = {
    "supermarket": {
        "label": "Supermarket",
        "accent": "#2f7d32",
        "accent_dark": "#1f5e24",
        "motif": "basket",
    },
    "big-bazaar": {
        "label": "Big Bazaar",
        "accent": "#b8470d",
        "accent_dark": "#8f3609",
        "motif": "crate",
    },
}
FAMILY_ACCENT = "#7a3b26"
PAPER = "#fbf7f0"


# ---- svg helpers ----

def write(name, text):
    path = os.path.join(IMG, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("  %-30s %6d bytes" % (name, len(text.encode("utf-8"))))


def motif(kind, accent):
    """Line-art shop motif, drawn on a 0 0 120 120 viewport."""
    if kind == "basket":
        # A shopping basket: trapezoid body, two handle arcs, weave lines.
        return (
            '<g fill="none" stroke="%s" stroke-width="3.5" '
            'stroke-linecap="round" stroke-linejoin="round" opacity=".85">'
            '<path d="M18 46h84l-9 46a8 8 0 0 1-8 6H35a8 8 0 0 1-8-6z"/>'
            '<path d="M44 46V32a16 16 0 0 1 32 0v14"/>'
            '<path d="M38 60l4 28M60 60v28M82 60l-4 28"/>'
            "</g>" % accent
        )
    # A stack of bulk crates/sacks for the wholesale shop.
    return (
        '<g fill="none" stroke="%s" stroke-width="3.5" '
        'stroke-linecap="round" stroke-linejoin="round" opacity=".85">'
        '<path d="M16 62h40v36H16zM64 62h40v36H64zM40 20h40v36H40z"/>'
        '<path d="M16 76h40M64 76h40M40 34h40"/>'
        "</g>" % accent
    )


def placeholder_svg(width, height, accent, accent_dark, kind, title, caption):
    """An intentionally plain, clearly-temporary image.

    Warm paper ground, a soft accent wash, diagonal awning stripes and a
    line-art motif. No gradients with many stops and no filters, so it stays a
    couple of kB and paints instantly on a cheap phone.
    """
    scale = min(width, height) / 220.0
    mx, my = width / 2.0, height / 2.0 - height * 0.06
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" \
width="{w}" height="{h}" role="img" aria-labelledby="t">
  <title id="t">{title}</title>
  <defs>
    <pattern id="stripe" width="22" height="22" patternUnits="userSpaceOnUse" \
patternTransform="rotate(45)">
      <rect width="22" height="22" fill="none"/>
      <rect width="11" height="22" fill="{accent}" opacity=".055"/>
    </pattern>
  </defs>
  <rect width="{w}" height="{h}" fill="{paper}"/>
  <rect width="{w}" height="{h}" fill="{accent}" opacity=".07"/>
  <rect width="{w}" height="{h}" fill="url(#stripe)"/>
  <rect x="6" y="6" width="{iw}" height="{ih}" fill="none" stroke="{accent}" \
stroke-width="2" stroke-dasharray="10 8" opacity=".38" rx="10"/>
  <g transform="translate({mx} {my}) scale({scale}) translate(-60 -60)">
    {motif}
  </g>
  <text x="{cx}" y="{ty}" text-anchor="middle" fill="{dark}" \
font-family="Nunito Sans, Segoe UI, Helvetica, Arial, sans-serif" \
font-size="{fs}" font-weight="700" letter-spacing=".5">{title}</text>
  <text x="{cx}" y="{cy}" text-anchor="middle" fill="{dark}" opacity=".7" \
font-family="Nunito Sans, Segoe UI, Helvetica, Arial, sans-serif" \
font-size="{cfs}" font-weight="600" letter-spacing="1.2">{caption}</text>
</svg>
""".format(
        w=width,
        h=height,
        iw=width - 12,
        ih=height - 12,
        paper=PAPER,
        accent=accent,
        dark=accent_dark,
        motif=motif(kind, accent),
        mx=round(mx, 1),
        my=round(my, 1),
        scale=round(scale, 3),
        cx=round(width / 2.0, 1),
        ty=round(height * 0.78, 1),
        cy=round(height * 0.86, 1),
        fs=round(min(width, height) * 0.075, 1),
        cfs=round(min(width, height) * 0.042, 1),
        title=title,
        caption=caption,
    )


def wordmark_svg():
    """The family mark: a tamarind-leaf sprig over the Mancherikalam name.

    Used in the sticky header at 28px, so it is drawn to read at that size.
    """
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" \
width="40" height="40" role="img" aria-label="Mancherikalam">
  <circle cx="20" cy="20" r="19" fill="{accent}"/>
  <g fill="none" stroke="{paper}" stroke-width="2.2" stroke-linecap="round" \
stroke-linejoin="round">
    <path d="M20 31V14"/>
    <path d="M20 19c-4.5 0-7.5-2.4-8.4-6 3.9-1.1 7.4.6 8.4 6z"/>
    <path d="M20 24c4.5 0 7.5-2.4 8.4-6-3.9-1.1-7.4.6-8.4 6z"/>
  </g>
</svg>
""".format(accent=FAMILY_ACCENT, paper=PAPER)


def favicon_svg():
    """A single 'M' on the family accent, legible at 16px in a browser tab."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" \
width="64" height="64" role="img" aria-label="Mancherikalam">
  <rect width="64" height="64" rx="14" fill="{accent}"/>
  <path d="M14 46V18h7l11 17 11-17h7v28h-7V31l-8 12h-6l-8-12v15z" \
fill="{paper}"/>
</svg>
""".format(accent=FAMILY_ACCENT, paper=PAPER)


def build_svgs():
    print("SVG placeholders:")
    write("logo-mancherikalam.svg", wordmark_svg())
    write("favicon.svg", favicon_svg())
    for slug, shop in SHOPS.items():
        write(
            "hero-%s.svg" % slug,
            placeholder_svg(
                1200, 675, shop["accent"], shop["accent_dark"], shop["motif"],
                shop["label"], "PLACEHOLDER PHOTO \u00b7 1200 \u00d7 675",
            ),
        )
        write(
            "card-%s.svg" % slug,
            placeholder_svg(
                800, 600, shop["accent"], shop["accent_dark"], shop["motif"],
                shop["label"], "PLACEHOLDER PHOTO \u00b7 800 \u00d7 600",
            ),
        )


# ---- png share images ----

FONT_CANDIDATES = [
    ("C:/Windows/Fonts/seguisb.ttf", "C:/Windows/Fonts/segoeui.ttf"),
    ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"),
    ("C:/Windows/Fonts/calibrib.ttf", "C:/Windows/Fonts/calibri.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ("/System/Library/Fonts/Helvetica.ttc",
     "/System/Library/Fonts/Helvetica.ttc"),
]


def pick_fonts():
    for bold, regular in FONT_CANDIDATES:
        if os.path.exists(bold) and os.path.exists(regular):
            return bold, regular
    return None, None


def rgb(hex_colour):
    hex_colour = hex_colour.lstrip("#")
    return tuple(int(hex_colour[i:i + 2], 16) for i in (0, 2, 4))


def centre_text(draw, box, text, font, fill):
    """Draw text centred in (x0, y0, x1, y1) using real glyph metrics."""
    x0, y0, x1, y1 = box
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    draw.text(
        (x0 + (x1 - x0 - (right - left)) / 2 - left,
         y0 + (y1 - y0 - (bottom - top)) / 2 - top),
        text, font=font, fill=fill,
    )


def build_pngs():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("\nPillow not installed - skipped the PNG share images:")
        print("  og-home.png, og-supermarket.png, og-big-bazaar.png,")
        print("  apple-touch-icon.png")
        print("  Install with:  python -m pip install Pillow")
        return False

    bold_path, regular_path = pick_fonts()
    if not bold_path:
        print("\nNo usable TTF found - skipped the PNG share images.")
        return False

    print("\nPNG share images (English labels only - see module docstring):")

    cards = [
        ("og-home.png", "Mancherikalam", "Two family shops in Karukachal",
         FAMILY_ACCENT),
        ("og-supermarket.png", "Mancherikalam Supermarket",
         "Groceries & household \u00b7 Karukachal, Kottayam", "#2f7d32"),
        ("og-big-bazaar.png", "Mancherikalam Big Bazaar",
         "Wholesale & bulk supply \u00b7 Karukachal, Kottayam", "#b8470d"),
    ]

    for name, title, subtitle, accent in cards:
        w, h = 1200, 630
        image = Image.new("RGB", (w, h), rgb(accent))
        draw = ImageDraw.Draw(image, "RGBA")

        # Soft concentric rings, bottom-right, to stop it reading as a flat slab.
        for radius in (520, 400, 280):
            draw.ellipse(
                (w - radius, h - radius, w + radius, h + radius),
                fill=(255, 255, 255, 12),
            )
        draw.rectangle((0, h - 12, w, h), fill=rgb(PAPER))

        # Shrink the title until it fits the safe width - shop names vary a lot.
        size = 86
        title_font = ImageFont.truetype(bold_path, size)
        while size > 40:
            box = draw.textbbox((0, 0), title, font=title_font)
            if box[2] - box[0] <= w - 220:
                break
            size -= 4
            title_font = ImageFont.truetype(bold_path, size)

        eyebrow_font = ImageFont.truetype(regular_path, 30)
        sub_font = ImageFont.truetype(regular_path, 38)
        note_font = ImageFont.truetype(regular_path, 24)

        centre_text(draw, (0, 170, w, 230), "MANCHERIKALAM", eyebrow_font,
                    (255, 255, 255, 190))
        centre_text(draw, (0, 250, w, 360), title, title_font,
                    (255, 255, 255, 255))
        centre_text(draw, (0, 380, w, 440), subtitle, sub_font,
                    (255, 255, 255, 220))
        centre_text(draw, (0, 500, w, 550),
                    "PLACEHOLDER \u2014 replace before sharing", note_font,
                    (255, 255, 255, 150))

        path = os.path.join(IMG, name)
        image.save(path, "PNG", optimize=True)
        print("  %-30s %6d bytes" % (name, os.path.getsize(path)))

    # apple-touch-icon: the favicon's M, rasterised at 180x180.
    icon = Image.new("RGB", (180, 180), rgb(FAMILY_ACCENT))
    draw = ImageDraw.Draw(icon)
    icon_font = ImageFont.truetype(bold_path, 112)
    centre_text(draw, (0, 0, 180, 180), "M", icon_font, rgb(PAPER))
    path = os.path.join(IMG, "apple-touch-icon.png")
    icon.save(path, "PNG", optimize=True)
    print("  %-30s %6d bytes" % ("apple-touch-icon.png",
                                 os.path.getsize(path)))
    return True


def main():
    if not os.path.isdir(IMG):
        os.makedirs(IMG)
    build_svgs()
    ok = build_pngs()
    print("\nWrote to %s" % IMG)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
