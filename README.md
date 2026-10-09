# MancherikalaM BigBazar — shop website

The website for **MancherikalaM BigBazar**, the family's wholesale and retail store in
Karukachal, Kottayam district, Kerala: rice by the sack, oils, flour, spices, frozen foods,
household and hygiene goods, for homes, caterers, hotels and events.

Plain HTML, CSS and vanilla JavaScript. No framework, no npm, no tracking, no cookies. The
only build step is filling the contact details in from environment variables at deploy time.

| Path | What it is |
|---|---|
| `index.html` | The whole site — one page, bilingual (English / മലയാളം) |
| `big-bazaar/index.html` | A redirect to the home page, so old links keep working |
| `404.html` | Self-contained "page not found" |
| `assets/` | Stylesheet, script, photos and icons |
| `tools/` | Python helpers — never served |

---

## Quick start

```sh
python -m http.server 8000
```

Then open <http://localhost:8000/>. Served like this, the contact buttons show
**"not added yet"** — the details come from environment variables (next section). To preview
with real values:

```sh
cp site.env.example .env          # then edit .env
python tools/apply-env.py --out _preview
python -m http.server 8000 -d _preview
```

Before committing a change:

```sh
python tools/check-site.py
```

---

## 1. Contact details — environment variables

Phone, WhatsApp, address, hours, map, GSTIN, FSSAI and the social links are **not written in
the HTML**. The page carries visible tokens such as `[BB_PHONE]`, and the deploy fills each one
from a GitHub repository variable of the same name.

### Changing a detail

1. On GitHub: **Settings ▸ Secrets and variables ▸ Actions ▸ Variables** tab.
2. **New repository variable** (or edit an existing one). Use exactly the names below.
3. **Actions ▸ Deploy to GitHub Pages ▸ Run workflow.** Changing a variable does not redeploy
   on its own.

| Variable | Format | Example |
|---|---|---|
| `BB_PHONE` | As you want it displayed | `+91 98765 43210` |
| `BB_WHATSAPP` | 10-digit mobile; `+91`, spaces and dashes are tidied | `9876543210` |
| `BB_STREET_ADDRESS` | Street line only — Karukachal, Kottayam, Kerala are added | `Main Road, near the junction` |
| `BB_PINCODE` | 6 digits | `686540` |
| `BB_HOURS_MON_SAT` | 24-hour `HH:MM-HH:MM`, or `closed` | `08:30-20:00` |
| `BB_HOURS_SUN` | Same | `closed` |
| `BB_LATITUDE`, `BB_LONGITUDE` | Right-click the shop in Google Maps; first menu item | `9.5077`, `76.6392` |
| `BB_MAPS_LINK` | Google Maps ▸ Share ▸ Send a link | `https://maps.app.goo.gl/…` |
| `BB_MAPS_EMBED` | Google Maps ▸ Share ▸ Embed a map ▸ only the `src="…"` URL | `https://www.google.com/maps/embed?pb=…` |
| `BB_GSTIN`, `BB_FSSAI` | As printed on the certificate | |
| `BB_FACEBOOK_URL`, `BB_WHATSAPP_GROUP` | Full URLs | |

The hours are written once and used twice: `08:30-20:00` shows as *8:30 am – 8:00 pm* in the
table and goes into the structured data for Google as `08:30` / `20:00`.

### What happens while something is unset

Its token stays on the page, and the matching WhatsApp / Call / Directions / map / social
button renders with a dashed outline and the words *"not added yet"*, with taps blocked — a
visible gap is better than a dead tap. It clears itself on the next deploy after the variable
is set. The deploy log lists which variables were filled and which are still unset.

**Set at least `BB_PHONE`, `BB_WHATSAPP` and the address before sharing the link publicly.**

### Why tokens instead of editing the HTML

Values are filled into the HTML itself at deploy time, not fetched by JavaScript, so search
engines and Google's business listing read the real address and hours. `apply-env.py` escapes
each value for where it lands — HTML-escaped in the page, JSON-escaped inside the structured
data and the `window.PAGE` script — so a URL with `&` in it works in both.

---

## 2. Photos

All photos are the shop's own, in `assets/img/`, as WebP. No staff or customers appear — photos
with people were left out or cropped.

| Files | Size | Used for |
|---|---|---|
| `hero-1..3.webp` | 540 × 720 | Hero mosaic |
| `sign.webp` | 650 × 284 | The lit sign, in About |
| `cat-*.webp` | 720 × 540 | The twelve product cards |
| `rice-1..4.webp`, `frozen-1..3.webp` | 480 × 480 | Rice wall and frozen foods sections |
| `frozen-sign.webp` | 720 × 205 | Frozen foods signboard |
| `gal-N.webp` / `gal-N-lg.webp` | 480 × 600 / 720 × 1280 | Gallery thumbnail / full size |
| `og-image.jpg` | 1200 × 630 | Social share image (must stay JPEG or PNG) |
| `favicon.svg`, `apple-touch-icon.png` | — | Browser tab and home-screen icons |

To swap a photo, export it at the same size and name, and keep the `width`/`height` attributes
in the HTML — they stop the page jumping while images load. Below-the-fold images are
`loading="lazy"`; the full-size gallery photos load only when tapped.

---

## 3. Typography — matching the signboard

The signboard sets **"MancherikalaM"** in a rounded geometric sans and **"BIGBAZAR"** in a heavy
geometric sans. The site uses the closest open fonts: **Quicksand 700** and **Montserrat 800**
(for headings too). Body text is Nunito Sans; Malayalam is Noto Sans Malayalam.

The wordmark is HTML and CSS, not an image — the golden arc and wheat sprig are inline SVG
(`#i-arc`, `#i-wheat` in the sprite at the top of `index.html`) — so it stays sharp at any size.
If the sign-maker can supply the exact font files, put them in `assets/fonts/`, add
`@font-face` rules at the top of `styles.css`, and point `--rounded` and `--display` at them.

---

## 4. Content to verify

- **Malayalam.** Translations are marked `<!-- TODO: verify Malayalam -->`. Read them aloud;
  most are literal and a natural shop-floor phrase is probably better. The prefilled WhatsApp
  greetings in `window.PAGE` at the bottom of `index.html` need checking too.
- **"Maccam"** in the frozen-foods brand list is spelled as on the signboard — confirm it.
- **Brand lists** on the product cards, rice wall and brand strip were read off the photos.
  Remove any you no longer stock. The site uses brand names only, no logos.
- **Pack sizes** — the rice note says 25, 30 and 50 kg sacks, as printed on the bags.
- **Delivery** is deliberately not mentioned. If the shop delivers, add it to the "For
  businesses" steps.

---

## 5. Deploy to GitHub Pages

This site lives **alongside** the existing portfolio at `jakee4488.github.io`, not inside it.
They are separate repositories and do not conflict:

| Repo | URL |
|---|---|
| `Jakee4488.github.io` | `https://jakee4488.github.io` — the portfolio, untouched |
| `mancherikalam` | `https://jakee4488.github.io/mancherikalam/` — this site |

1. Create a new **public** repository on GitHub named `mancherikalam`. Do not let GitHub add
   a README, licence or `.gitignore` — this folder already has them.
2. Push:
   ```sh
   git remote add origin https://github.com/Jakee4488/mancherikalam.git
   git push -u origin main
   ```
3. On GitHub: **Settings ▸ Pages ▸ Build and deployment**. Set *Source* to **GitHub
   Actions**. This matters: the workflow in `.github/workflows/deploy.yml` is what fills the
   contact details in. "Deploy from a branch" would publish the raw `[BB_...]` tokens.
4. Wait a minute, then open `https://jakee4488.github.io/mancherikalam/`.

`.nojekyll` is already present, which stops GitHub running Jekyll over the files.

---

## 6. Moving to a different address later

All internal links and asset paths are **relative**, so the pages work from a subfolder, from
a domain root, or from any other host without edits. The only absolute URLs are the ones that
have to be: canonical links, Open Graph tags, the JSON-LD identifiers, `sitemap.xml` and
`robots.txt`.

One command rewrites all of them:

```sh
python tools/set-domain.py https://yourdomain.in
```

| Where you are going | Command |
|---|---|
| GitHub Pages subpath (current) | `python tools/set-domain.py https://jakee4488.github.io/mancherikalam` |
| Custom domain on GitHub Pages | `python tools/set-domain.py https://yourdomain.in` |
| Netlify / Cloudflare Pages / a VPS | `python tools/set-domain.py https://yourdomain.in --no-cname` |
| Another host, under a subfolder | `python tools/set-domain.py https://example.com/shops --no-cname` |

It updates every canonical, `og:url`, `og:image`, `twitter:image`, JSON-LD
`url`/`@id`/`image`/`logo`, the `sitemap.xml` entry, the `Sitemap:` line in
`robots.txt`, and the root-absolute link in `404.html`. With a custom domain it also
writes `CNAME`; `--no-cname` removes it instead. The change is reversible — running it back
gives a byte-for-byte identical tree.

If you would rather not run the script, those are the only files to edit by hand.

### Why `CNAME.example` instead of `CNAME`

A `CNAME` file containing a domain that does not resolve **breaks the Pages deployment** —
GitHub tries to serve the site at that address and it fails. So the placeholder lives in
`CNAME.example` and is not active. `set-domain.py` writes the real `CNAME` when you give it a
real domain, or you can rename the file yourself.

---

## 7. DNS for a custom domain

At your registrar, for the apex domain (`yourdomain.in`, no `www`):

**A records** — four of them, all host `@`:

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

**AAAA records** — four of them, all host `@`:

```
2606:50c0:8000::153
2606:50c0:8001::153
2606:50c0:8002::153
2606:50c0:8003::153
```

**CNAME record** — host `www`, value:

```
jakee4488.github.io
```

(The GitHub user, with no repository name; add a trailing dot if your registrar wants one.)

Then:

1. `python tools/set-domain.py https://yourdomain.in`, commit and push.
2. GitHub **Settings ▸ Pages ▸ Custom domain**: enter the domain and save. GitHub checks the
   DNS, which takes anywhere from a few minutes to a day.
3. Once the check passes, tick **Enforce HTTPS**. The certificate is issued automatically and
   is free. If the box is greyed out, DNS has not propagated yet — wait and come back.

---

## 8. Editing the site

### Text

Visible copy is in `index.html`. Every bilingual string is a pair:

```html
<h2 class="bi">
  <span class="bi-en">Brands on our shelves</span>
  <span class="bi-ml" lang="ml">ഞങ്ങളുടെ ഷെൽഫുകളിലെ ബ്രാൻഡുകൾ</span>
</h2>
```

Edit **both** spans, keep English first in the markup, and keep `lang="ml"` on the Malayalam
one. The language toggle only reorders them visually.

### A product card

Copy one `<li>` inside `<ul class="photo-cards">`, then change the image, the alt text, the two
labels and the brand line. Twelve cards fill the grid evenly at 2, 3 and 4 columns.

### Brands

The rice wall, frozen foods and "Brands on our shelves" lists are plain `<li class="chip">`
items — add or delete lines.

### Colours

Tokens at the top of `assets/css/styles.css`. `--accent` (orange) is for text and buttons and
is contrast-checked; `--sign-wall` and `--sign-gold` are the sign's colours, used for the
header, hero and footer in both light and dark mode. Re-check contrast if you change
`--accent`, and update `<meta name="theme-color">`.

---

## 9. How it works

- **`data-lang="en|ml"`** on `<html>` selects which script leads. The toggle is pure CSS;
  JavaScript only flips the attribute and remembers the choice in `localStorage` (inside a
  `try/catch`). A three-line inline script applies it before first paint.
- **Contact links** (WhatsApp, Call, Directions, map) are built by `assets/js/main.js` from the
  `window.PAGE` object, so the prefilled WhatsApp message follows the reader's language.
- **The map is click-to-load**, so the page calls no third party until someone asks.
- **The gallery** is plain links to the full photos; `main.js` upgrades a tap to a `<dialog>`
  lightbox (Esc, the close button or a tap outside closes it).
- **Only one Malayalam font weight is loaded**, and `.bi-ml` is pinned to 400 so headings never
  make the browser synthesise a smeared fake bold.
- **`404.html` is self-contained** — GitHub Pages serves it from the site root whatever the
  URL, so it uses no stylesheet or images, and its one link is root-absolute.

---

## 10. Tools

Plain Python 3, standard library only. Nothing in `tools/` is served.

| Command | What it does |
|---|---|
| `python tools/check-site.py` | Structural checks — run before every commit (CI runs it too) |
| `python tools/apply-env.py _site` | Fill contact details into a staged copy (the deploy runs this) |
| `python tools/apply-env.py --out _preview` | Copy the site to `_preview/` and fill it from `.env` |
| `python tools/set-domain.py <url>` | Repoint the site at a new base URL |

`check-site.py` catches root-absolute paths, links and assets that do not resolve, `#anchors`
with no matching `id`, duplicate `id`s, unbalanced tags, `<img>` without `alt`/`width`/`height`,
Malayalam spans missing `lang="ml"`, invalid JSON-LD, and pages over budget. It also counts the
`[BB_...]` tokens — in the source these are expected; the deploy fills them.

---

## Licence

Content and photographs belong to the Mancherikalam family. The code is yours to do with as
you like.
