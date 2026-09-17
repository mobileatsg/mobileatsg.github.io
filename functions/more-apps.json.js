/**
 * Optional CF Pages edge filter (same rules as generate-platform-catalogs.py).
 *
 * Prefer static more-apps-ios.json / more-apps-android.json for in-app clients.
 * This Function keeps ?platform=ios|android working when Pages Functions are live.
 */
const IOS_KEYS = [
  "id", "name", "blurb", "category", "status", "platforms", "bundleId",
  "iosAppStoreId", "appStoreUrl", "iconUrl", "sortOrder", "enabled",
  "showInMobileApp", "featured", "hideInAppIds", "moreAppsExcludeIds", "locales",
];
const ANDROID_KEYS = [
  "id", "name", "blurb", "category", "status", "platforms", "androidPackage",
  "playStoreUrl", "iconUrl", "sortOrder", "enabled",
  "showInMobileApp", "featured", "hideInAppIds", "moreAppsExcludeIds", "locales",
];
const LOCALE_KEYS = ["name", "blurb", "category"];

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const platform = (url.searchParams.get("platform") || "").trim().toLowerCase();

  const assetUrl = new URL(context.request.url);
  assetUrl.search = "";
  const assetRes = await context.env.ASSETS.fetch(assetUrl.toString());
  if (!platform || (platform !== "ios" && platform !== "android")) {
    return assetRes;
  }
  if (!assetRes.ok) return assetRes;

  let catalog;
  try {
    catalog = await assetRes.json();
  } catch {
    return new Response("Invalid more-apps.json", { status: 500 });
  }

  const keys = platform === "ios" ? IOS_KEYS : ANDROID_KEYS;
  const apps = [];
  for (const app of catalog.apps || []) {
    const slim = slimApp(app, platform, keys);
    if (slim) apps.push(slim);
  }
  apps.sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0));

  const out = {
    schemaVersion: catalog.schemaVersion ?? 1,
    updatedAt: catalog.updatedAt,
    defaultLocale: catalog.defaultLocale || "en",
    supportedLocales: catalog.supportedLocales || ["en", "zh-Hans"],
    policy: {
      inAppMoreAppsShowStatuses:
        catalog.policy?.inAppMoreAppsShowStatuses || ["Published"],
    },
    filteredFor: platform,
    filteredAt: new Date().toISOString(),
    source: "more-apps.json",
    apps,
  };

  return new Response(JSON.stringify(out), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=300",
      "access-control-allow-origin": "*",
    },
  });
}

function slimApp(app, platform, keys) {
  if (!app || app.showInMobileApp === false || app.enabled === false) return null;
  const out = {};
  for (const k of keys) {
    if (!(k in app) || app[k] == null || app[k] === "" || (Array.isArray(app[k]) && !app[k].length)) {
      continue;
    }
    if (k === "locales") {
      const loc = slimLocales(app.locales);
      if (loc) out.locales = loc;
      continue;
    }
    if (k === "status" && typeof app.status === "object") {
      if (app.status[platform] != null) out.status = { [platform]: app.status[platform] };
      continue;
    }
    if (k === "platforms" && Array.isArray(app.platforms)) {
      const plats = app.platforms.filter((p) => p === platform);
      if (plats.length) out.platforms = plats;
      continue;
    }
    out[k] = app[k];
  }
  if (!out.id) return null;
  if (platform === "ios" && !(out.appStoreUrl || out.iosAppStoreId)) return null;
  if (platform === "android" && !(out.playStoreUrl || out.androidPackage)) return null;
  return out;
}

function slimLocales(locales) {
  if (!locales || typeof locales !== "object") return null;
  const out = {};
  for (const [loc, copy] of Object.entries(locales)) {
    if (!copy || typeof copy !== "object") continue;
    const slim = {};
    for (const k of LOCALE_KEYS) {
      if (copy[k]) slim[k] = copy[k];
    }
    if (Object.keys(slim).length) out[loc] = slim;
  }
  return Object.keys(out).length ? out : null;
}
