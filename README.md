# Mobile@SG website (apps list)

Static landing page for **https://mobilesg.org/** — publisher identity + list of apps.

**Git:** this folder is the working tree for:

| Remote | Repo | Role |
|--------|------|------|
| **`origin`** | [`chachean/mobilesg`](https://github.com/chachean/mobilesg) | Canonical source (`main`) |
| **`pages`** | [`mobileatsg/mobileatsg.github.io`](https://github.com/mobileatsg/mobileatsg.github.io) | Legacy GitHub Pages mirror (optional) |

```bash
git push origin main          # primary
git push pages main           # keep github.io in sync if still used
```

SSH: `origin` uses host alias **`github.com-chachean`** (`~/.ssh/id_github` → user **chachean**). Default `github.com` key is **mobileatsg** (org), which cannot see private `chachean/*` repos.

Point **Cloudflare Pages** at **`chachean/mobilesg`** when you cut over from `mobileatsg.github.io`.

## Shared catalog (source of truth)

| URL (after deploy) | File |
|--------------------|------|
| `https://mobilesg.org/more-apps.json` | [`more-apps.json`](./more-apps.json) |

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
https://mobilesg.org/?lang=zh
https://mobilesg.org/?lang=zh-Hans
https://mobilesg.org/?lang=en
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
| `privacyUrl` | string | **Host-relative** path, e.g. `/{id}/` (resolved against the page/catalog origin — works for `www` and apex) |
| `iconUrl` | string | **Absolute** PNG URL for in-app More apps, e.g. `https://mobilesg.org/assets/apps/{id}.png` (not host-relative — apps cannot load `/assets/...`) |
| `iconPath` | string | Relative path for website, e.g. `assets/apps/{id}.png` |
| `sortOrder` | number | Ascending |
| `enabled` | bool | `false` hides without deleting (website + in-app) |
| `showInMobileApp` | bool | **Optional.** `false` = hide from **in-app** More apps only; website still shows. **Missing ⇒ `true`** (backward compatible; do not bump `schemaVersion`) |
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
| **Developer website** | All `enabled` apps (**ignores** `showInMobileApp`) | Per-platform chips (`iOS · Published`, `Android · In process`); store button only for platforms that are `Published` |
| **In-app More apps (iOS device)** | `showInMobileApp != false` + **`status.ios === "Published"`** | Ignore `status.android` for the list; exclude self |
| **In-app More apps (Android device)** | `showInMobileApp != false` + **`status.android === "Published"`** | Ignore `status.ios` for the list; exclude self |

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
   - `showInMobileApp != false` (missing ⇒ **true**)  
   - current platform status must be **`Published`**  
   - exclude current app (`bundleId` / `androidPackage`)  
   - apply `hideInAppIds` / `moreAppsExcludeIds`  
5. Prefer `appStoreUrl` → else `iosAppStoreId` → else search / website.  
6. Prefer `playStoreUrl` → else package details URL.  
7. Load `iconUrl` over the network (cache on disk in apps).  
8. On network failure: last successful cache → bundled fallback (apps only).

### Canonical fetch URL

```text
https://mobilesg.org/more-apps.json
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
| `sudoku/` | https://mobilesg.org/sudoku/ |
| `sudokumix/` | Redirect → `/sudoku/` |
| `pixelcolor/` | https://mobilesg.org/pixelcolor/ |
| `smartalarm/` | https://mobilesg.org/smartalarm/ |
| `mathbuddy/` | https://mobilesg.org/mathbuddy/ |
| `parksg/` | https://mobilesg.org/parksg/ |
| `totomatch/` | https://mobilesg.org/totomatch/ |
| `fourdmatch/` | https://mobilesg.org/fourdmatch/ |
| `stocksg/` | https://mobilesg.org/stocksg/ |
| `stocksg/eula/` | https://mobilesg.org/stocksg/eula/ |

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
   - https://mobilesg.org/
   - https://mobilesg.org/more-apps.json
   - https://mobilesg.org/{slug}/

---

## Adding a new app (no other app redeploy)

1. Add icon: `assets/apps/{id}.png` (256×256).  
2. Append an entry to **`more-apps.json`** (`enabled: true`, `showInMobileApp: true` unless you want website-only).  
3. Deploy Pages.  
4. Fill `iosAppStoreId` / store URLs when listings go live (edit JSON only).  

In-app More apps and this website pick it up on next catalog fetch.

To pause everywhere: `"enabled": false` → redeploy JSON only.  
To hide from in-app More apps only (keep on website): `"showInMobileApp": false`.

---

## Identity (fixed)

| Field | Value |
|-------|--------|
| Developer | Mobile@SG |
| Support | mobileatsg@gmail.com |
| Site | https://mobilesg.org/ |
| Catalog | https://mobilesg.org/more-apps.json |
