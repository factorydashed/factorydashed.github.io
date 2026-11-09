#!/usr/bin/env python3
"""Generates the static site in docs/ from apps.json. Run: python3 build.py"""
import json
import sys
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
DATA = json.loads((ROOT / "apps.json").read_text())
SITE, APPS = DATA["site"], DATA["apps"]
BASE = f"https://{SITE['domain']}"
FONTS = "https://fonts.googleapis.com/css2?family=Anton&family=Barlow+Condensed:wght@500;600&family=Geist:wght@400;500;700&display=swap"


def asset(app, name):
    return f"/assets/{app['slug']}/{name}"


def check_images():
    missing = []
    for a in APPS:
        names = [a["hero"]] + [t["image"] for t in a["themes"]]
        names += [f["image"] for g in a["groups"] for f in g["features"] if f["image"]]
        missing += [asset(a, n) for n in names if not (DOCS / asset(a, n)[1:]).exists()]
    if missing:
        sys.exit("Missing images:\n" + "\n".join(missing))


def page(title, desc, path, body, index=True, cls=""):
    robots = "" if index else '<meta name="robots" content="noindex">'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">{robots}
<link rel="canonical" href="{BASE}{path}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{BASE}{path}"><meta property="og:type" content="website">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="{FONTS}"><link rel="stylesheet" href="/assets/site.css"><script src="/assets/site.js" defer></script></head>
<body class="{cls}">{body}</body></html>
"""


def write(rel, text):
    f = DOCS / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)


def scope(a):
    b = a["brand"]
    style = ";".join(f"--{k}:{v}" for k, v in [("bg", b["bg"]), ("fg", b["fg"]), ("mut", b["mut"]), ("pill-bg", b["pillBg"]), ("pill-fg", b["pillFg"]), ("store-bg", b["storeBg"]), ("store-fg", b["storeFg"])])
    cls = f"d-{b['display']} store-{b['storeStyle']}" + (" tex" if b["texture"] else "")
    return cls, style


def mark(a):
    return f'<span class="mark">{e(a["name"])}<span class="pill">-ed</span></span>'


def brand():
    return '<span class="mark brandm">factory<span class="pill">-ed</span></span>'


def shot(src, alt, lazy=True):
    load = ' loading="lazy"' if lazy else ""
    return f'<figure class="ph"><img src="{src}" alt="{e(alt)}"{load} decoding="async"></figure>'


def stores(a):
    play = f'<a class="store" href="{e(a["play"])}" rel="noopener">Google Play</a>' if a["play"] else '<span class="soon strong">Coming to Google Play</span>'
    ios = f'<a class="store" href="{e(a["appStore"])}" rel="noopener">App Store</a>' if a["appStore"] else '<span class="soon">App Store later</span>'
    return f'<div class="stores">{play}{ios}</div>'


def footer():
    links = "".join(f'<a href="/{a["slug"]}/privacy/">{a["slug"]} privacy</a>' for a in APPS)
    return f'<footer class="foot"><span>© {SITE["year"]} {SITE["name"]}</span><nav aria-label="Footer">{links}<a href="mailto:{SITE["contact"]}">Contact</a></nav></footer>'


def film(a, eager=False):
    imgs = [f["image"] for g in a["groups"] for f in g["features"] if f["image"]][:14]
    while len(imgs) < 14:
        imgs += imgs
    imgs = imgs[:14]
    def load(n):
        return "" if eager and n < 8 else ' loading="lazy"'
    return "".join(f'<figure class="ph"><img src="{asset(a, x)}" alt=""{load(n)}></figure>' for n, x in enumerate(imgs * 2))


def row(a, i):
    cls, style = scope(a)
    alt = " alt" if i % 2 else ""
    return f"""<div class="wrap"><section class="row {cls}{alt}" style="{style}" aria-labelledby="r-{a['slug']}">
<div class="fw" aria-hidden="true"><div class="film">{film(a, eager=i == 0)}</div></div>
<div class="copy"><h2 id="r-{a['slug']}"><a href="/{a['slug']}/">{mark(a)}</a></h2><p>{e(a['line'])} {e(a['about'])}</p>{stores(a)}<a class="see" href="/{a['slug']}/">See every feature</a></div></section></div>"""


def home():
    stripes = "".join(f'<i style="background:{a["brand"]["stripe"]}"></i>' for a in APPS)
    verbs = ", ".join(a["slug"] for a in APPS)
    body = f"""<header class="hero"><div class="sw" aria-hidden="true">{stripes}</div><div class="tx"><h1>{brand()}</h1><p>{e(SITE['concept'])}</p><button id="motion" class="motion" aria-pressed="false">Pause motion</button></div></header>
<main>{''.join(row(a, i) for i, a in enumerate(APPS))}</main>{footer()}"""
    write("index.html", page(f"{SITE['name']}: {SITE['concept']}", f"{SITE['name']} makes small Android apps, one per verb: {verbs}.", "/", body))


def top(a):
    links = "".join(f'<a href="/{x["slug"]}/"{" aria-current=page" if x is a else ""}><img src="{asset(x, "icon.svg")}" alt="" width="32" height="32">{x["slug"]}</a>' for x in APPS)
    return f'<nav class="top" aria-label="Main"><a href="/" aria-label="{SITE["name"]} home">{brand()}</a><details class="menu"><summary>Apps</summary><div>{links}<a class="all" href="/">All apps</a></div></details></nav>'


def feature(a, f):
    pic = shot(asset(a, f["image"]), f["title"]) if f["image"] else f'<div class="ph noimg"><img src="{asset(a, "icon.svg")}" alt="" loading="lazy"></div>'
    return f'<article>{pic}<h3>{e(f["title"])}</h3><p>{e(f["text"])}</p></article>'


def media(a):
    poster = asset(a, a["hero"])
    if a["video"]:
        return f'<video class="ph" src="{e(a["video"])}" poster="{poster}" controls muted playsinline preload="none" aria-label="{a["slug"]} demo"></video>'
    return shot(poster, f'{a["slug"]} in the {a["defaultTheme"]} theme', lazy=False)


def app_page(a, i):
    cls, style = scope(a)
    nxt = APPS[(i + 1) % len(APPS)]
    ncls, nstyle = scope(nxt)
    groups = "".join(f'<section class="fs"><h2>{e(g["title"])}</h2><div class="strip" tabindex="0" role="group" aria-label="{e(g["title"])} features">{"".join(feature(a, f) for f in g["features"])}</div></section>' for g in a["groups"])
    themes = "".join(f'<figure>{shot(asset(a, t["image"]), f"{a["slug"]} in the {t["name"]} theme")}<figcaption>{e(t["name"])}{" <em>default</em>" if t["name"] == a["defaultTheme"] else ""}</figcaption></figure>' for t in a["themes"])
    facts = "".join(f"<li>{e(x)}</li>" for x in a["facts"])
    next_link = "" if len(APPS) < 2 else f'<a class="nextapp {ncls}" style="{nstyle}" href="/{nxt["slug"]}/"><small>Next app</small>{mark(nxt)}</a>'
    body = f"""<div class="page {cls}" style="{style}">{top(a)}<main><header class="hh">{media(a)}<div><h1>{mark(a)}</h1><p><b>{e(a['line'])}</b> {e(a['about'])}</p>{stores(a)}<ul class="facts">{facts}</ul></div></header>
{groups}<section class="fs"><h2>{len(a['themes'])} themes</h2><div class="strip themes" tabindex="0" role="group" aria-label="Themes">{themes}</div></section></main>{next_link}</div>{footer()}"""
    write(f"{a['slug']}/index.html", page(f"{a['slug']}: {a['line']}", f"{a['line']} {a['about']}", f"/{a['slug']}/", body))
    privacy = f"""<div class="page {cls}" style="{style}">{top(a)}<main class="legal"><h1>{a['slug']} privacy policy</h1><p>The full policy will be published here before the app launches.</p><p>Questions: <a href="mailto:{SITE['contact']}">{SITE['contact']}</a></p></main></div>{footer()}"""
    write(f"{a['slug']}/privacy/index.html", page(f"{a['slug']} privacy policy", f"Privacy policy for {a['slug']}.", f"/{a['slug']}/privacy/", privacy, index=False))


def extras():
    body = f'<main class="legal lost"><a href="/" aria-label="{SITE["name"]} home">{brand()}</a><h1>That page doesn\'t exist</h1><p><a href="/">See all apps</a></p></main>'
    write("404.html", page("Page not found", "Page not found.", "/404.html", body, index=False))
    write("CNAME", SITE["domain"] + "\n")
    write(".nojekyll", "")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    urls = ["/"] + [f"/{a['slug']}/" for a in APPS]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{BASE}{u}</loc></url>" for u in urls) + "</urlset>\n")


if __name__ == "__main__":
    check_images()
    home()
    for index, app in enumerate(APPS):
        app_page(app, index)
    extras()
    print(f"Built {len(APPS)} apps into {DOCS}")
