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


def status_label(st: str | None) -> str:
    if st == "Published":
        return "Published"
    if st == "InProcess":
        return "Coming soon"
    return "—"


def render_card(app: dict, publisher: dict) -> str:
    app_id = app["id"]
    name = app.get("name") or app_id
    blurb = app.get("blurb") or ""
    category = app.get("category") or ""
    tagline = app.get("tagline") or blurb
    icon = abs_url(app.get("iconUrl") or "")
    feature = abs_url(
        app.get("featureGraphicUrl")
        or (f"/assets/apps/feature/{app_id}.png" if (ROOT / "assets" / "apps" / "feature" / f"{app_id}.png").exists() else None)
        or app.get("ogImageUrl")
    )
    # Prefer Play feature graphic (1024×500) for OG; fall back to app icon.
    og_image = feature if feature and feature != SITE + "/" else icon
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
        },
        "zh-Hans": {
            "name": zh.get("name") or name,
            "blurb": zh.get("blurb") or blurb,
            "category": zh.get("category") or category,
            "tagline": zh.get("tagline") or zh.get("blurb") or tagline,
            "highlights": zh_highlights,
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
        if not url:
            return ""
        label = "App Store" if kind == "ios" else "Google Play"
        cls = "btn btn-ios" if kind == "ios" else "btn btn-play"
        bid = "btn-ios" if kind == "ios" else "btn-android"
        badge = ""
        if st == "InProcess":
            badge = '<span class="btn-badge">Coming soon</span>'
        elif st == "Published":
            badge = '<span class="btn-badge on">Get</span>'
        # Always clickable when URL exists (even InProcess).
        return (
            f'<a class="{cls}" id="{bid}" href="{esc(url)}" rel="noopener noreferrer">'
            f"<span>{label}</span>{badge}</a>"
        )

    ios_btn = store_btn("ios", ios, ios_st)
    and_btn = store_btn("android", android, and_st)

    status_chips = []
    if ios_st:
        cls = "ok" if ios_st == "Published" else "soon"
        status_chips.append(
            f'<span class="status-chip {cls}">iOS · {esc(status_label(ios_st))}</span>'
        )
    if and_st:
        cls = "ok" if and_st == "Published" else "soon"
        status_chips.append(
            f'<span class="status-chip {cls}">Android · {esc(status_label(and_st))}</span>'
        )
    status_html = "".join(status_chips)

    hi_items = "".join(f"<li>{esc(h)}</li>" for h in highlights)
    highlights_block = (
        f'<section class="panel" aria-labelledby="features-title">'
        f'<h2 id="features-title">Highlights</h2>'
        f'<ul class="features" id="el-features">{hi_items}</ul>'
        f"</section>"
        if highlights
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
      --surface-2: #213044;
      --text: #e7ecf3;
      --muted: #9aa8b8;
      --accent: #5b9fd4;
      --border: #2a3648;
      --link: #7ec8ff;
      --ok: #6bcf8e;
      --soon: #e0b35c;
      --radius: 22px;
      --shadow: 0 18px 50px rgba(0,0,0,.38);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.55;
      color: var(--text);
      background:
        radial-gradient(1100px 560px at 12% -12%, rgba(91,159,212,.18), transparent 55%),
        radial-gradient(900px 480px at 100% 0%, rgba(123,108,240,.12), transparent 52%),
        var(--bg);
    }}
    a {{ color: var(--link); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .wrap {{
      width: min(960px, 100%);
      margin: 0 auto;
      padding: 1.5rem 1.25rem 3.5rem;
    }}
    .top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.5rem;
      font-size: .92rem;
    }}
    .brand {{
      display: flex; align-items: center; gap: .6rem;
      color: inherit; font-weight: 650;
    }}
    .brand img {{ width: 30px; height: 30px; border-radius: 8px; }}
    .banner {{
      display: block;
      width: 100%;
      aspect-ratio: 1024 / 500;
      object-fit: cover;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
      background: var(--surface);
      margin-bottom: 1.15rem;
    }}
    .hero {{
      display: grid;
      gap: 1.5rem;
      background: linear-gradient(180deg, rgba(33,48,68,.92), rgba(26,35,50,.98));
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.5rem;
      box-shadow: var(--shadow);
    }}
    @media (min-width: 800px) {{
      .hero {{
        grid-template-columns: 160px 1fr;
        align-items: start;
        gap: 2rem;
        padding: 2rem 2.1rem;
      }}
    }}
    .icon-wrap {{ text-align: center; }}
    @media (min-width: 800px) {{ .icon-wrap {{ text-align: left; }} }}
    .icon {{
      width: 112px; height: 112px; border-radius: 26px;
      object-fit: cover; background: #fff;
      box-shadow: var(--shadow);
    }}
    @media (min-width: 800px) {{
      .icon {{ width: 144px; height: 144px; border-radius: 32px; }}
    }}
    .chip {{
      display: inline-block;
      font-size: .78rem;
      color: var(--muted);
      background: #243044;
      border-radius: 999px;
      padding: .22rem .7rem;
      margin: 0 .35rem .55rem 0;
    }}
    .status-chip {{
      display: inline-block;
      font-size: .75rem;
      border-radius: 999px;
      padding: .22rem .7rem;
      margin: 0 .35rem .55rem 0;
      border: 1px solid var(--border);
      color: var(--muted);
    }}
    .status-chip.ok {{ color: var(--ok); border-color: rgba(107,207,142,.35); }}
    .status-chip.soon {{ color: var(--soon); border-color: rgba(224,179,92,.35); }}
    h1 {{
      margin: .15rem 0 .45rem;
      font-size: clamp(1.6rem, 3vw, 2.15rem);
      letter-spacing: -.02em;
      line-height: 1.15;
    }}
    .tagline {{
      margin: 0 0 1.1rem;
      color: var(--muted);
      font-size: 1.02rem;
      max-width: 38rem;
    }}
    .btns {{
      display: flex;
      flex-wrap: wrap;
      gap: .7rem;
      margin: 1rem 0 .35rem;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: .55rem;
      min-width: 148px;
      padding: .85rem 1.1rem;
      border-radius: 12px;
      font-weight: 650;
      text-decoration: none !important;
      color: #fff !important;
      transition: transform .12s ease, filter .12s ease;
    }}
    .btn:hover {{ filter: brightness(1.06); text-decoration: none !important; }}
    .btn:active {{ transform: translateY(1px); }}
    .btn-ios {{ background: #0a84ff; }}
    .btn-play {{ background: #3ddc84; color: #0b1a10 !important; }}
    .btn-badge {{
      font-size: .7rem;
      font-weight: 700;
      letter-spacing: .02em;
      padding: .15rem .45rem;
      border-radius: 999px;
      background: rgba(0,0,0,.18);
      color: inherit;
    }}
    .btn-badge.on {{ background: rgba(255,255,255,.22); }}
    .btn-stay {{
      background: transparent;
      border: 1px solid var(--border);
      color: var(--muted) !important;
      font-weight: 500;
      font-size: .9rem;
      min-width: auto;
    }}
    .grid {{
      display: grid;
      gap: 1rem;
      margin-top: 1.25rem;
    }}
    @media (min-width: 800px) {{
      .grid {{ grid-template-columns: 1.4fr .9fr; align-items: start; }}
    }}
    .panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 1.25rem 1.3rem 1.35rem;
    }}
    .panel h2 {{
      margin: 0 0 .85rem;
      font-size: 1.05rem;
      letter-spacing: -.01em;
    }}
    .features {{
      margin: 0;
      padding: 0;
      list-style: none;
    }}
    .features li {{
      position: relative;
      padding: .45rem 0 .45rem 1.35rem;
      color: var(--text);
      border-bottom: 1px solid rgba(42,54,72,.65);
      font-size: .95rem;
    }}
    .features li:last-child {{ border-bottom: 0; }}
    .features li::before {{
      content: "";
      position: absolute;
      left: 0; top: .85rem;
      width: .55rem; height: .55rem;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 0 3px rgba(91,159,212,.18);
    }}
    .side p {{
      margin: 0 0 .75rem;
      color: var(--muted);
      font-size: .92rem;
    }}
    .side .links a {{
      display: inline-block;
      margin: .15rem .75rem .15rem 0;
    }}
    .hint {{
      margin: .75rem 0 0;
      font-size: .82rem;
      color: var(--muted);
      min-height: 1.2em;
    }}
    footer.note {{
      margin-top: 1.5rem;
      text-align: center;
      color: var(--muted);
      font-size: .8rem;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <a class="brand" href="/">
        <img src="/assets/brand/mobileatsg-logo.png" alt="" width="30" height="30" />
        {esc(pub_name)}
      </a>
      <a href="/apps/{esc(app_id)}/?lang=zh" id="lang-link"
         data-en="/apps/{esc(app_id)}/?lang=en"
         data-zh="/apps/{esc(app_id)}/?lang=zh">中文</a>
    </div>

    {f'<img class="banner" src="{esc(feature)}" alt="{esc(name)} feature graphic" width="1024" height="500" />' if feature and feature != SITE + "/" and feature != icon else ""}
    <section class="hero">
      <div class="icon-wrap">
        <img class="icon" src="{esc(icon)}" alt="{esc(name)} icon" width="144" height="144" />
      </div>
      <div>
        <div>
          <span class="chip" id="el-category">{esc(category)}</span>
          {status_html}
        </div>
        <h1 id="el-name">{esc(name)}</h1>
        <p class="tagline" id="el-tagline">{esc(tagline)}</p>
        <div class="btns">
          {ios_btn}
          {and_btn}
          <a class="btn btn-stay" href="?stay=1" id="btn-stay">Stay on this page</a>
        </div>
        <p class="hint" id="hint"></p>
      </div>
    </section>

    <div class="grid">
      {highlights_block}
      <aside class="panel side">
        <h2>About</h2>
        <p id="el-blurb">{esc(blurb)}</p>
        <p>Published by <strong style="color:var(--text)">{esc(pub_name)}</strong>.</p>
        <div class="links">
          <a href="{esc(privacy)}">Privacy policy</a>
          <a href="/">All apps</a>
          <a href="mailto:{esc(support)}">Support</a>
        </div>
      </aside>
    </div>

    <footer class="note">App Store &amp; Google Play are trademarks of their respective owners.</footer>
  </div>
  <script type="application/json" id="app-data">{payload_json}</script>
  <script>
(function () {{
  var data = JSON.parse(document.getElementById("app-data").textContent);
  var params = new URLSearchParams(location.search);
  var stay = params.get("stay") === "1";
  var go = (params.get("go") || "").toLowerCase();
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
    document.title = L.name + " — Mobile@SG";
    var ul = document.getElementById("el-features");
    if (ul && L.highlights && L.highlights.length) {{
      ul.innerHTML = L.highlights.map(function (h) {{
        return "<li>" + h.replace(/[&<>\"']/g, function (c) {{
          return ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}})[c];
        }}) + "</li>";
      }}).join("");
    }}
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

  function isIOS() {{
    return /iPhone|iPad|iPod/i.test(navigator.userAgent) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  }}
  function isAndroid() {{ return /Android/i.test(navigator.userAgent); }}

  function targetUrl() {{
    if (go === "ios" || go === "apple") return data.iosUrl;
    if (go === "android" || go === "play") return data.androidUrl;
    if (go === "1" || go === "store") {{
      if (isIOS() && data.iosUrl) return data.iosUrl;
      if (isAndroid() && data.androidUrl) return data.androidUrl;
      return data.iosUrl || data.androidUrl;
    }}
    if (isIOS() && data.iosUrl) return data.iosUrl;
    if (isAndroid() && data.androidUrl) return data.androidUrl;
    return null;
  }}

  var url = targetUrl();
  var mobile = isIOS() || isAndroid();
  var force = go === "1" || go === "store" || go === "ios" || go === "android" || go === "apple" || go === "play";
  // Soft redirect on phones only (desktop stays on the responsive page).
  if (url && !stay && (mobile || force)) {{
    var hint = document.getElementById("hint");
    hint.textContent = locale === "zh-Hans" ? "正在打开商店…" : "Opening the store…";
    setTimeout(function () {{ location.replace(url); }}, force ? 200 : 1200);
  }}
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
