#!/usr/bin/env python3
"""Generates the static site in docs/ from apps.json and i18n/*.json.

python3 build.py            build every language
python3 build.py --extract  write i18n/source.json, the English strings to translate
"""
import json
import re
import sys
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
I18N = ROOT / "i18n"
DATA = json.loads((ROOT / "apps.json").read_text())
SITE, ALL_APPS = DATA["site"], DATA["apps"]
APPS = [a for a in ALL_APPS if not a.get("hidden")]  # hidden apps only get a privacy page
LANGS = SITE["languages"]
BASE = f"https://{SITE['domain']}"
FONTS = "https://fonts.googleapis.com/css2?family=Anton&family=Barlow+Condensed:wght@500;600&family=Geist:wght@400;500;700&display=swap"

LANG = "en"
TR = {}
SOURCE = {}


def T(text):
    if LANG == "en":
        SOURCE[text] = True
        return text
    return TR[text]


def url(path, lang=None):
    code = lang or LANG
    return path if code == "en" else f"/{code}{path}"


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


def load_translation(code):
    data = json.loads((I18N / f"{code}.json").read_text())
    problems = [f"missing: {k}" for k in SOURCE if not str(data.get(k, "")).strip()]
    holes = re.compile(r"\{\w+\}")
    problems += [f"placeholders differ: {k}" for k in SOURCE if k in data and sorted(holes.findall(k)) != sorted(holes.findall(data[k]))]
    if problems:
        sys.exit(f"{code}.json has problems:\n" + "\n".join(problems))
    return data


def page(title, desc, path, body, index=True, alternates=True, lang=None):
    code = lang or LANG
    robots = "" if index else '<meta name="robots" content="noindex">'
    alts = ""
    if alternates:
        alts = "".join(f'<link rel="alternate" hreflang="{x["code"]}" href="{BASE}{url(path, x["code"])}">' for x in LANGS)
        alts += f'<link rel="alternate" hreflang="x-default" href="{BASE}{path}">'
    canonical = BASE + url(path, code)
    return f"""<!doctype html>
<html lang="{code}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">{robots}
<link rel="canonical" href="{canonical}">{alts}<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canonical}"><meta property="og:type" content="website">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="{FONTS}"><link rel="stylesheet" href="/assets/site.css"><script src="/assets/site.js" defer></script></head>
<body>{body}</body></html>
"""


def write(rel, text):
    f = DOCS / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)


def out(rel):
    return rel if LANG == "en" else f"{LANG}/{rel}"


def scope(a):
    b = a["brand"]
    style = ";".join(f"--{k}:{v}" for k, v in [("bg", b["bg"]), ("fg", b["fg"]), ("mut", b["mut"]), ("pill-bg", b["pillBg"]), ("pill-fg", b["pillFg"]), ("store-bg", b["storeBg"]), ("store-fg", b["storeFg"])])
    cls = f"d-{b['display']} store-{b['storeStyle']}" + (" tex" if b["texture"] else "")
    return cls, style


def mark(a):
    return f'<span class="mark" translate="no">{e(a["name"])}<span class="pill">-ed</span></span>'


def brand():
    return '<span class="mark brandm" translate="no">factory<span class="pill">-ed</span></span>'


def shot(src, alt, lazy=True):
    load = ' loading="lazy"' if lazy else ""
    return f'<figure class="ph"><img src="{src}" alt="{e(alt)}"{load} decoding="async"></figure>'


def stores(a):
    play = f'<a class="store" href="{e(a["play"])}" rel="noopener">Google Play</a>' if a["play"] else f'<span class="soon strong">{e(T("Coming to Google Play"))}</span>'
    ios = f'<a class="store" href="{e(a["appStore"])}" rel="noopener">App Store</a>' if a["appStore"] else f'<span class="soon">{e(T("App Store later"))}</span>'
    return f'<div class="stores">{play}{ios}</div>'


def footer():
    links = "".join(f'<a href="/{a["slug"]}/privacy/">{e(T("{app} privacy").format(app=a["slug"]))}</a>' for a in APPS)
    note = ""
    if LANG != "en":
        note = f'<p class="draft">{e(T("Draft translation. Found a mistake?"))} <a href="mailto:{SITE["contact"]}">{e(T("Tell us"))}</a></p>'
    else:
        T("Draft translation. Found a mistake?")
        T("Tell us")
    return f'<footer class="foot"><span>© {SITE["year"]} {SITE["name"]}</span><nav aria-label="{e(T("Footer"))}">{links}<a href="mailto:{SITE["contact"]}">{e(T("Contact"))}</a></nav>{note}</footer>'


def language_menu(path, cls=""):
    now = next(x for x in LANGS if x["code"] == LANG)
    links = "".join(f'<a href="{url(path, x["code"])}" lang="{x["code"]}" hreflang="{x["code"]}" data-lang="{x["code"]}"{" aria-current=true" if x is now else ""}>{e(x["name"])}</a>' for x in LANGS)
    return f'<details class="menu {cls}"><summary aria-label="{e(T("Language"))}: {e(now["name"])}">{e(now["name"])}</summary><div>{links}</div></details>'


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
    link = url(f"/{a['slug']}/")
    return f"""<div class="wrap"><section class="row {cls}{alt}" style="{style}" aria-labelledby="r-{a['slug']}">
<div class="fw" aria-hidden="true"><div class="film">{film(a, eager=i == 0)}</div></div>
<div class="copy"><h2 id="r-{a['slug']}"><a href="{link}">{mark(a)}</a></h2><p>{e(T(a['line']))} {e(T(a['about']))}</p>{stores(a)}<a class="see" href="{link}">{e(T("See every feature"))}</a></div></section></div>"""


def home():
    stripes = "".join(f'<i style="background:{a["brand"]["stripe"]}"></i>' for a in APPS)
    names = ", ".join(a["slug"] for a in APPS)
    pause, play = T("Pause motion"), T("Play motion")
    body = f"""<div class="home-top"><header class="hero"><div class="sw" aria-hidden="true">{stripes}</div><div class="tx"><h1>{brand()}</h1><p translate="no" lang="en">{e(SITE['concept'])}</p><button id="motion" class="motion" aria-pressed="false" data-pause="{e(pause)}" data-play="{e(play)}">{e(pause)}</button></div></header>{language_menu("/", "home-lang")}</div>
<main>{''.join(row(a, i) for i, a in enumerate(APPS))}</main>{footer()}"""
    write(out("index.html"), page(f"{SITE['name']}: {SITE['concept']}", T("{site} makes small Android apps: {apps}.").format(site=SITE["name"], apps=names), "/", body))


def top(a, path=None):
    links = "".join(f'<a href="{url("/" + x["slug"] + "/")}"{" aria-current=page" if x is a else ""}><img src="{asset(x, "icon.svg")}" alt="" width="32" height="32">{x["slug"]}</a>' for x in APPS)
    apps = f'<details class="menu"><summary>{e(T("Apps"))}</summary><div>{links}<a class="all" href="{url("/")}">{e(T("All apps"))}</a></div></details>'
    lang = language_menu(path) if path else ""
    return f'<nav class="top" aria-label="{e(T("Main"))}"><a href="{url("/")}" aria-label="{SITE["name"]}">{brand()}</a><div class="navs">{lang}{apps}</div></nav>'


def feature(a, f):
    title = T(f["title"])
    pic = shot(asset(a, f["image"]), title) if f["image"] else f'<div class="ph noimg"><img src="{asset(a, "icon.svg")}" alt="" loading="lazy"></div>'
    return f'<article>{pic}<h3>{e(title)}</h3><p>{e(T(f["text"]))}</p></article>'


def themed_alt(a, name):
    return T("{app} in the {theme} theme").format(app=a["slug"], theme=name)


def media(a):
    poster = asset(a, a["hero"])
    if a["video"]:
        return f'<video class="ph" src="{e(a["video"])}" poster="{poster}" controls muted playsinline preload="none" aria-label="{e(T("{app} demo").format(app=a["slug"]))}"></video>'
    T("{app} demo")
    return shot(poster, themed_alt(a, a["defaultTheme"]), lazy=False)


def inline(text):
    """A line of the policy: links and bold, everything else escaped."""
    out = e(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    return re.sub(r"\[(.+?)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', out)


def markdown(text):
    """The small part of Markdown a policy in legal/ uses: ## headings, paragraphs, - lists and | tables. The # title is the page's own."""
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().split("\n")
        if lines[0].startswith("# "):
            continue
        if lines[0].startswith("## "):
            out.append(f"<h2>{inline(lines[0][3:])}</h2>")
        elif lines[0].startswith("- "):
            out.append("<ul>" + "".join(f"<li>{inline(l[2:])}</li>" for l in lines) + "</ul>")
        elif lines[0].startswith("|"):
            rows = [[inline(c.strip()) for c in l.strip().strip("|").split("|")] for l in lines if not re.fullmatch(r"\|[-| ]+\|", l.strip())]
            head = "".join(f"<th>{c}</th>" for c in rows[0])
            body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows[1:])
            out.append(f'<div class="table"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
        else:
            out.append(f"<p>{inline(' '.join(lines))}</p>")
    return "".join(out)


def app_page(a, i):
    cls, style = scope(a)
    nxt = APPS[(i + 1) % len(APPS)]
    ncls, nstyle = scope(nxt)
    path = f"/{a['slug']}/"
    groups = "".join(f'<section class="fs"><h2>{e(T(g["title"]))}</h2><div class="strip" tabindex="0" role="group" aria-label="{e(T(g["title"]))}">{"".join(feature(a, f) for f in g["features"])}</div></section>' for g in a["groups"])
    default = e(T("default"))
    themes = "".join(f'<figure>{shot(asset(a, t["image"]), themed_alt(a, t["name"]))}<figcaption translate="no">{e(t["name"])}{f" <em>{default}</em>" if t["name"] == a["defaultTheme"] else ""}</figcaption></figure>' for t in a["themes"])
    facts = "".join(f"<li>{e(T(x))}</li>" for x in a["facts"])
    heading = T("{n} themes").format(n=len(a["themes"]))
    next_link = "" if len(APPS) < 2 else f'<a class="nextapp {ncls}" style="{nstyle}" href="{url("/" + nxt["slug"] + "/")}"><small>{e(T("Next app"))}</small>{mark(nxt)}</a>'
    body = f"""<div class="page {cls}" style="{style}">{top(a, path)}<main><header class="hh">{media(a)}<div><h1>{mark(a)}</h1><p><b>{e(T(a['line']))}</b> {e(T(a['about']))}</p>{stores(a)}<ul class="facts">{facts}</ul></div></header>
{groups}<section class="fs"><h2>{e(heading)}</h2><div class="strip themes" tabindex="0" role="group" aria-label="{e(heading)}">{themes}</div></section></main>{next_link}</div>{footer()}"""
    write(out(f"{a['slug']}/index.html"), page(f"{a['slug']}: {T(a['line'])}", f"{T(a['line'])} {T(a['about'])}", path, body))


def english_only():
    for a in ALL_APPS:
        cls, style = scope(a)
        legal = ROOT / "legal" / f"{a['slug']}.md"
        policy = markdown(legal.read_text()) if legal.exists() else f"""<p>The full policy will be published here before the app launches.</p><p>Questions: <a href="mailto:{SITE['contact']}">{SITE['contact']}</a></p>"""
        privacy = f"""<div class="page {cls}" style="{style}">{top(a)}<main class="legal"><h1>{a['slug']} privacy policy</h1>{policy}</main></div>{footer()}"""
        write(f"{a['slug']}/privacy/index.html", page(f"{a['slug']} privacy policy", f"Privacy policy for {a['slug']}.", f"/{a['slug']}/privacy/", privacy, index=False, alternates=False))
    body = f'<main class="legal lost"><a href="/" aria-label="{SITE["name"]}">{brand()}</a><h1>That page doesn\'t exist</h1><p><a href="/">See all apps</a></p></main>'
    write("404.html", page("Page not found", "Page not found.", "/404.html", body, index=False, alternates=False))
    write("CNAME", SITE["domain"])
    write(".nojekyll", "")
    write("app-ads.txt", "google.com, pub-4928653890056064, DIRECT, f08c47fec0942fa0\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    paths = ["/"] + [f"/{a['slug']}/" for a in APPS]
    locs = "".join(f"<url><loc>{BASE}{url(p, x['code'])}</loc></url>" for p in paths for x in LANGS)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locs}</urlset>\n')


def build_language():
    home()
    for index, app in enumerate(APPS):
        app_page(app, index)


if __name__ == "__main__":
    check_images()
    build_language()
    english_only()
    if "--extract" in sys.argv:
        I18N.mkdir(exist_ok=True)
        (I18N / "source.json").write_text(json.dumps(list(SOURCE), ensure_ascii=False, indent=1) + "\n")
        print(f"Wrote {len(SOURCE)} strings to i18n/source.json")
        sys.exit()
    for language in LANGS:
        if language["code"] != "en":
            TR = load_translation(language["code"])
            LANG = language["code"]
            build_language()
    print(f"Built {len(APPS)} apps in {len(LANGS)} languages into {DOCS}")
