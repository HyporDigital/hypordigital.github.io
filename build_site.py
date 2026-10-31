"""Build hypordigital.com's pages from their YAML files.

    python build_site.py

The YAML files are the source. site.yaml holds what every page shares (header,
footer, business details) and each other .yaml holds one page. This script
only reads them; it never writes a YAML, so your edits always win.

Every page comes out self-contained (site.css is inlined). A page that changes
is moved to Legacy Versions/<stamp>/ before the new one is written. The script
also writes sitemap.xml and robots.txt.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from html import escape
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
LEGACY = "Legacy Versions"
STAMP = datetime.now().strftime("%Y-%m-%d_%H%M")

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600'
         '&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600&display=swap">')


def a(s) -> str:
    """Attribute value."""
    return escape(str(s), quote=True)


def link(label, href, cls="") -> str:
    ext = href.startswith("http")
    rel = ' rel="noopener" target="_blank"' if ext else ""
    arrow = '<span class="arrow" aria-hidden="true">→</span>' if "btn" in cls else ""
    return f'<a class="{cls}" href="{a(href)}"{rel}>{label}{arrow}</a>'


def buttons(items) -> str:
    out = []
    for it in items or []:
        label, href = it[0], it[1]
        kind = it[2] if len(it) > 2 else ""
        out.append(link(label, href, f"btn {kind}".strip()))
    return f'<div class="actions">{"".join(out)}</div>'


def paras(body) -> str:
    """A body is a list of paragraphs; a nested list becomes bullets."""
    out = []
    for item in body or []:
        if isinstance(item, list):
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in item) + "</ul>")
        else:
            out.append(f"<p>{item}</p>")
    return "".join(out)


def head_of(b) -> str:
    sid = f' id="{a(b["id"])}"' if b.get("id") else ""
    return sid


def band_head(b) -> str:
    intro = f'<p>{b["intro"]}</p>' if b.get("intro") else "<span></span>"
    return (f'<div class="band-head"><div><p class="kicker">{b["kicker"]}</p>'
            f'<h2>{b["title"]}</h2></div>{intro}</div>')


# ------------------------------------------------------------------ blocks
def hero(b, site):
    aside = ""
    if b.get("aside"):
        rows = "".join(f'<li><span class="n">{i:02d}</span>{x}</li>'
                       for i, x in enumerate(b["aside"]["items"], 1))
        aside = (f'<aside class="hero-aside"><p class="label">{b["aside"]["label"]}</p>'
                 f'<ul>{rows}</ul></aside>')
    return (f'<section class="hero"><div class="wrap hero-grid"><div>'
            f'<p class="kicker">{b["kicker"]}</p><h1>{b["title"]}</h1>'
            f'<p class="sub">{b["sub"]}</p>{buttons(b.get("actions"))}'
            f'<p class="meta">{b.get("meta", "")}</p></div>{aside}</div></section>')


def logos(b, site):
    names = "".join(f"<li>{escape(n)}</li>" for n in b["names"])
    return (f'<section class="logos" aria-label="{a(b["label"])}"><div class="wrap">'
            f'<p class="label">{b["label"]}</p><ul>{names}</ul></div></section>')


def work(b, site):
    cards = []
    for c in b["items"]:
        tags = "".join(f"<li>{escape(t)}</li>" for t in c.get("tags", []))
        result = (f'<div class="result"><span class="v">{escape(c["result"][0])}</span>'
                  f'<span class="k">{c["result"][1]}</span></div>') if c.get("result") else ""
        cards.append(f'<article class="work-card"><p class="cat">{c["category"]}</p>'
                     f'<h3>{escape(c["brand"])}</h3><p class="headline">{c["headline"]}</p>'
                     f'<p>{c["text"]}</p>{result}<ul class="tags">{tags}</ul></article>')
    note = f'<p class="note">{b["note"]}</p>' if b.get("note") else ""
    return (f'<section class="band"{head_of(b)}><div class="wrap">{band_head(b)}'
            f'<div class="work">{"".join(cards)}</div>{note}</div></section>')


def systems(b, site):
    items = "".join(
        f'<article class="system"><h3>{s["title"]}</h3><p>{s["text"]}</p>'
        + (f'<p class="eg">{s["example"]}</p>' if s.get("example") else "")
        + "</article>"
        for s in b["items"])
    return (f'<section class="band systems-band"{head_of(b)}><div class="wrap">{band_head(b)}'
            f'<div class="systems">{items}</div></div></section>')


def figures(items, site):
    cells = "".join(f'<div class="figure"><div class="v">{escape(str(v))}</div>'
                    f'<div class="k">{k}</div></div>' for v, k in items)
    return f'<section aria-label="Results at a glance" class="figures-band"><div class="wrap"><div class="figures">{cells}</div></div></section>'


def services(b, site):
    items = "".join(
        f'<article class="service"><div class="n">{i:02d}</div><h3>{s["title"]}</h3>'
        f'<p>{s["text"]}</p><ul class="tags">'
        + "".join(f"<li>{escape(t)}</li>" for t in s.get("tags", []))
        + "</ul></article>"
        for i, s in enumerate(b["items"], 1))
    return (f'<section class="band"{head_of(b)}><div class="wrap">{band_head(b)}'
            f'<div class="services">{items}</div></div></section>')


def cases(b, site):
    items = "".join(
        f'<article class="case"><div class="who">{c["who"]}<span>{c.get("detail", "")}</span></div>'
        f'<div><h3>{c["title"]}</h3><ul>'
        + "".join(f"<li>{p}</li>" for p in c["points"])
        + "</ul></div></article>"
        for c in b["items"])
    note = f'<p class="note">{b["note"]}</p>' if b.get("note") else ""
    return (f'<section class="band"{head_of(b)}><div class="wrap">{band_head(b)}'
            f'<div class="cases">{items}</div>{note}</div></section>')


def steps(b, site):
    items = "".join(
        f'<article class="step"><div class="n">{i:02d}</div><h3>{s["title"]}</h3><p>{s["text"]}</p></article>'
        for i, s in enumerate(b["items"], 1))
    note = f'<p class="note">{b["note"]}</p>' if b.get("note") else ""
    return (f'<section class="band"{head_of(b)}><div class="wrap">{band_head(b)}'
            f'<div class="steps">{items}</div>{note}</div></section>')


def about(b, site):
    copy = "".join(f"<p>{p}</p>" for p in b["copy"])
    facts = "".join(f'<li><span class="k">{escape(k)}</span><span class="v">{escape(str(v))}</span></li>'
                    for k, v in b.get("facts", []))
    return (f'<section class="band"{head_of(b)}><div class="wrap">'
            f'<div class="band-head"><div><p class="kicker">{b["kicker"]}</p><h2>{b["title"]}</h2></div><span></span></div>'
            f'<div class="about"><div class="copy">{copy}</div><ul class="facts">{facts}</ul></div>'
            f'</div></section>')


def cta(b, site):
    return (f'<section class="cta"{head_of(b)}><div class="wrap"><h2>{b["title"]}</h2>'
            f'<p>{b["text"]}</p>{buttons(b.get("actions"))}</div></section>')


BLOCKS = {"hero": hero, "logos": logos, "figures": figures, "services": services,
          "work": work, "systems": systems, "cases": cases, "steps": steps, "about": about,
          "cta": cta}


def doc_body(pg) -> str:
    """A long-form page: privacy policy, app page."""
    date = f'<p class="date">Last updated {pg["updated"]}</p>' if pg.get("updated") else ""
    secs = "".join(f'<section><h2>{s["title"]}</h2><div class="body">{paras(s["body"])}</div></section>'
                   for s in pg["sections"])
    return (f'<main class="doc"><div class="wrap"><header><h1>{pg["heading"]}</h1>'
            f'<p class="lede">{pg["lede"]}</p>{date}</header>{secs}</div></main>')


# ------------------------------------------------------------------ chrome
def header(site) -> str:
    nav = "".join(link(t, h) for t, h in site["header"]["nav"])
    label, href = site["header"]["cta"]
    return (f'<header class="top"><div class="wrap">'
            f'<a class="brand" href="index.html" aria-label="{a(site["name"])} home">'
            f'<img src="{a(site["logo"])}" alt="" width="30" height="30"><span>{escape(site["name"])}</span></a>'
            f'<nav aria-label="Main">{nav}{link(label, href, "btn primary small")}</nav>'
            f'</div></header>')


def footer(site) -> str:
    links = "".join(link(t, h) for t, h in site["footer"]["links"])
    return (f'<footer class="foot"><div class="wrap"><span>{site["footer"]["line"]}</span>'
            f'<span class="links">{links}</span></div></footer>')


def schema(site, pg) -> str:
    url = site["url"]
    data = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": site["name"],
        "url": url + "/",
        "logo": f'{url}/{site["logo"]}',
        "image": f'{url}/{site["og_image"]}',
        "email": site["email"],
        "description": " ".join(pg["description"].split()),
        "address": {"@type": "PostalAddress", "addressLocality": site["locality"],
                    "addressRegion": site["region"], "addressCountry": site["country"]},
        "areaServed": {"@type": "Country", "name": "United States"},
        "founder": {"@type": "Person", "name": site["founder"], "sameAs": [site["linkedin"]]},
        "sameAs": [site["linkedin"]],
        "knowsAbout": site["services_offered"],
    }
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def page(site, pg, css) -> str:
    url = site["url"]
    path = "" if pg["file"] == "index.html" else pg["file"]
    canonical = f"{url}/{path}"
    desc = " ".join(pg["description"].split())
    body = ("".join(BLOCKS[k](v, site) for b in pg["blocks"] for k, v in b.items())
            if "blocks" in pg else doc_body(pg))
    main_open, main_close = ("<main>", "</main>") if "blocks" in pg else ("", "")
    ld = schema(site, pg) if pg["file"] == "index.html" else ""
    return f"""<!doctype html>
<html lang="en-US"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(pg["title"])}</title>
<meta name="description" content="{a(desc)}">
<link rel="canonical" href="{a(canonical)}">
<meta name="theme-color" content="#0E1210">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{a(site["name"])}">
<meta property="og:title" content="{a(pg["title"])}">
<meta property="og:description" content="{a(desc)}">
<meta property="og:url" content="{a(canonical)}">
<meta property="og:image" content="{a(url + "/" + site["og_image"])}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="{a(site["logo"])}">
{FONTS}
<style>
{css}
</style>
{ld}
</head><body>
{header(site)}
{main_open}{body}{main_close}
{footer(site)}
</body></html>
"""


# ------------------------------------------------------------------ files
def write(path: Path, text: str) -> bool:
    """Write `text`, moving a different existing file to Legacy Versions/ first."""
    if path.is_file():
        if path.read_text(encoding="utf-8") == text:
            return False
        dest = HERE / LEGACY / STAMP / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    site = yaml.safe_load((HERE / "site.yaml").read_text(encoding="utf-8"))
    css = (HERE / "site.css").read_text(encoding="utf-8")
    pages = []
    for y in sorted(HERE.glob("*.yaml")):
        if y.name == "site.yaml":
            continue
        try:
            pg = yaml.safe_load(y.read_text(encoding="utf-8"))
        except yaml.YAMLError as ex:
            print(f"  FAILED {y.name} doesn't parse, nothing built from it: {ex}")
            return 1
        out = HERE / pg["file"]
        changed = write(out, page(site, pg, css))
        print(f"  {'built ' if changed else 'same  '} {out.name}")
        pages.append(pg["file"])

    today = datetime.now().strftime("%Y-%m-%d")
    urls = "".join(
        f"<url><loc>{site['url']}/{'' if p == 'index.html' else p}</loc><lastmod>{today}</lastmod></url>"
        for p in sorted(pages, key=lambda p: p != "index.html"))
    write(HERE / "sitemap.xml",
          f'<?xml version="1.0" encoding="UTF-8"?>\n'
          f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    write(HERE / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {site['url']}/sitemap.xml\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
