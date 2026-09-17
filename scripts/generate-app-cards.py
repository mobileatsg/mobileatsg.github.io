#!/usr/bin/env python3
"""Generate static /apps/{id}/ share cards from more-apps.json (OG-friendly HTML).

Usage (from website/):
  python3 scripts/generate-app-cards.py
  python3 scripts/generate-app-cards.py --write-share-urls   # also set shareUrl on each app
"""
from __future__ import annotations

import argparse
import html
import json
import re
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


def render_card(app: dict, publisher: dict) -> str:
    app_id = app["id"]
    name = app.get("name") or app_id
    blurb = app.get("blurb") or ""
    category = app.get("category") or ""
    tagline = app.get("tagline") or blurb
    icon = abs_url(app.get("ogImageUrl") or app.get("iconUrl") or "")
    share = abs_url(app.get("shareUrl") or f"/apps/{app_id}/")
    privacy = abs_url(app.get("privacyUrl") or f"/{app_id}/")
    ios, android = store_urls(app)
    support = publisher.get("supportEmail") or "mobileatsg@gmail.com"
    pub_name = publisher.get("name") or "Mobile@SG"
    zh = (app.get("locales") or {}).get("zh-Hans") or {}

    # Embed locale strings for client switcher
    payload = {
        "id": app_id,
        "en": {"name": name, "blurb": blurb, "category": category, "tagline": tagline},
        "zh-Hans": {
            "name": zh.get("name") or name,
            "blurb": zh.get("blurb") or blurb,
            "category": zh.get("category") or category,
            "tagline": zh.get("tagline") or zh.get("blurb") or tagline,
        },
        "iosUrl": ios,
        "androidUrl": android,
        "privacyUrl": privacy,
        "shareUrl": share,
    }
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    ios_btn = (
        f'<a class="btn btn-ios" id="btn-ios" href="{esc(ios)}">App Store</a>'
        if ios
        else ""
    )
    and_btn = (
        f'<a class="btn btn-play" id="btn-android" href="{esc(android)}">Google Play</a>'
        if android
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
  <meta property="og:image" content="{esc(icon)}" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{esc(name)}" />
  <meta name="twitter:description" content="{esc(blurb)}" />
  <meta name="twitter:image" content="{esc(icon)}" />
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
      --shadow: 0 16px 48px rgba(0,0,0,.35);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.55;
      color: var(--text);
      background:
        radial-gradient(900px 480px at 15% -10%, rgba(91,159,212,.16), transparent 55%),
        radial-gradient(700px 400px at 100% 0%, rgba(123,108,240,.1), transparent 50%),
        var(--bg);
    }}
    a {{ color: var(--link); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .wrap {{
      max-width: 440px;
      margin: 0 auto;
      padding: 2rem 1.25rem 3rem;
    }}
    .top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      font-size: .9rem;
    }}
    .brand {{
      display: flex; align-items: center; gap: .55rem;
      color: inherit; font-weight: 600;
    }}
    .brand img {{ width: 28px; height: 28px; border-radius: 8px; }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.75rem 1.4rem 1.5rem;
      box-shadow: var(--shadow);
      text-align: center;
    }}
    .icon {{
      width: 96px; height: 96px; border-radius: 22px;
      object-fit: cover; background: #fff;
      box-shadow: var(--shadow);
      margin: 0 auto 1.1rem;
      display: block;
    }}
    .chip {{
      display: inline-block;
      font-size: .75rem;
      color: var(--muted);
      background: #243044;
      border-radius: 999px;
      padding: .2rem .65rem;
      margin-bottom: .65rem;
    }}
    h1 {{
      margin: 0 0 .35rem;
      font-size: 1.55rem;
      letter-spacing: -.02em;
    }}
    .tagline {{
      margin: 0 0 1.25rem;
      color: var(--muted);
      font-size: .98rem;
    }}
    .btns {{
      display: flex; flex-direction: column; gap: .65rem;
      margin: 1.25rem 0 1rem;
    }}
    .btn {{
      display: block;
      padding: .85rem 1rem;
      border-radius: 12px;
      font-weight: 650;
      text-decoration: none !important;
      color: #fff !important;
    }}
    .btn-ios {{ background: #0a84ff; }}
    .btn-play {{ background: #3ddc84; color: #0b1a10 !important; }}
    .btn-stay {{
      background: transparent;
      border: 1px solid var(--border);
      color: var(--muted) !important;
      font-weight: 500;
      font-size: .9rem;
    }}
    .meta {{
      font-size: .85rem;
      color: var(--muted);
      margin-top: 1rem;
    }}
    .meta a {{ margin: 0 .35rem; }}
    .hint {{
      margin-top: 1rem;
      font-size: .8rem;
      color: var(--muted);
      min-height: 1.2em;
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
      <a href="/?lang=zh" id="lang-link" data-en="/apps/{esc(app_id)}/?lang=en" data-zh="/apps/{esc(app_id)}/?lang=zh">中文</a>
    </div>
    <article class="card">
      <img class="icon" src="{esc(icon)}" alt="{esc(name)} icon" width="96" height="96" />
      <div class="chip" id="el-category">{esc(category)}</div>
      <h1 id="el-name">{esc(name)}</h1>
      <p class="tagline" id="el-tagline">{esc(tagline)}</p>
      <div class="btns">
        {ios_btn}
        {and_btn}
        <a class="btn btn-stay" href="?stay=1" id="btn-stay">Stay on this page</a>
      </div>
      <p class="meta">
        <a href="{esc(privacy)}">Privacy</a>
        ·
        <a href="/">All apps</a>
        ·
        <a href="mailto:{esc(support)}">Support</a>
      </p>
      <p class="hint" id="hint"></p>
    </article>
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
    document.title = L.name + " — Mobile@SG";
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

  // Soft redirect on mobile (OG crawlers rarely look like phones; ?stay=1 disables).
  var url = targetUrl();
  var mobile = isIOS() || isAndroid();
  var force = go === "1" || go === "store" || go === "ios" || go === "android" || go === "apple" || go === "play";
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
