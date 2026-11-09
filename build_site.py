"""Build hypordigital.com's pages from their YAML files.

    python build_site.py

The YAML files are the source. site.yaml holds what every page shares (header,
footer, business details) and each other .yaml holds one page. This script
only reads them; it never writes a YAML, so your edits always win.

Every page comes out self-contained (site.css is inlined). A page that changes
is moved to Legacy Versions/<stamp>/ before the new one is written. The script
also writes sitemap.xml and robots.txt.

Icons: any `icon:` in a YAML names one of the ICONS below (ads, web, systems,
brand, data, link, box, price, mail, ai, table, joystick, ball, store, gem,
medical, cart, camera, chart, search).
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

FONTS = ('<link rel="preload" href="fonts/schibsted-grotesk-latin.woff2" as="font" type="font/woff2" crossorigin>'
         '<link rel="preload" href="fonts/public-sans-latin.woff2" as="font" type="font/woff2" crossorigin>')

# 24x24 line icons, drawn with stroke="currentColor".
ICONS = {
    "ads": '<path d="M4 18V9m6 9V5m6 13v-6m4 6H2"/>',
    "web": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M7 6.5h.01M10 6.5h.01"/>',
    "systems": '<circle cx="12" cy="12" r="3"/><circle cx="4" cy="5" r="2"/><circle cx="20" cy="5" r="2"/>'
               '<circle cx="4" cy="19" r="2"/><circle cx="20" cy="19" r="2"/>'
               '<path d="M5.5 6.5 9.8 10M18.5 6.5 14.2 10M5.5 17.5l4.3-3.5M18.5 17.5l-4.3-3.5"/>',
    "brand": '<path d="M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.6 6.6 19.5l1.2-6L3.3 9.3l6.1-.7z"/>',
    "data": '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    "box": '<path d="M3 7.5 12 3l9 4.5v9L12 21l-9-4.5z"/><path d="M3 7.5 12 12l9-4.5M12 12v9"/>',
    "price": '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.5"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "ai": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4m6-4v4M9 18v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4M10 10h4v4h-4z"/>',
    "table": '<rect x="2" y="7" width="20" height="9" rx="1.5"/><circle cx="6" cy="11.5" r="1"/>'
             '<circle cx="15" cy="10" r="1"/><path d="M5 16v4m14-4v4"/>',
    "joystick": '<circle cx="12" cy="6" r="3"/><path d="M12 9v6"/><rect x="4" y="15" width="16" height="6" rx="2"/>',
    "ball": '<circle cx="12" cy="12" r="9"/><circle cx="9" cy="8" r=".8"/><circle cx="14" cy="9" r=".8"/>'
            '<circle cx="8" cy="13" r=".8"/><circle cx="13" cy="14" r=".8"/><circle cx="16.5" cy="13" r=".8"/>'
            '<circle cx="11" cy="17.5" r=".8"/>',
    "store": '<path d="M4 9h16l-1.5-5h-13zM5 9v11h14V9"/><path d="M10 20v-6h4v6"/>',
    "gem": '<path d="M6 3h12l4 6-10 12L2 9z"/><path d="M2 9h20M9 3l-1 6 4 12 4-12-1-6"/>',
    "medical": '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M12 8v8m-4-4h8"/>',
    "cart": '<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.7 12.4h11.6L22 7H6.3"/>',
    "camera": '<path d="M3 8h4l2-3h6l2 3h4v12H3z"/><circle cx="12" cy="13.5" r="3.5"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 6-7"/><path d="M16 7h4v4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
}


def icon(name, cls="ico") -> str:
    if not name:
        return ""
    paths = ICONS.get(name)
    if paths is None:
        print(f"  note: no icon named '{name}', left it out")
        return ""
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths}</svg>')


def a(s) -> str:
    """Attribute value."""
    return escape(str(s), quote=True)


def link(label, href, cls="") -> str:
    ext = href.startswith("http")
    rel = ' rel="noopener" target="_blank"' if ext else ""
    arrow = '<span class="arrow" aria-hidden="true">→</span>' if "btn" in cls else ""
    klass = f' class="{cls}"' if cls else ""
    return f'<a{klass} href="{a(href)}"{rel}>{label}{arrow}</a>'


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
    return f' id="{a(b["id"])}"' if b.get("id") else ""


def band_head(b, center=False) -> str:
    intro = f'<p class="intro">{b["intro"]}</p>' if b.get("intro") else ""
    cls = "band-head center" if center else "band-head"
    return (f'<div class="{cls}"><p class="kicker">{b["kicker"]}</p>'
            f'<h2>{b["title"]}</h2>{intro}</div>')


def stat_tiles(results) -> str:
    tiles = "".join(f'<div class="tile"><span class="v">{escape(str(v))}</span><span class="k">{k}</span></div>'
                    for v, k in results)
    return f'<div class="tiles">{tiles}</div>'


# ------------------------------------------------------------------ blocks
def hero(b, site):
    aside = ""
    if b.get("aside"):
        ab = b["aside"]
        if ab.get("stats"):
            rows = "".join(f'<li><span class="v">{escape(str(v))}</span><span class="k">{k}</span></li>'
                           for v, k in ab["stats"])
            aside = (f'<aside class="hero-card"><p class="label"><span class="dot"></span>{ab["label"]}</p>'
                     f'<ul>{rows}</ul>'
                     + (f'<p class="foot-note">{ab["note"]}</p>' if ab.get("note") else "")
                     + '</aside>')
        else:
            rows = "".join(f'<li>{x}</li>' for x in ab["items"])
            aside = f'<aside class="hero-card"><p class="label">{ab["label"]}</p><ul class="plain">{rows}</ul></aside>'
    return (f'<section class="hero">'
            f'<div class="wrap hero-grid"><div class="hero-copy">'
            f'<p class="kicker">{b["kicker"]}</p><h1>{b["title"]}</h1>'
            f'<p class="sub">{b["sub"]}</p>{buttons(b.get("actions"))}'
            f'<p class="meta">{b.get("meta", "")}</p></div>'
            + (f'<div class="hero-stack">{aside}</div>' if aside else "")   # layered cards behind it, in 3D
            + '</div></section>')


def logos(b, site):
    """The strip of industries: one line that scrolls sideways on a loop. The list is printed twice so the loop
    is seamless; the copy is hidden from screen readers. Without motion it is one wrapped list."""
    names = "".join(f"<li>{escape(n)}</li>" for n in b["names"])
    return (f'<section class="marquee" aria-label="{a(b["label"])}">'
            f'<p class="label wrap">{b["label"]}</p><div class="track"><div class="lane">'
            f'<ul>{names}</ul><ul aria-hidden="true">{names}</ul></div></div></section>')


def figures(b, site):
    items = b["items"] if isinstance(b, dict) else b
    cells = "".join(f'<div class="figure"><div class="v">{escape(str(v))}</div>'
                    f'<div class="k">{k}</div></div>' for v, k in items)
    title = ""
    if isinstance(b, dict) and b.get("title"):
        title = (f'<div class="panel-head"><p class="kicker">{b.get("kicker", "")}</p>'
                 f'<h2>{b["title"]}</h2>'
                 + (f'<p class="intro">{b["intro"]}</p>' if b.get("intro") else "") + '</div>')
    return (f'<section class="panel-wrap" aria-label="Results at a glance"><div class="wrap">'
            f'<div class="panel light">{title}<div class="figures">{cells}</div></div></div></section>')


def services(b, site):
    items = "".join(
        f'<article class="service"><div class="badge">{icon(s.get("icon"))}</div><h3>{s["title"]}</h3>'
        f'<p>{s["text"]}</p><ul class="tags">'
        + "".join(f"<li>{escape(t)}</li>" for t in s.get("tags", []))
        + "</ul></article>"
        for s in b["items"])
    return (f'<section class="band"{head_of(b)}><div class="wrap">{band_head(b)}'
            f'<div class="services">{items}</div></div></section>')


def work(b, site):
    cards = []
    for i, c in enumerate(b["items"]):
        tags = "".join(f"<li>{escape(t)}</li>" for t in c.get("tags", []))
        results = c.get("results") or ([c["result"]] if c.get("result") else [])
        tone = c.get("tone", ["ember", "violet", "cyan", "pink"][i % 4])
        # image: an optional screenshot for the cover (a path in the site folder); without one, the colour block
        # and its icon stand in
        cover = (f'<img class="cover-img" src="{a(c["image"])}" alt="{a(c.get("image_alt", ""))}" loading="lazy">'
                 if c.get("image") else icon(c.get("icon"), "cover-ico"))
        cards.append(
            f'<article class="work-card tone-{a(tone)}">'
            f'<div class="cover">{cover}'
            f'<span class="pill">{c["category"]}</span></div>'
            f'<div class="body"><p class="who">{escape(c["brand"])}</p>'
            f'<h3>{c["headline"]}</h3><p>{c["text"]}</p>'
            + (stat_tiles(results) if results else "")
            + f'<ul class="tags">{tags}</ul></div></article>')
    note = f'<p class="note">{b["note"]}</p>' if b.get("note") else ""
    return (f'<section class="band"{head_of(b)}><div class="wrap">{band_head(b)}'
            f'<div class="work">{"".join(cards)}</div>{note}</div></section>')


def diagram(d) -> str:
    """Sources on the left feed one hub; the hub feeds outputs on the right.
    Drawn as SVG for wide screens, with a stacked HTML version for phones."""
    W, H = 640, 400
    src, out = d["sources"], d["outputs"]

    def ys(n):
        step = H / (n + 1)
        return [round(step * (i + 1)) for i in range(n)]

    cx, cy, r = W / 2, H / 2, 62
    parts = []
    for y in ys(len(src)):
        parts.append(f'<path class="flow" d="M150 {y} C 230 {y}, 220 {cy}, {cx - r} {cy}"/>')
    for y in ys(len(out)):
        parts.append(f'<path class="flow out" d="M{cx + r} {cy} C 420 {cy}, 410 {y}, 490 {y}"/>')
    for y, label in zip(ys(len(src)), src):
        parts.append(f'<g class="node"><rect x="10" y="{y - 17}" width="140" height="34" rx="17"/>'
                     f'<text x="80" y="{y + 5}">{escape(label)}</text></g>')
    for y, label in zip(ys(len(out)), out):
        parts.append(f'<g class="node outn"><rect x="490" y="{y - 17}" width="140" height="34" rx="17"/>'
                     f'<text x="560" y="{y + 5}">{escape(label)}</text></g>')
    hub_lines = d["hub"].split("\n") if "\n" in d["hub"] else [d["hub"]]
    hub_text = "".join(f'<tspan x="{cx}" dy="{0 if i == 0 else 18}">{escape(t)}</tspan>'
                       for i, t in enumerate(hub_lines))
    first_dy = -9 * (len(hub_lines) - 1)
    parts.append(f'<circle class="hub-ring" cx="{cx}" cy="{cy}" r="{r + 14}"/>'
                 f'<circle class="hub" cx="{cx}" cy="{cy}" r="{r}"/>'
                 f'<text class="hub-t" x="{cx}" y="{cy + 5 + first_dy}">{hub_text}</text>')
    svg = (f'<svg class="diagram-svg" viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="{a(d.get("label", "How the systems connect"))}">'
           f'{"".join(parts)}</svg>')
    chips = lambda xs: "".join(f"<li>{escape(x)}</li>" for x in xs)
    stacked = (f'<div class="diagram-stack" aria-hidden="true"><ul>{chips(src)}</ul>'
               f'<div class="hub-chip">{escape(" ".join(hub_lines))}</div><ul class="outs">{chips(out)}</ul></div>')
    return f'<div class="diagram">{svg}{stacked}</div>'


def systems(b, site):
    items = "".join(
        f'<article class="system">{icon(s.get("icon"))}<div><h3>{s["title"]}</h3><p>{s["text"]}</p>'
        + (f'<p class="eg">{s["example"]}</p>' if s.get("example") else "")
        + "</div></article>"
        for s in b["items"])
    feature = ""
    if b.get("diagram"):
        points = "".join(f"<li>{p}</li>" for p in b.get("points", []))
        feature = (f'<div class="platform"><div class="platform-copy"><p class="kicker">{b["kicker"]}</p>'
                   f'<h2>{b["title"]}</h2><p class="intro">{b.get("intro", "")}</p>'
                   f'<ul class="checks">{points}</ul></div>{diagram(b["diagram"])}</div>')
        head = ""
    else:
        head = band_head(b)
    return (f'<section class="band systems-band"{head_of(b)}><div class="wrap">{head}{feature}'
            f'<div class="systems">{items}</div></div></section>')


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
        f'<li class="step"><span class="n">{i}</span><h3>{s["title"]}</h3><p>{s["text"]}</p></li>'
        for i, s in enumerate(b["items"], 1))
    note = f'<p class="note">{b["note"]}</p>' if b.get("note") else ""
    return (f'<section class="panel-wrap"{head_of(b)}><div class="wrap"><div class="panel light">'
            f'{band_head(b)}<ol class="steps">{items}</ol>{note}</div></div></section>')


def about(b, site):
    copy = "".join(f"<p>{p}</p>" for p in b["copy"])
    facts = "".join(f'<li><span class="v">{escape(str(v))}</span><span class="k">{escape(k)}</span></li>'
                    for k, v in b.get("facts", []))
    return (f'<section class="band"{head_of(b)}><div class="wrap about">'
            f'<div><p class="kicker">{b["kicker"]}</p><h2>{b["title"]}</h2><div class="copy">{copy}</div></div>'
            f'<ul class="facts">{facts}</ul></div></section>')


GRADE_TONE = {"A": "a", "B": "b", "C": "c", "D": "d"}

LEAD_JS = """<script>
document.querySelectorAll('form.lead-form').forEach(function (f) {
  f.addEventListener('submit', function (e) {
    e.preventDefault();
    if (f.elements.company && f.elements.company.value) return;
    var d = Object.fromEntries(new FormData(f)), btn = f.querySelector('button');
    function show(state) {
      f.querySelectorAll('.ok b').forEach(function (b) { b.textContent = d.brand; });
      f.classList.remove('failed'); f.classList.add(state);
    }
    /* No relay: hand the request to the visitor's email app. Nothing has been sent yet, so the page says so and
       no conversion fires. */
    if (!f.dataset.endpoint) {
      location.href = 'mailto:' + f.dataset.to + '?subject=' + encodeURIComponent('Brand analysis request: ' + d.brand)
        + '&body=' + encodeURIComponent('Brand: ' + d.brand + '\\nWebsite: ' + (d.website || '-') + '\\nEmail: ' + d.email);
      show('mailed'); return;
    }
    /* The relay (form-relay.gs, a Google Apps Script web app) answers {"ok":true} only once the request is stored
       and mailed; anything else is a failure. URL-encoded and without custom headers, so no CORS preflight. */
    btn.disabled = true;
    fetch(f.dataset.endpoint, {method: 'POST', body: new URLSearchParams(new FormData(f))})
      .then(function (r) { if (!r.ok) throw r; return r.json(); })
      .then(function (j) {
        if (!j || !j.ok) throw j;
        show('sent');
        if (window.gtag && f.dataset.conversion) gtag('event', 'conversion', {send_to: f.dataset.conversion});
      })
      .catch(function () { f.classList.add('failed'); btn.disabled = false; });
  });
});
</script>"""


def analysis(b, site):
    """The brand-analysis offer: what's in it, a sample scorecard, and the request form."""
    gets = "".join(
        f'<li>{icon(g.get("icon"))}<div><h3>{g["title"]}</h3><p>{g["text"]}</p></div></li>'
        for g in b["gets"])
    s = b["sample"]
    rows = "".join(
        f'<li><span>{escape(area)}</span><span class="grade g-{GRADE_TONE.get(str(g)[0], "d")}">{escape(str(g))}</span></li>'
        for area, g in s["areas"])
    sample = (f'<aside class="scorecard" aria-label="{a(s["label"])}">'
              f'<div class="sc-head"><p class="label">{s["label"]}</p>'
              f'<div class="sc-brand"><span>{escape(s["brand"])}</span>'
              f'<span class="overall"><small>Overall</small>{escape(str(s["overall"]))}</span></div></div>'
              f'<ul class="sc-rows">{rows}</ul>'
              f'<div class="sc-first"><p class="label">{s["first_label"]}</p><ol>'
              + "".join(f"<li>{p}</li>" for p in s["first"])
              + f'</ol></div><p class="sc-note">{s["note"]}</p></aside>')
    steps_html = "".join(f'<li><span class="n">{i}</span><div><h3>{st["title"]}</h3><p>{st["text"]}</p></div></li>'
                         for i, st in enumerate(b["steps"], 1))
    fm = b["form"]
    hidden = "".join(f'<input type="hidden" name="{a(k)}" value="{a(v)}">'
                     for k, v in (fm.get("hidden") or {}).items())
    form = (f'<form class="lead-form" data-endpoint="{a(fm.get("endpoint", ""))}" data-to="{a(site["email"])}"'
            f' data-conversion="{a(fm.get("ads_conversion", ""))}">'
            f'<h3>{fm["title"]}</h3><p class="lede">{fm["text"]}</p>{hidden}'
            f'<label>{fm["brand_label"]}<input name="brand" required autocomplete="organization" '
            f'placeholder="{a(fm["brand_hint"])}"></label>'
            f'<label>{fm["email_label"]}<input name="email" type="email" required autocomplete="email" '
            f'placeholder="{a(fm["email_hint"])}"></label>'
            f'<label>{fm["site_label"]} <span class="opt">{fm["site_optional"]}</span>'
            f'<input name="website" type="text" inputmode="url" autocomplete="url" placeholder="{a(fm["site_hint"])}"></label>'
            f'<label class="hp" aria-hidden="true">Company<input name="company" tabindex="-1" autocomplete="off"></label>'
            f'<button class="btn primary" type="submit">{fm["button"]}<span class="arrow" aria-hidden="true">→</span></button>'
            f'<p class="fine">{fm["fine"]}</p>'
            f'<p class="err" role="alert">{fm["error"]}</p>'
            f'<div class="ok is-sent" role="status"><span class="tick" aria-hidden="true"></span>'
            f'<h3>{fm["success_title"]}</h3><p>{fm["success"]}</p></div>'
            f'<div class="ok is-mailed" role="status"><h3>{fm.get("mail_title", "One more step")}</h3>'
            f'<p>{fm.get("mail_text", "Your email app should open with the request ready to send.")}</p></div></form>')
    return (f'<section class="band analysis-band"{head_of(b)}><div class="wrap">{band_head(b)}'
            f'<div class="offer"><div><p class="sub-k">{b["gets_label"]}</p><ul class="gets">{gets}</ul></div>'
            f'{sample}</div>'
            f'<div class="request">'
            f'<div class="request-copy"><p class="sub-k">{b["steps_label"]}</p><ol class="how">{steps_html}</ol></div>'
            f'{form}</div></div></section>{LEAD_JS}')


def cta(b, site):
    return (f'<section class="cta-wrap"{head_of(b)}><div class="wrap"><div class="cta">'
            f'<h2>{b["title"]}</h2>'
            f'<p>{b["text"]}</p>{buttons(b.get("actions"))}</div></div></section>')


def access_guide(b, site):
    """Animated how-to over real screenshots: one tab per Google service, a pointer that moves to each click and a
    ring around it, a ripple when it clicks, the step list under it, and a thank-you card with the logo after the last
    step (`thanks:`). A step can zoom in on its target (zoom: 2). Screenshot coordinates are in the capture's own pixels (`size`) and turn
    into percentages here, so the overlay stays on target at any width."""
    W, H = b.get("size", [1568, 778])
    pct = lambda v, d: f"{v / d * 100:.3f}%"  # noqa: E731
    email = escape(b["email"])
    th = b.get("thanks") or {}
    w1, w2 = site.get("wordmark", [site["name"], ""])
    end_card = (f'<div class="g-end" hidden><img src="{a(site.get("icon", site["logo"]))}" alt="" width="72" height="72">'
                f'<span class="g-end-mark">{escape(w1)}<span class="w2">{escape(w2)}</span></span>'
                f'<p class="g-end-title">{th.get("title", "Thank you")}</p>'
                + (f'<p class="g-end-text">{th["text"]}</p>' if th.get("text") else "") + '</div>')
    tabs, panels = [], []
    for n, s in enumerate(b["services"]):
        sid = a(s["id"])
        sel = "true" if n == 0 else "false"
        tabs.append(f'<button role="tab" id="tab-{sid}" aria-controls="p-{sid}" aria-selected="{sel}" '
                    f'data-for="{sid}">{icon(s.get("icon"))}<span>{escape(s["name"])}</span></button>')
        steps_data, items = [], []
        for i, st in enumerate(s["steps"], 1):
            x, y, w, h = st["box"]
            px, py = st.get("at", [x + w / 2, y + h / 2])
            steps_data.append({"img": st["image"], "box": [pct(x, W), pct(y, H), pct(w, W), pct(h, H)],
                               "at": [pct(px, W), pct(py, H)], "zoom": st.get("zoom", 1),
                               "label": st.get("label", "")})
            items.append(f'<li><button type="button" data-step="{i - 1}"><span class="n">{i}</span>'
                         f'<span>{st["text"]}</span></button></li>')
        first = s["steps"][0]
        note = f'<p class="g-note">{s["note"]}</p>' if s.get("note") else ""
        panels.append(
            f'<div class="g-panel" role="tabpanel" id="p-{sid}" aria-labelledby="tab-{sid}"'
            f'{"" if n == 0 else " hidden"} data-steps="{a(json.dumps(steps_data))}">'
            f'<div class="g-head"><h3>{escape(s["name"])}</h3>'
            f'<p class="g-meta"><span>Access level: <strong>{escape(s["level"])}</strong></span>'
            f'<span>About {escape(str(s["minutes"]))} minute{"" if str(s["minutes"]) == "1" else "s"}</span>'
            + (f'<a href="{a(s["help"])}" rel="noopener" target="_blank">Google\'s help page</a>' if s.get("help") else "")
            + f'</p></div>'
            f'<div class="g-body"><figure class="g-player">'
            f'<div class="g-screen"><div class="g-stage"><img src="{a(first["image"])}" alt="" width="1568" height="{round(1568 * H / W)}" '
            f'loading="{"eager" if n == 0 else "lazy"}">'
            f'<span class="g-ring" aria-hidden="true"></span><span class="g-click" aria-hidden="true"></span><span class="g-tag" aria-hidden="true" hidden></span>'
            f'<svg class="g-pointer" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 2l15 10-7 1.5L8.5 21z"/></svg>'
            f'</div>{end_card}</div>'
            f'<figcaption class="g-controls"><button type="button" class="g-prev" aria-label="Previous step">'
            f'<span aria-hidden="true">‹</span></button>'
            f'<button type="button" class="g-play" aria-label="Pause">Pause</button>'
            f'<button type="button" class="g-next" aria-label="Next step"><span aria-hidden="true">›</span></button>'
            f'<span class="g-count" aria-live="polite">Step 1 of {len(s["steps"])}</span></figcaption></figure>'
            f'<ol class="g-steps">{"".join(items)}</ol></div>{note}</div>')
    copy = (f'<div class="g-email"><span class="g-label">The email to add</span><code>{email}</code>'
            f'<button type="button" class="btn primary small g-copy" data-copy="{a(b["email"])}">Copy</button></div>')
    return (f'<section class="band access"{head_of(b)}><div class="wrap">{band_head(b)}{copy}'
            f'<div class="g-tabs" role="tablist" aria-label="Google services">{"".join(tabs)}</div>'
            f'{"".join(panels)}</div></section>{GUIDE_JS}')


GUIDE_JS = """<script>
(function(){
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.access').forEach(function(root){
    var tabs = root.querySelectorAll('[role=tab]');
    var players = {};
    function player(panel){
      var steps = JSON.parse(panel.dataset.steps), i = 0, timer = null, playing = !reduce;
      var img = panel.querySelector('.g-screen img'), ring = panel.querySelector('.g-ring'),
          ptr = panel.querySelector('.g-pointer'), clk = panel.querySelector('.g-click'),
          stage = panel.querySelector('.g-stage'), tag = panel.querySelector('.g-tag'),
          count = panel.querySelector('.g-count'), end = panel.querySelector('.g-end'),
          N = steps.length + 1,
          play = panel.querySelector('.g-play'), items = panel.querySelectorAll('.g-steps button');
      steps.forEach(function(s){ var p = new Image(); p.src = s.img; });
      function show(n){
        i = (n + N) % N;
        if (i === steps.length) {                       // the end card: logo and thanks
          end.hidden = false; void end.offsetWidth; end.classList.add('on');
          ring.classList.remove('click'); clk.classList.remove('go');
          items.forEach(function(b){ b.classList.remove('on'); b.setAttribute('aria-current', 'false'); });
          count.textContent = 'All done';
          return;
        }
        end.classList.remove('on'); end.hidden = true;
        var s = steps[i];
        if (img.getAttribute('src') !== s.img) img.src = s.img;
        ring.classList.remove('click');
        ring.style.left = s.box[0]; ring.style.top = s.box[1]; ring.style.width = s.box[2]; ring.style.height = s.box[3];
        ptr.style.left = s.at[0]; ptr.style.top = s.at[1];
        clk.style.left = s.at[0]; clk.style.top = s.at[1];
        tag.hidden = !s.label; tag.textContent = s.label || '';
        tag.style.left = s.box[0]; tag.style.top = s.box[1];
        stage.style.transformOrigin = s.at[0] + ' ' + s.at[1];
        stage.style.transform = s.zoom > 1 ? 'scale(' + s.zoom + ')' : '';
        ptr.classList.remove('press'); clk.classList.remove('go');
        setTimeout(function(){
          ring.classList.add('click');
          if (reduce) return;
          void clk.offsetWidth; ptr.classList.add('press'); clk.classList.add('go');
          setTimeout(function(){ ptr.classList.remove('press'); }, 260);
        }, reduce ? 0 : 800);
        items.forEach(function(b, k){ b.classList.toggle('on', k === i); b.setAttribute('aria-current', k === i ? 'step' : 'false'); });
        count.textContent = 'Step ' + (i + 1) + ' of ' + steps.length;
      }
      function tick(){ clearTimeout(timer); if (playing) timer = setTimeout(function(){ show(i + 1); tick(); },
                                                                          i === steps.length ? 4200 : 3600); }
      function setPlay(on){ playing = on; play.textContent = on ? 'Pause' : 'Play'; play.setAttribute('aria-label', on ? 'Pause' : 'Play'); tick(); }
      panel.querySelector('.g-next').onclick = function(){ setPlay(false); show(i + 1); };
      panel.querySelector('.g-prev').onclick = function(){ setPlay(false); show(i - 1); };
      play.onclick = function(){ setPlay(!playing); };
      items.forEach(function(b){ b.onclick = function(){ setPlay(false); show(+b.dataset.step); }; });
      show(0); setPlay(playing);
      return {stop: function(){ setPlay(false); }, start: function(){ show(0); setPlay(!reduce); }};
    }
    function select(id, focus){
      tabs.forEach(function(t){
        var on = t.dataset.for === id, panel = root.querySelector('#p-' + t.dataset.for);
        t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; panel.hidden = !on;
        if (on) { players[id] = players[id] || player(panel); players[id].start(); if (focus) t.focus(); }
        else if (players[t.dataset.for]) players[t.dataset.for].stop();
      });
    }
    tabs.forEach(function(t, k){
      t.onclick = function(){ select(t.dataset.for); history.replaceState(null, '', '#' + t.dataset.for); };
      t.onkeydown = function(e){
        var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (d) { e.preventDefault(); select(tabs[(k + d + tabs.length) % tabs.length].dataset.for, true); }
      };
    });
    var want = location.hash.slice(1);
    select(Array.prototype.some.call(tabs, function(t){ return t.dataset.for === want; }) ? want : tabs[0].dataset.for);
    var copy = root.querySelector('.g-copy');
    if (copy) copy.onclick = function(){
      navigator.clipboard.writeText(copy.dataset.copy).then(function(){
        copy.textContent = 'Copied'; setTimeout(function(){ copy.textContent = 'Copy'; }, 2000); });
    };
  });
})();
</script>"""


BLOCKS = {"hero": hero, "logos": logos, "figures": figures, "services": services,
          "work": work, "systems": systems, "cases": cases, "steps": steps, "about": about,
          "analysis": analysis, "cta": cta, "access_guide": access_guide}


def doc_body(pg) -> str:
    """A long-form page: privacy policy, app page."""
    date = f'<p class="date">Last updated {pg["updated"]}</p>' if pg.get("updated") else ""
    secs = "".join(f'<section><h2>{s["title"]}</h2><div class="body">{paras(s["body"])}</div></section>'
                   for s in pg["sections"])
    return (f'<main class="doc" id="main" tabindex="-1"><div class="wrap">'
            f'<header><p class="kicker">{pg.get("kicker", "HyporDigital")}</p><h1>{pg["heading"]}</h1>'
            f'<p class="lede">{pg["lede"]}</p>{date}</header>'
            f'<article class="panel light doc-panel">{secs}</article></div></main>')


# ------------------------------------------------------------------ chrome
def brand(site, label=True) -> str:
    """The icon plus the two-weight wordmark (Hypor bold, Digital lighter)."""
    w1, w2 = site.get("wordmark", [site["name"], ""])
    aria = f' aria-label="{a(site["name"])} home"' if label else ""
    return (f'<a class="brand" href="index.html"{aria}>'
            f'<img src="{a(site.get("icon", site["logo"]))}" alt="" width="34" height="34">'
            f'<span>{escape(w1)}<span class="w2">{escape(w2)}</span></span></a>')


def header(site) -> str:
    nav = "".join(link(t, h) for t, h in site["header"]["nav"])
    label, href = site["header"]["cta"]
    return (f'<header class="top"><div class="wrap">{brand(site)}'
            f'<nav aria-label="Main">{nav}</nav>'
            f'<div class="top-right">{link(label, href, "btn primary small")}'
            f'<details class="menu"><summary aria-label="Menu"><span></span><span></span><span></span></summary>'
            f'<nav aria-label="Mobile">{nav}{link(label, href)}</nav></details></div>'
            f'</div></header>')


def footer(site) -> str:
    f = site["footer"]
    cols = "".join(
        f'<div class="col"><p class="h">{escape(c["title"])}</p><ul>'
        + "".join(f"<li>{link(t, h)}</li>" for t, h in c["links"])
        + "</ul></div>"
        for c in f.get("columns", []))
    return (f'<footer class="foot"><div class="wrap"><div class="foot-grid">'
            f'<div class="col about-col">{brand(site, label=False)}'
            f'<p>{f.get("blurb", "")}</p>{link(site["email"], "mailto:" + site["email"], "mail")}</div>'
            f'{cols}</div><div class="foot-line"><span>{f["line"]}</span></div></div></footer>')


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


def gtag(site) -> str:
    """The Google tag, placed first in <head> as Google asks."""
    tid = site.get("google_tag")
    if not tid:
        return ""
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={a(tid)}"></script>\n'
            f"<script>window.dataLayer = window.dataLayer || [];function gtag(){{dataLayer.push(arguments);}}"
            f"gtag('js', new Date());gtag('config', '{a(tid)}');</script>\n")


def gtm_head(site) -> str:
    """Google Tag Manager's container, high in <head> as Google asks."""
    cid = site.get("google_tag_manager")
    if not cid:
        return ""
    return ("<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});"
            "var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;"
            "j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);"
            f"}})(window,document,'script','dataLayer','{a(cid)}');</script>\n")


def gtm_body(site) -> str:
    """Tag Manager's fallback for browsers without JavaScript, right after <body>."""
    cid = site.get("google_tag_manager")
    if not cid:
        return ""
    return (f'<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={a(cid)}" '
            'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n')


# ------------------------------------------------------------------ motion
# Charles, 11/08/2026: motion in the spirit of digitalsilk.com (headings rising through a mask, reveals on scroll,
# figures counting up, a line drawing across the process). Only with JavaScript and without reduced motion: the head
# script adds .m; if the motion script never starts, the guard drops .m after 4 seconds so nothing stays hidden.
# The script itself lives in motion.js beside site.css and is inlined the same way. It loads Lenis last, so the
# page never waits on the CDN.
MOTION_HEAD = ("<script>if(!matchMedia('(prefers-reduced-motion: reduce)').matches){var r=document.documentElement;"
               "r.classList.add('m');setTimeout(function(){if(!window.__hdm)r.classList.remove('m')},4000)}</script>")

MOTION_JS = "<script>\n" + (HERE / "motion.js").read_text(encoding="utf-8") + "</script>"



def page(site, pg, css) -> str:
    url = site["url"]
    path = "" if pg["file"] == "index.html" else pg["file"]
    canonical = f"{url}/{path}"
    desc = " ".join(pg["description"].split())
    body = ("".join(BLOCKS[k](v, site) for b in pg["blocks"] for k, v in b.items())
            if "blocks" in pg else doc_body(pg))
    main_open, main_close = ('<main id="main" tabindex="-1">', "</main>") if "blocks" in pg else ("", "")
    ld = schema(site, pg) if pg["file"] == "index.html" else ""
    return f"""<!doctype html>
<html lang="en-US"><head><meta charset="utf-8">
{gtm_head(site)}{gtag(site)}<meta name="viewport" content="width=device-width,initial-scale=1">
{MOTION_HEAD}
<title>{escape(pg["title"])}</title>
<meta name="description" content="{a(desc)}">
<link rel="canonical" href="{a(canonical)}">
<meta name="theme-color" content="#0A0C18">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{a(site["name"])}">
<meta property="og:title" content="{a(pg["title"])}">
<meta property="og:description" content="{a(desc)}">
<meta property="og:url" content="{a(canonical)}">
<meta property="og:image" content="{a(url + "/" + site["og_image"])}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
{FONTS}
<style>
{css}
</style>
{ld}
</head><body>
{gtm_body(site)}<a class="skip" href="#main">Skip to content</a>
{header(site)}
{main_open}{body}{main_close}
{footer(site)}
{MOTION_JS}
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
