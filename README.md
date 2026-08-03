# Mobile@SG website (apps list)

Static landing page for **https://mobileatsg.github.io/** — publisher identity + list of apps.

## Shared catalog (source of truth)

| URL (after deploy) | File |
|--------------------|------|
| `https://mobileatsg.github.io/more-apps.json` | [`more-apps.json`](./more-apps.json) |

**One JSON drives both:**

1. **Developer website** — `index.html` fetches and renders cards  
2. **In-app “More apps”** — Stock@SG (and other apps) fetch the same URL, filter out self, show list  

Do **not** duplicate the app list in HTML or hardcode full catalogs in binaries (except a small offline fallback).

### Contents

| Path | Role |
|------|------|
| `more-apps.json` | **Shared catalog** (website + apps) |
| `index.html` | Landing page (reads catalog) |
| `assets/brand/` | Mobile@SG logo |
| `assets/apps/` | Per-app icons (256×256) |

---

## Catalog contract (`more-apps.json`)

```json
{
  "schemaVersion": 1,
  "updatedAt": "YYYY-MM-DD",
  "publisher": {
    "name": "Mobile@SG",
    "website": "https://mobileatsg.github.io/",
    "supportEmail": "mobileatsg@gmail.com"
  },
  "policy": {
    "websiteShowStatuses": ["Published", "InProcess"],
    "inAppMoreAppsShowStatuses": ["Published"]
  },
  "apps": [ /* AppEntry */ ]
}
```

`policy` documents the filter rules; clients should still implement them even if they ignore the object.

### `AppEntry`

| Field | Type | Notes |
|-------|------|--------|
| `id` | string | Stable slug (`stocksg`, `sudoku`, …) |
| `name` | string | Display name |
| `blurb` | string | One short description |
| `category` | string | Chip label |
| `status` | `"Published"` \| `"InProcess"` | Store readiness (see below) |
| `platforms` | `ios` \| `android`[] | Store buttons / platform filter |
| `tags` | string[] | Extra chips (e.g. `No ads`) |
| `bundleId` | string \| null | iOS production bundle |
| `androidPackage` | string \| null | Play `applicationId` |
| `iosAppStoreId` | string \| null | Numeric App Store id when live |
| `playStoreUrl` | string \| null | Optional override |
| `appStoreUrl` | string \| null | Optional override |
| `privacyUrl` | string | `https://mobileatsg.github.io/{id}/` |
| `iconUrl` | string | Absolute icon URL (for apps) |
| `iconPath` | string | Relative path (for website) |
| `sortOrder` | number | Ascending |
| `enabled` | bool | `false` hides without deleting |
| `featured` | bool | Optional highlight / soft-promo pick |

### `status` values

| Value | Meaning |
|-------|---------|
| **`Published`** | Live (or ready) on store(s) |
| **`InProcess`** | Building / not store-live yet |

Exact strings (case-sensitive): `Published`, `InProcess`.  
If `status` is missing, treat as **`Published`**.

### Display policy (required)

| Surface | Which apps | Status UI |
|---------|------------|-----------|
| **Developer website** | **All** `enabled` apps (`Published` + `InProcess`) | Show status badge; store buttons only if `Published`; `InProcess` → “Coming soon” |
| **In-app More apps** | **Only** `status === "Published"` | No InProcess rows; also exclude the current app |

Do **not** show `InProcess` apps inside More apps (users cannot install them yet).  
The website is the full public roadmap; the app only cross-promotes store-ready titles.

### Client rules

1. Ignore entries with `enabled: false`.  
2. Sort by `sortOrder` ascending.  
3. **Website:** render every remaining app; respect status for CTAs/badges.  
4. **In-app More apps:**  
   - `status === "Published"` only  
   - exclude current app (`bundleId` / `androidPackage` == this install)  
5. Prefer `appStoreUrl` → else `iosAppStoreId` → else search / website.  
6. Prefer `playStoreUrl` → else package details URL.  
7. Load `iconUrl` over the network (cache on disk in apps).  
8. On network failure: last successful cache → bundled fallback (apps only).

### Canonical fetch URL

```text
https://mobileatsg.github.io/more-apps.json
```

Suggested app cache TTL: **12–24 hours** (still refresh when opening Settings / More apps if stale).

---

## Preview locally

`fetch(more-apps.json)` needs HTTP (not `file://`):

```bash
cd "/Users/chachean/Projects/Mobile@SG/website"
python3 -m http.server 8080
# open http://127.0.0.1:8080/
```

---

## Deploy to GitHub Pages

Target: **`mobileatsg/mobileatsg.github.io`**.

1. Copy **contents** of this `website/` folder to the **repo root**:
   - `index.html`
   - `more-apps.json`
   - `assets/…`
2. Keep privacy folders: `stocksg/`, `sudoku/`, `pixelcolor/`, `smartalarm/`, `mathbuddy/`, …  
3. Confirm:
   - https://mobileatsg.github.io/
   - https://mobileatsg.github.io/more-apps.json

---

## Adding a new app (no other app redeploy)

1. Add icon: `assets/apps/{id}.png` (256×256).  
2. Append an entry to **`more-apps.json`** (`enabled: true`).  
3. Deploy Pages.  
4. Fill `iosAppStoreId` / store URLs when listings go live (edit JSON only).  

In-app More apps and this website pick it up on next catalog fetch.

To pause: `"enabled": false` → redeploy JSON only.

---

## Identity (fixed)

| Field | Value |
|-------|--------|
| Developer | Mobile@SG |
| Support | mobileatsg@gmail.com |
| Site | https://mobileatsg.github.io/ |
| Catalog | https://mobileatsg.github.io/more-apps.json |
