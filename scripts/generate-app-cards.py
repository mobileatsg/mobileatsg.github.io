#!/usr/bin/env python3
"""Generate static /apps/{id}/ share cards from more-apps.json (OG-friendly HTML).

Usage (from website/):
  python3 scripts/generate-app-cards.py
  python3 scripts/generate-app-cards.py --write-share-urls
"""
from __future__ import annotations

import argparse
import html
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "more-apps.json"
APPS_DIR = ROOT / "apps"
SITE = "https://mobilesg.org"

# Simple brand marks (inline SVG) — Binance-style download pills.
APPLE_SVG = """<svg class="store-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M16.37 12.29c-.03-2.34 1.91-3.46 2-3.51-1.09-1.59-2.78-1.81-3.38-1.83-1.44-.15-2.81.85-3.54.85-.73 0-1.86-.83-3.06-.81-1.57.02-3.02.92-3.83 2.33-1.64 2.84-.42 7.04 1.17 9.35.78 1.13 1.71 2.4 2.93 2.35 1.18-.05 1.62-.76 3.04-.76 1.41 0 1.81.76 3.05.74 1.26-.02 2.06-1.15 2.83-2.29.89-1.3 1.26-2.56 1.28-2.62-.03-.01-2.45-.94-2.49-3.8zM14.2 5.48c.65-.79 1.09-1.88.97-2.97-0.94.04-2.08.63-2.75 1.42-.6.7-1.13 1.82-.99 2.89 1.05.08 2.12-.53 2.77-1.34z"/></svg>"""

GOOGLE_SVG = """<svg class="store-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="#EA4335" d="M3.6 2.2 13.3 12 3.6 21.8A2.1 2.1 0 0 1 3 20.1V3.9c0-.7.2-1.3.6-1.7z"/><path fill="#FBBC04" d="m13.3 12 2.7-2.7 4.2 2.4c.7.4.7 1.5 0 1.9l-4.2 2.4L13.3 12z"/><path fill="#4285F4" d="M13.3 12 3.6 2.2A2.3 2.3 0 0 1 5.1 2l11.2 6.5L13.3 12z"/><path fill="#34A853" d="M13.3 12 16.3 15.5 5.1 22a2.3 2.3 0 0 1-1.5-.2L13.3 12z"/></svg>"""


def esc(s: str | None) -> str:
    return html.escape(s or "", quote=True)


def abs_url(path_or_url: str | None) -> str:
    if not path_or_url:
        return SITE + "/"
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    if not path_or_url.startswith("/"):
        path_or_url = "/" + path_or_url
    return SITE + path_or_url


def store_urls(app: dict) -> tuple[str | None, str | None]:
    ios = app.get("appStoreUrl") or (
        f"https://apps.apple.com/sg/app/id{app['iosAppStoreId']}"
        if app.get("iosAppStoreId")
        else None
    )
    android = app.get("playStoreUrl") or (
        f"https://play.google.com/store/apps/details?id={app['androidPackage']}"
        if app.get("androidPackage")
        else None
    )
    return ios, android


def render_card(app: dict, publisher: dict) -> str:
    app_id = app["id"]
    name = app.get("name") or app_id
    blurb = app.get("blurb") or ""
    category = app.get("category") or ""
    tagline = app.get("tagline") or blurb
    icon = abs_url(app.get("iconUrl") or "")
    feature_path = ROOT / "assets" / "apps" / "feature" / f"{app_id}.png"
    feature = abs_url(
        app.get("featureGraphicUrl")
        or (f"/assets/apps/feature/{app_id}.png" if feature_path.exists() else None)
    )
    og_image = feature if feature != SITE + "/" else icon
    share = abs_url(app.get("shareUrl") or f"/apps/{app_id}/")
    privacy = abs_url(app.get("privacyUrl") or f"/{app_id}/")
    ios, android = store_urls(app)
    support = publisher.get("supportEmail") or "mobileatsg@gmail.com"
    pub_name = publisher.get("name") or "Mobile@SG"
    zh = (app.get("locales") or {}).get("zh-Hans") or {}
    status = app.get("status") or {}
    platforms = app.get("platforms") or []
    highlights = app.get("highlights") or []
    zh_highlights = zh.get("highlights") or highlights

    ios_st = status.get("ios") if "ios" in platforms else None
    and_st = status.get("android") if "android" in platforms else None

    payload = {
        "id": app_id,
        "en": {
            "name": name,
            "blurb": blurb,
            "category": category,
            "tagline": tagline,
            "highlights": highlights,
            "featuresTitle": "Highlights",
            "aboutTitle": "About",
            "publishedBy": "Published by",
            "privacy": "Privacy policy",
            "allApps": "All apps",
            "support": "Support",
            "comingSoon": "Coming soon",
            "downloadOn": "Download on the",
            "getItOn": "Get it on",
            "opening": "Opening the store…",
        },
        "zh-Hans": {
            "name": zh.get("name") or name,
            "blurb": zh.get("blurb") or blurb,
            "category": zh.get("category") or category,
            "tagline": zh.get("tagline") or zh.get("blurb") or tagline,
            "highlights": zh_highlights,
            "featuresTitle": "亮点",
            "aboutTitle": "关于",
            "publishedBy": "出品方",
            "privacy": "隐私政策",
            "allApps": "全部应用",
            "support": "支持",
            "comingSoon": "即将推出",
            "downloadOn": "下载自",
            "getItOn": "获取于",
            "opening": "正在打开商店…",
        },
        "iosUrl": ios,
        "androidUrl": android,
        "privacyUrl": privacy,
        "shareUrl": share,
        "iosStatus": ios_st,
        "androidStatus": and_st,
    }
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    def store_btn(kind: str, url: str | None, st: str | None) -> str:
        # Hide when platform not available.
        if st is None:
            return ""
        is_ios = kind == "ios"
        ico = APPLE_SVG if is_ios else GOOGLE_SVG
        store_name = "App Store" if is_ios else "Google Play"
        top = "Download on the" if is_ios else "Get it on"
        bid = "btn-ios" if is_ios else "btn-android"
        cls = "store-btn store-ios" if is_ios else "store-btn store-play"

        if st == "Published" and url:
            return (
                f'<a class="{cls}" id="{bid}" href="{esc(url)}" rel="noopener noreferrer">'
                f"{ico}"
                f'<span class="store-text"><span class="store-top" data-i18n-top>{top}</span>'
                f'<span class="store-name">{store_name}</span></span></a>'
            )
        # InProcess (or Published without URL): disabled Coming soon — not a store link.
        return (
            f'<span class="{cls} is-soon" id="{bid}" aria-disabled="true">'
            f"{ico}"
            f'<span class="store-text"><span class="store-top">{store_name}</span>'
            f'<span class="store-name" data-i18n-soon>Coming soon</span></span></span>'
        )

    ios_btn = store_btn("ios", ios, ios_st)
    and_btn = store_btn("android", android, and_st)

    hi_items = "".join(f"<li>{esc(h)}</li>" for h in highlights)
    highlights_block = (
        f'<section class="panel highlights" aria-labelledby="features-title">'
        f'<h2 id="features-title">Highlights</h2>'
        f'<ul class="features" id="el-features">{hi_items}</ul>'
        f"</section>"
        if highlights
        else ""
    )

    banner = (
        f'<div class="banner-wrap">'
        f'<img class="banner" src="{esc(feature)}" alt="" width="1024" height="500" />'
        f"</div>"
        if feature != SITE + "/"
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(name)} — {esc(pub_name)}</title>
  <meta name="description" content="{esc(blurb)}" />
  <meta name="author" content="{esc(pub_name)}" />
  <link rel="canonical" href="{esc(share)}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{esc(pub_name)}" />
  <meta property="og:title" content="{esc(name)}" />
  <meta property="og:description" content="{esc(blurb)}" />
  <meta property="og:url" content="{esc(share)}" />
  <meta property="og:image" content="{esc(og_image)}" />
  <meta property="og:image:width" content="1024" />
  <meta property="og:image:height" content="500" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(name)}" />
  <meta name="twitter:description" content="{esc(blurb)}" />
  <meta name="twitter:image" content="{esc(og_image)}" />
  <meta name="theme-color" content="#0f1419" />
  <link rel="icon" href="/assets/brand/mobileatsg-logo.png" type="image/png" />
  <style>
    :root {{
      --bg: #0f1419;
      --surface: #1a2332;
      --text: #e7ecf3;
      --muted: #9aa8b8;
      --accent: #5b9fd4;
      --border: #2a3648;
      --link: #7ec8ff;
      --radius: 20px;
      --shadow: 0 14px 40px rgba(0,0,0,.35);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.55;
      color: var(--text);
      background:
        radial-gradient(1000px 520px at 12% -12%, rgba(91,159,212,.16), transparent 55%),
        radial-gradient(800px 420px at 100% 0%, rgba(123,108,240,.1), transparent 50%),
        var(--bg);
    }}
    a {{ color: var(--link); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .wrap {{
      width: min(880px, 100%);
      margin: 0 auto;
      padding: 1.35rem 1.2rem 3rem;
    }}
    .top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.15rem;
      font-size: .9rem;
    }}
    .brand {{
      display: flex; align-items: center; gap: .55rem;
      color: inherit; font-weight: 650;
    }}
    .brand img {{ width: 28px; height: 28px; border-radius: 8px; }}

    /* Full graphic, natural 1024×500 aspect — no crop / zoom */
    .banner-wrap {{
      margin-bottom: 1.1rem;
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
      background: #0b0e11;
      line-height: 0;
    }}
    .banner {{
      display: block;
      width: 100%;
      height: auto;
      aspect-ratio: 1024 / 500;
      object-fit: contain;
      object-position: center;
    }}

    .hero {{
      display: grid;
      gap: 1.15rem;
      background: linear-gradient(180deg, rgba(33,48,68,.92), rgba(26,35,50,.98));
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem 1.25rem 1.35rem;
      box-shadow: var(--shadow);
    }}
    @media (min-width: 800px) {{
      .hero {{
        grid-template-columns: 120px 1fr;
        align-items: center;
        gap: 1.5rem;
        padding: 1.5rem 1.75rem;
      }}
    }}
    .icon-wrap {{ text-align: center; }}
    @media (min-width: 800px) {{ .icon-wrap {{ text-align: left; }} }}
    .icon {{
      width: 96px; height: 96px; border-radius: 22px;
      object-fit: cover; background: #fff;
      box-shadow: var(--shadow);
    }}
    @media (min-width: 800px) {{
      .icon {{ width: 112px; height: 112px; border-radius: 26px; }}
    }}
    .chip {{
      display: inline-block;
      font-size: .75rem;
      color: var(--muted);
      background: #243044;
      border-radius: 999px;
      padding: .2rem .65rem;
      margin: 0 .3rem .5rem 0;
    }}
    h1 {{
      margin: .1rem 0 .4rem;
      font-size: clamp(1.45rem, 2.6vw, 1.95rem);
      letter-spacing: -.02em;
      line-height: 1.15;
    }}
    .tagline {{
      margin: 0 0 1rem;
      color: var(--muted);
      font-size: .98rem;
      max-width: 36rem;
    }}

    /* Binance-like store pills */
    .btns {{
      display: flex;
      flex-wrap: wrap;
      gap: .65rem;
    }}
    .store-btn {{
      display: inline-flex;
      align-items: center;
      gap: .7rem;
      min-width: 168px;
      padding: .55rem 1rem .55rem .85rem;
      border-radius: 10px;
      background: #0b0e11;
      border: 1px solid #2b3139;
      color: #fff !important;
      text-decoration: none !important;
      transition: background .15s ease, border-color .15s ease, transform .1s ease;
    }}
    a.store-btn:hover {{
      background: #141920;
      border-color: #3a424d;
      text-decoration: none !important;
    }}
    a.store-btn:active {{ transform: translateY(1px); }}
    .store-btn.is-soon {{
      opacity: .72;
      cursor: default;
      background: #151a21;
    }}
    .store-ico {{
      width: 26px;
      height: 26px;
      flex: 0 0 auto;
    }}
    .store-text {{
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      line-height: 1.15;
    }}
    .store-top {{
      font-size: .68rem;
      color: #b7bdc6;
      font-weight: 500;
    }}
    .store-name {{
      font-size: 1.02rem;
      font-weight: 700;
      letter-spacing: -.01em;
    }}
    .btn-stay {{
      display: inline-flex;
      align-items: center;
      padding: .65rem .9rem;
      border-radius: 10px;
      border: 1px solid var(--border);
      color: var(--muted) !important;
      font-size: .88rem;
      font-weight: 500;
      text-decoration: none !important;
    }}
    .hint {{
      margin: .7rem 0 0;
      font-size: .8rem;
      color: var(--muted);
      min-height: 1.1em;
    }}

    /* Highlights directly under hero */
    .highlights {{
      margin-top: 1.1rem;
    }}
    .panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.15rem 1.2rem 1.25rem;
    }}
    .panel h2 {{
      margin: 0 0 .75rem;
      font-size: 1rem;
      letter-spacing: -.01em;
    }}
    .features {{
      margin: 0;
      padding: 0;
      list-style: none;
    }}
    .features li {{
      position: relative;
      padding: .55rem 0 .55rem 1.25rem;
      border-bottom: 1px solid rgba(42,54,72,.55);
      font-size: .92rem;
      /* One highlight per row (no multi-column wrap). */
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    @media (max-width: 640px) {{
      .features li {{
        white-space: normal;
      }}
    }}
    .features li::before {{
      content: "";
      position: absolute;
      left: 0; top: .9rem;
      width: .45rem; height: .45rem;
      border-radius: 50%;
      background: var(--accent);
    }}

    .about {{
      margin-top: 1rem;
      color: var(--muted);
      font-size: .9rem;
    }}
    .about strong {{ color: var(--text); }}
    .about .links a {{ margin-right: .85rem; }}
    footer.note {{
      margin-top: 1.5rem;
      text-align: center;
      color: var(--muted);
      font-size: .78rem;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <a class="brand" href="/">
        <img src="/assets/brand/mobileatsg-logo.png" alt="" width="28" height="28" />
        {esc(pub_name)}
      </a>
      <a href="/apps/{esc(app_id)}/?lang=zh" id="lang-link"
         data-en="/apps/{esc(app_id)}/?lang=en"
         data-zh="/apps/{esc(app_id)}/?lang=zh">中文</a>
    </div>

    {banner}

    <section class="hero">
      <div class="icon-wrap">
        <img class="icon" src="{esc(icon)}" alt="{esc(name)} icon" width="112" height="112" />
      </div>
      <div>
        <span class="chip" id="el-category">{esc(category)}</span>
        <h1 id="el-name">{esc(name)}</h1>
        <p class="tagline" id="el-tagline">{esc(tagline)}</p>
        <div class="btns">
          {ios_btn}
          {and_btn}
        </div>
      </div>
    </section>

    {highlights_block}

    <section class="panel about" aria-labelledby="about-title">
      <h2 id="about-title">About</h2>
      <p id="el-blurb">{esc(blurb)}</p>
      <p><span id="el-published-by">Published by</span> <strong>{esc(pub_name)}</strong>.</p>
      <p class="links">
        <a id="el-privacy" href="{esc(privacy)}">Privacy policy</a>
        <a id="el-all-apps" href="/">All apps</a>
        <a id="el-support" href="mailto:{esc(support)}">Support</a>
      </p>
    </section>

    <footer class="note">App Store &amp; Google Play are trademarks of their respective owners.</footer>
  </div>
  <script type="application/json" id="app-data">{payload_json}</script>
  <script>
(function () {{
  var data = JSON.parse(document.getElementById("app-data").textContent);
  var params = new URLSearchParams(location.search);
  var langParam = (params.get("lang") || "").toLowerCase();
  var locale = (langParam === "zh" || langParam.indexOf("zh") === 0) ? "zh-Hans" : "en";
  if (!langParam && /zh/i.test(navigator.language || "")) locale = "zh-Hans";

  function applyLocale(loc) {{
    var L = data[loc] || data.en;
    document.getElementById("el-name").textContent = L.name;
    document.getElementById("el-tagline").textContent = L.tagline || L.blurb;
    document.getElementById("el-category").textContent = L.category;
    var blurb = document.getElementById("el-blurb");
    if (blurb) blurb.textContent = L.blurb;
    var ft = document.getElementById("features-title");
    if (ft && L.featuresTitle) ft.textContent = L.featuresTitle;
    var at = document.getElementById("about-title");
    if (at && L.aboutTitle) at.textContent = L.aboutTitle;
    var pub = document.getElementById("el-published-by");
    if (pub) pub.textContent = L.publishedBy || "Published by";
    var priv = document.getElementById("el-privacy");
    if (priv) priv.textContent = L.privacy || "Privacy policy";
    var all = document.getElementById("el-all-apps");
    if (all) all.textContent = L.allApps || "All apps";
    var sup = document.getElementById("el-support");
    if (sup) sup.textContent = L.support || "Support";
    document.title = L.name + " — Mobile@SG";
    var ul = document.getElementById("el-features");
    if (ul && L.highlights && L.highlights.length) {{
      ul.innerHTML = L.highlights.map(function (h) {{
        return "<li>" + String(h).replace(/[&<>\"']/g, function (c) {{
          return ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}})[c];
        }}) + "</li>";
      }}).join("");
    }}
    document.querySelectorAll("[data-i18n-soon]").forEach(function (el) {{
      el.textContent = L.comingSoon || "Coming soon";
    }});
    document.querySelectorAll("[data-i18n-top]").forEach(function (el) {{
      var btn = el.closest(".store-btn");
      if (!btn || btn.classList.contains("is-soon")) return;
      el.textContent = btn.classList.contains("store-ios")
        ? (L.downloadOn || "Download on the")
        : (L.getItOn || "Get it on");
    }});
    var link = document.getElementById("lang-link");
    if (loc === "zh-Hans") {{
      link.textContent = "EN";
      link.href = link.getAttribute("data-en");
    }} else {{
      link.textContent = "中文";
      link.href = link.getAttribute("data-zh");
    }}
  }}
  applyLocale(locale);

  // No auto-redirect — user taps App Store / Google Play.
}})();
  </script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--write-share-urls",
        action="store_true",
        help="Set shareUrl=/apps/{id}/ on each enabled app and bump updatedAt",
    )
    args = ap.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    publisher = catalog.get("publisher") or {}
    apps = catalog.get("apps") or []
    changed = False

    APPS_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for app in apps:
        if not app.get("enabled", True):
            continue
        app_id = app["id"]
        share = f"/apps/{app_id}/"
        if args.write_share_urls and app.get("shareUrl") != share:
            app["shareUrl"] = share
            changed = True
        if not app.get("shareUrl"):
            app["shareUrl"] = share
            changed = True

        out_dir = APPS_DIR / app_id
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(
            render_card(app, publisher), encoding="utf-8"
        )
        written += 1
        print(f"wrote apps/{app_id}/index.html")

    if changed:
        catalog["updatedAt"] = date.today().isoformat()
        CATALOG.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"updated {CATALOG.name} shareUrl fields")

    print(f"done: {written} cards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
