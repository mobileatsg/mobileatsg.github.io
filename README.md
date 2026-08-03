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
| `status` | object or string | **Per platform** (preferred) or legacy single string (see below) |
| `platforms` | `ios` \| `android`[] | Platforms this app ships on |
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

### `status` (per platform)

**Preferred** — configure iOS and Android independently:

```json
"status": {
  "ios": "InProcess",
  "android": "Published"
}
```

Example: Sudoku Mix Android live, iOS still shipping → Android store button only; iOS More apps on Android can still promote it; iOS More apps will **not** list it until `ios` is `Published`.

| Value | Meaning |
|-------|---------|
| **`Published`** | Live (or ready) on that store |
| **`InProcess`** | Building / not store-live on that platform |

Exact strings (case-sensitive). Omit a platform key if that platform is not in `platforms`.

**Legacy** (still accepted): `"status": "Published"` applies the same value to all listed platforms.

### Display policy (required)

| Surface | Which apps | Status UI |
|---------|------------|-----------|
| **Developer website** | All `enabled` apps | Per-platform chips (`iOS · Published`, `Android · In process`); store button only for platforms that are `Published` |
| **In-app More apps (iOS device)** | Only peers with **`status.ios === "Published"`** | Ignore `status.android` for the list; exclude self |
| **In-app More apps (Android device)** | Only peers with **`status.android === "Published"`** | Ignore `status.ios` for the list; exclude self |

**Required:** filter by **device platform**. Do not show an app because the *other* store is Published. Missing status for this platform ⇒ exclude.

### Client rules

1. Ignore entries with `enabled: false`.  
2. Sort by `sortOrder` ascending.  
3. **Website:** render every remaining app; badges + CTAs per platform status.  
4. **In-app More apps:**  
   - current platform status must be **`Published`**  
   - exclude current app (`bundleId` / `androidPackage`)  
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
