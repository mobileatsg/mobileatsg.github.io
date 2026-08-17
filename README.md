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
  "defaultLocale": "en",
  "supportedLocales": ["en", "zh-Hans"],
  "publisher": { ... },
  "policy": { ... },
  "apps": [ /* AppEntry */ ]
}
```

`policy` documents the filter rules; clients should still implement them even if they ignore the object.

### Locales (English + Simplified Chinese only)

| Locale | Meaning |
|--------|---------|
| `en` | English — **default** top-level `name` / `blurb` / `category` / `tags` |
| `zh-Hans` | 简体中文 |

**Do not** add `zh-Hant` (Traditional Chinese) to this catalog.

```json
{
  "name": "Sudoku Mix",
  "blurb": "Colorful Sudoku…",
  "category": "Games · Puzzle",
  "tags": [],
  "locales": {
    "zh-Hans": {
      "name": "数独混合",
      "blurb": "多彩数独…",
      "category": "游戏 · 益智",
      "tags": []
    }
  }
}
```

**Resolve (website + in-app):**

```text
locale = en | zh-Hans
if locale == zh-Hans and app.locales["zh-Hans"][field] present → use it
else → top-level English field
```

Website language (priority):

1. **URL** — `?lang=zh` or `?lang=zh-Hans` (English: `?lang=en`)  
2. **Last choice** — `localStorage` (EN / 中文 switcher)  
3. **Browser** — any `zh*` → 简体  

Examples:

```text
https://mobileatsg.github.io/?lang=zh
https://mobileatsg.github.io/?lang=zh-Hans
https://mobileatsg.github.io/?lang=en
```

In-app: use the app’s UI language (`en` / `zh-Hans` only for this catalog).

### `AppEntry`

| Field | Type | Notes |
|-------|------|--------|
| `id` | string | Stable slug (`stocksg`, `sudoku`, …) |
| `name` | string | Display name (**English** default) |
| `blurb` | string | One short description (**English**) |
| `category` | string | Chip label (**English**) |
| `locales` | object | Optional `zh-Hans` overrides for `name`, `blurb`, `category`, `tags` |
| `status` | object or string | **Per platform** (preferred) or legacy single string (see below) |
| `platforms` | `ios` \| `android`[] | Platforms this app ships on |
| `tags` | string[] | Extra chips (e.g. `No ads`) — English default |
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

### Exclusion lists (in-app More apps only)

| Field | On | Meaning |
|-------|-----|---------|
| `hideInAppIds` | Peer (e.g. Stock@SG) | Hide this peer inside these host app `id`s |
| `moreAppsExcludeIds` | Host (e.g. Math Buddy) | Host never lists these peer `id`s |

Example: Stock@SG not for kids → `"hideInAppIds": ["mathbuddy"]` and/or Math Buddy `"moreAppsExcludeIds": ["stocksg"]`.  
**Website ignores exclusions.**

### Client rules

1. Ignore entries with `enabled: false`.  
2. Sort by `sortOrder` ascending.  
3. **Website:** render every remaining app; badges + CTAs per platform status (**no** exclusion filter).  
4. **In-app More apps:**  
   - current platform status must be **`Published`**  
   - exclude current app (`bundleId` / `androidPackage`)  
   - apply `hideInAppIds` / `moreAppsExcludeIds`  
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

## Privacy policies (same repo — no extra Pages project)

Each app’s live policy is **`{slug}/index.html`** in **this** folder. One public site, one repo (`mobileatsg/mobileatsg.github.io`).

| Slug folder | Public URL |
|-------------|------------|
| `sudoku/` | https://mobileatsg.github.io/sudoku/ |
| `sudokumix/` | Redirect → `/sudoku/` |
| `pixelcolor/` | https://mobileatsg.github.io/pixelcolor/ |
| `smartalarm/` | https://mobileatsg.github.io/smartalarm/ |
| `mathbuddy/` | https://mobileatsg.github.io/mathbuddy/ |
| `parksg/` | https://mobileatsg.github.io/parksg/ |
| `totomatch/` | https://mobileatsg.github.io/totomatch/ |
| `stocksg/` | https://mobileatsg.github.io/stocksg/ |
| `stocksg/eula/` | https://mobileatsg.github.io/stocksg/eula/ |

`/generate-privacy-policy-html` writes the app copy **and** overwrites `website/{slug}/index.html` here. Then push this repo.

Do **not** create a new GitHub repo or Pages site per app.

## Deploy to GitHub Pages

Target: **`mobileatsg/mobileatsg.github.io`**.

1. Copy **contents** of this `website/` folder to the **repo root**:
   - `index.html`
   - `more-apps.json`
   - `assets/…`
   - `{slug}/index.html` (privacy pages)
2. Confirm:
   - https://mobileatsg.github.io/
   - https://mobileatsg.github.io/more-apps.json
   - https://mobileatsg.github.io/{slug}/

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
