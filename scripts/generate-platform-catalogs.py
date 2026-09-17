#!/usr/bin/env python3
"""Derive lightweight platform catalogs from more-apps.json (single source of truth).

Writes slim files for in-app More apps only — no website/share/feature-graphic bloat:

  more-apps-ios.json
  more-apps-android.json

Filters:
  - showInMobileApp != false (missing ⇒ include)
  - strips other-store fields (Guideline 5.6 on iOS)

Edit more-apps.json only; re-run this script (and commit) after catalog changes.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "more-apps.json"

# Fields kept on each app entry for in-app More apps.
IOS_APP_KEYS = (
    "id",
    "name",
    "blurb",
    "category",
    "status",
    "platforms",
    "bundleId",
    "iosAppStoreId",
    "appStoreUrl",
    "iconUrl",
    "sortOrder",
    "enabled",
    "showInMobileApp",
    "featured",
    "hideInAppIds",
    "moreAppsExcludeIds",
    "locales",
)

ANDROID_APP_KEYS = (
    "id",
    "name",
    "blurb",
    "category",
    "status",
    "platforms",
    "androidPackage",
    "playStoreUrl",
    "iconUrl",
    "sortOrder",
    "enabled",
    "showInMobileApp",
    "featured",
    "hideInAppIds",
    "moreAppsExcludeIds",
    "locales",
)

# Locale copy: name/blurb/category only (drop highlights/tags for payload size).
LOCALE_KEYS = ("name", "blurb", "category")


def slim_locales(locales: dict | None) -> dict | None:
    if not isinstance(locales, dict):
        return None
    out: dict = {}
    for loc, copy in locales.items():
        if not isinstance(copy, dict):
            continue
        slim = {k: copy[k] for k in LOCALE_KEYS if k in copy and copy[k] not in (None, "", [])}
        if slim:
            out[loc] = slim
    return out or None


def slim_app(app: dict, platform: str) -> dict | None:
    if not app or app.get("showInMobileApp") is False:
        return None
    if app.get("enabled") is False:
        return None

    keys = IOS_APP_KEYS if platform == "ios" else ANDROID_APP_KEYS
    out: dict = {}
    for k in keys:
        if k not in app:
            continue
        if k == "locales":
            loc = slim_locales(app.get("locales"))
            if loc:
                out["locales"] = loc
            continue
        if k == "status" and isinstance(app.get("status"), dict):
            st = app["status"].get(platform)
            if st is not None:
                out["status"] = {platform: st}
            continue
        if k == "platforms" and isinstance(app.get("platforms"), list):
            plats = [p for p in app["platforms"] if p == platform]
            if plats:
                out["platforms"] = plats
            continue
        val = app[k]
        if val is None or val == "" or val == []:
            continue
        out[k] = val

    # Must have id + a store open path for this platform.
    if "id" not in out:
        return None
    if platform == "ios" and not (out.get("appStoreUrl") or out.get("iosAppStoreId")):
        return None
    if platform == "android" and not (out.get("playStoreUrl") or out.get("androidPackage")):
        return None
    return out


def build(platform: str) -> dict:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    apps = []
    for a in src.get("apps") or []:
        slim = slim_app(a, platform)
        if slim:
            apps.append(slim)
    apps.sort(key=lambda x: (x.get("sortOrder") is None, x.get("sortOrder") or 0, x.get("id") or ""))

    policy = src.get("policy") or {}
    return {
        "schemaVersion": src.get("schemaVersion", 1),
        "updatedAt": src.get("updatedAt"),
        "defaultLocale": src.get("defaultLocale", "en"),
        "supportedLocales": src.get("supportedLocales") or ["en", "zh-Hans"],
        "policy": {
            "inAppMoreAppsShowStatuses": policy.get("inAppMoreAppsShowStatuses") or ["Published"],
        },
        "filteredFor": platform,
        "filteredAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "more-apps.json",
        "apps": apps,
    }


def main() -> int:
    for platform, name in (("ios", "more-apps-ios.json"), ("android", "more-apps-android.json")):
        data = build(platform)
        path = ROOT / name
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
        # Pretty for git diffs is nicer for review — use compact for weight:
        # User asked lightweight → compact JSON.
        path.write_text(text, encoding="utf-8")
        src_size = SRC.stat().st_size
        print(f"wrote {name}: {len(data['apps'])} apps, {path.stat().st_size} bytes (source {src_size})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
