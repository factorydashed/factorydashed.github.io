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
FONTS = "https://fonts.googleapis.com/css2?family=Anton&family=Fraunces:ital,opsz,wght@0,9..144,500;1,9..144,500&family=Barlow+Condensed:wght@500;600&family=Geist:wght@400;500;700&display=swap"

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
    if b.get("heading") == "serif":
        cls += " h-serif"
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
    zoom = f'<div id="zoom-text" hidden data-close="{e(T("Close screenshot"))}" data-prev="{e(T("Previous screenshot"))}" data-next="{e(T("Next screenshot"))}" data-of="{e(T("{n} of {total}"))}"></div>'
    return zoom + f'<footer class="foot"><span>© {SITE["year"]} {SITE["name"]}</span><nav aria-label="{e(T("Footer"))}">{links}<a href="mailto:{SITE["contact"]}">{e(T("Contact"))}</a></nav>{note}</footer>'


def language_menu(path, cls=""):
    now = next(x for x in LANGS if x["code"] == LANG)
    links = "".join(f'<a href="{url(path, x["code"])}" lang="{x["code"]}" hreflang="{x["code"]}" data-lang="{x["code"]}"{" aria-current=true" if x is now else ""}>{e(x["name"])}</a>' for x in LANGS)
    return f'<details class="menu {cls}"><summary aria-label="{e(T("Language"))}: {e(now["name"])}">{e(now["name"])}</summary><div>{links}</div></details>'


def anchor(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def feature_count(a):
    return sum(len(g["features"]) for g in a["groups"])


def tile(a):
    cls, style = scope(a)
    images = [f["image"] for g in a["groups"] for f in g["features"] if f["image"]]
    back = next((x for x in images if x != a["hero"]), a["hero"])
    badge = f'<span class="new">{e(T("New"))}</span>' if a.get("new") else ""
    if LANG == "en":
        T("New")
    count = T("{n} features").format(n=feature_count(a))
    return f"""<a class="tile {cls}" style="{style}" href="{url('/' + a['slug'] + '/')}"><div class="trow"><img class="icon" src="{asset(a, 'icon.svg')}" alt="" width="48" height="48">{badge}</div><h2>{mark(a)}</h2><p>{e(T(a['line']))}</p><small>{e(count)}</small><figure class="ph two" aria-hidden="true"><img src="{asset(a, back)}" alt="" loading="lazy"></figure><figure class="ph one" aria-hidden="true"><img src="{asset(a, a['hero'])}" alt="" loading="lazy"></figure></a>"""


def home():
    stripes = "".join(f'<i style="background:{a["brand"]["stripe"]}"></i>' for a in APPS)
    names = ", ".join(a["slug"] for a in APPS)
    body = f"""<div class="home-top"><header class="hd"><div class="sw" aria-hidden="true">{stripes}</div><h1>{brand()}</h1><p translate="no" lang="en">{e(SITE['concept'])}</p></header>{language_menu("/", "home-lang")}</div>
<main class="shelf" aria-label="{e(T("Apps"))}">{''.join(tile(a) for a in APPS)}</main>{footer()}"""
    write(out("index.html"), page(f"{SITE['name']}: {SITE['concept']}", T("{site} makes small Android apps: {apps}.").format(site=SITE["name"], apps=names), "/", body))


def top(a, path=None):
    links = "".join(f'<a href="{url("/" + x["slug"] + "/")}"{" aria-current=page" if x is a else ""}><img src="{asset(x, "icon.svg")}" alt="" width="32" height="32">{x["slug"]}</a>' for x in APPS)
    apps = f'<details class="menu"><summary>{e(T("Apps"))}</summary><div>{links}<a class="all" href="{url("/")}">{e(T("All apps"))}</a></div></details>'
    lang = language_menu(path) if path else ""
    return f'<nav class="top" aria-label="{e(T("Main"))}"><a href="{url("/")}" aria-label="{SITE["name"]}">{brand()}</a><div class="navs">{lang}{apps}</div></nav>'


def picture(a, f, title):
    if f["image"]:
        return shot(asset(a, f["image"]), title)
    return f'<div class="ph noimg"><img src="{asset(a, "icon.svg")}" alt="" loading="lazy"></div>'


def card(a, f):
    title = T(f["title"])
    return f'<article class="card">{picture(a, f, title)}<h3>{e(title)}</h3><p>{e(T(f["text"]))}</p></article>'


def story_step(a, f, k):
    title = T(f["title"])
    mode = f'<span class="tag">{e(T(f["mode"]))}</span>' if f.get("mode") else ""
    quote = ""
    if f.get("quote"):
        side = "b" if k % 2 else "a"
        who = "Ben" if k % 2 else "Ana"
        quote = f'<blockquote class="q {side}"><small>{e(T("{name} says").format(name=who))}</small>{e(T(f["quote"]))}</blockquote>'
    return f"""<section class="step" id="s-{anchor(f['title'])}"><div><div class="num" aria-hidden="true">{f.get("n") or "·"}</div><h3>{e(title)}</h3>{mode}<p>{e(T(f.get("long") or f["text"]))}</p>{quote}</div>{picture(a, f, title)}</section>"""


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
    chips, sections = [], []
    for g in a["groups"]:
        gid = "g-" + anchor(g["title"])
        if g.get("story"):
            for f in g["features"]:
                num = f'<b>{f["n"]}</b>' if f.get("n") else ""
                chips.append(f'<li><a href="#s-{anchor(f["title"])}">{num}{e(T(f["title"]))}</a></li>')
            intro = g.get("intro") or {}
            head = f'<div class="intro"><h2>{e(T(intro.get("title") or g["title"]))}</h2>{f"<p>{e(T(intro["text"]))}</p>" if intro.get("text") else ""}</div>'
            steps = "".join(story_step(a, f, k) for k, f in enumerate(g["features"]))
            sections.append(f'<section class="grp story" id="{gid}">{head}{steps}</section>')
        else:
            chips.append(f'<li><a href="#{gid}">{e(T(g["title"]))}</a></li>')
            cards = "".join(card(a, f) for f in g["features"])
            sections.append(f'<section class="grp" id="{gid}"><h2>{e(T(g["title"]))}</h2><div class="cards">{cards}</div></section>')
    if len(a["themes"]) > 1:
        heading = T("{n} themes").format(n=len(a["themes"]))
        default = e(T("default"))
        figs = "".join(f'<figure>{shot(asset(a, t["image"]), themed_alt(a, t["name"]))}<figcaption translate="no">{e(t["name"])}{f" <em>{default}</em>" if t["name"] == a["defaultTheme"] else ""}</figcaption></figure>' for t in a["themes"])
        chips.append(f'<li><a href="#themes">{e(heading)}</a></li>')
        sections.append(f'<section class="grp" id="themes"><h2>{e(heading)}</h2><div class="themes">{figs}</div></section>')
    elif LANG == "en":
        T("{n} themes")
        T("default")
    if a.get("faq"):
        qa = "".join(f"<details><summary>{e(T(q))}</summary><p>{e(T(ans))}</p></details>" for q, ans in a["faq"])
        chips.append(f'<li><a href="#faq">{e(T("Questions"))}</a></li>')
        sections.append(f'<section class="grp faq" id="faq"><h2>{e(T("Questions"))}</h2>{qa}</section>')
    facts = "".join(f"<li>{e(T(x))}</li>" for x in a["facts"])
    bar = f'<nav class="bar" aria-label="{e(T("On this page"))}"><ol>{"".join(chips)}</ol></nav>'
    next_link = "" if len(APPS) < 2 else f'<a class="nextapp {ncls}" style="{nstyle}" href="{url("/" + nxt["slug"] + "/")}"><small>{e(T("Next app"))}</small>{mark(nxt)}</a>'
    body = f"""<div class="page {cls}" style="{style}">{top(a, path)}<main><header class="hh"><div><h1>{mark(a)}</h1><p class="lead">{e(T(a['line']))}</p><p>{e(T(a['about']))}</p>{stores(a)}<ul class="facts">{facts}</ul></div>{media(a)}</header>{bar}
{"".join(sections)}</main>{next_link}</div>{footer()}"""
    write(out(f"{a['slug']}/index.html"), page(f"{a['slug']}: {T(a['line'])}", f"{T(a['line'])} {T(a['about'])}", path, body))


OPEN_CSP = "default-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"
PLAY_CERTS = [
    "FC:02:31:0C:A8:E1:BC:47:59:B1:77:30:D5:A8:CE:73:22:5B:A4:57:71:00:2F:98:FE:B5:CB:5D:6E:CE:9A:88",  # Play app signing key
    "E2:E5:A8:C6:DC:85:99:82:43:91:25:5C:37:EC:52:B6:7B:09:33:FE:D7:70:24:95:69:C8:35:27:38:02:99:47",  # debug key, public
]


def open_page(a):
    """The page a shared link opens: English only, no fonts, no network, the payload stays in the browser."""
    cls, style = scope(a)
    get = a["play"] or f"/{a['slug']}/"
    body = f"""<div class="page {cls}" style="{style}">{top(a)}<main class="legal open"><h1>Open in {a['slug']}</h1>
<p id="msg">Someone shared a page of counters with you. Open it in {a['slug']}, or get the app first.</p>
<div class="stores"><a id="go" class="store" href="#" hidden>Open in {a['slug']}</a><a class="store" href="{e(get)}">Get {a['slug']}</a></div>
<noscript><p>This page needs JavaScript to open the link.</p></noscript></main></div>{footer()}
<style>.open .stores{{justify-content:flex-start;margin-top:22px}}.open [hidden]{{display:none}}.open .store{{text-decoration:none}}</style>
<script>(function(){{var h=location.hash.slice(1),go=document.getElementById("go");
if(h.length&&h.length<=8000&&/^[A-Za-z0-9_-]+$/.test(h)){{go.href="counted://t#"+h;go.hidden=false}}
else document.getElementById("msg").textContent="This link has no page in it."}})()</script>"""
    head = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{OPEN_CSP}"><meta name="robots" content="noindex"><meta name="referrer" content="no-referrer">
<title>Open in {a['slug']}</title><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css"></head>
<body>{body}</body></html>
"""
    write(f"{a['slug']}/open/index.html", head)
    links = [{"relation": ["delegate_permission/common.handle_all_urls"], "target": {"namespace": "android_app", "package_name": "com.factorydashed.counted", "sha256_cert_fingerprints": PLAY_CERTS}}]
    write(".well-known/assetlinks.json", json.dumps(links, indent=2) + "\n")


def english_only():
    for a in ALL_APPS:
        cls, style = scope(a)
        legal = ROOT / "legal" / f"{a['slug']}.md"
        policy = markdown(legal.read_text()) if legal.exists() else f"""<p>The full policy will be published here before the app launches.</p><p>Questions: <a href="mailto:{SITE['contact']}">{SITE['contact']}</a></p>"""
        privacy = f"""<div class="page {cls}" style="{style}">{top(a)}<main class="legal"><h1>{a['slug']} privacy policy</h1>{policy}</main></div>{footer()}"""
        write(f"{a['slug']}/privacy/index.html", page(f"{a['slug']} privacy policy", f"Privacy policy for {a['slug']}.", f"/{a['slug']}/privacy/", privacy, index=False, alternates=False))
    open_page(next(a for a in APPS if a["slug"] == "count-ed"))
    body = f'<main class="legal lost"><a href="/" aria-label="{SITE["name"]}">{brand()}</a><h1>That page doesn\'t exist</h1><p><a href="/">See all apps</a></p></main>'
    write("404.html", page("Page not found", "Page not found.", "/404.html", body, index=False, alternates=False))
    write("CNAME", SITE["domain"])
    write(".nojekyll", "")
    write("app-ads.txt", "google.com, pub-4928653890056064, DIRECT, f08c47fec0942fa0\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /count-ed/open/\nSitemap: {BASE}/sitemap.xml\n")
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
