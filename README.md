# hypordigital.com

The HyporDigital website, served by GitHub Pages.

The YAML files are the source. `site.yaml` holds the header, footer and business
details every page shares; `index.yaml`, `privacy.yaml` and `keyword-research.yaml`
each hold one page. `site.css` is the stylesheet and `motion.js` the scroll and
pointer motion; both are inlined into every page. To change anything, edit the
YAML, CSS or JS and rebuild:

```bash
python build_site.py
```

That rebuilds every page, `sitemap.xml` and `robots.txt`. Commit the YAML and the
HTML together.

Google's OAuth consent screen links to `privacy.html` and `keyword-research.html`.
Keep those file names, the app name on `keyword-research.html`, and the privacy
link in the footer, or brand verification breaks.
