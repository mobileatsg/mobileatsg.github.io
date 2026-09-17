#!/usr/bin/env python3
"""Derive platform-filtered catalogs from more-apps.json (single source of truth).

Writes:
  more-apps-ios.json     — no Play fields; showInMobileApp != false
  more-apps-android.json — no App Store fields; showInMobileApp != false

Also used when Cloudflare Pages Functions are unavailable (e.g. GitHub Pages mirror).
Prefer these static URLs in AppConfig; ?platform= still works if Functions are enabled.
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "more-apps.json"


def strip(app: dict, platform: str) -> dict:
    out = deepcopy(app)
    if platform == "ios":
        out.pop("playStoreUrl", None)
        out.pop("androidPackage", None)
        if isinstance(out.get("platforms"), list):
            out["platforms"] = [p for p in out["platforms"] if p == "ios"]
        if isinstance(out.get("status"), dict):
            out["status"] = {k: v for k, v in out["status"].items() if k == "ios"}
    elif platform == "android":
        out.pop("appStoreUrl", None)
        out.pop("iosAppStoreId", None)
        if isinstance(out.get("platforms"), list):
            out["platforms"] = [p for p in out["platforms"] if p == "android"]
        if isinstance(out.get("status"), dict):
            out["status"] = {k: v for k, v in out["status"].items() if k == "android"}
    return out


def build(platform: str) -> dict:
    catalog = json.loads(SRC.read_text(encoding="utf-8"))
    apps = catalog.get("apps") or []
    catalog["apps"] = [
        strip(a, platform)
        for a in apps
        if a and a.get("showInMobileApp") is not False
    ]
    catalog["filteredFor"] = platform
    catalog["filteredAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    catalog["source"] = "more-apps.json"
    return catalog


def main() -> int:
    for platform, name in (("ios", "more-apps-ios.json"), ("android", "more-apps-android.json")):
        out = ROOT / name
        data = build(platform)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {name} ({len(data['apps'])} apps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
