/**
 * Edge filter for more-apps.json (Guideline 5.6 / in-app More apps).
 *
 * Single source file on disk; no hand-maintained duplicate.
 *
 *   GET /more-apps.json                  → full catalog (website)
 *   GET /more-apps.json?platform=ios     → iOS in-app: strip Google Play fields,
 *                                          keep showInMobileApp != false only
 *   GET /more-apps.json?platform=android → Android in-app: strip App Store fields,
 *                                          keep showInMobileApp != false only
 *
 * Missing showInMobileApp ⇒ true (backward compatible).
 */
export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const platform = (url.searchParams.get("platform") || "").trim().toLowerCase();

  // Fetch the static catalog without query (avoid Function re-entry).
  const assetUrl = new URL(context.request.url);
  assetUrl.search = "";
  const assetRes = await context.env.ASSETS.fetch(assetUrl.toString());
  if (!platform || (platform !== "ios" && platform !== "android")) {
    // Pass through full catalog for website / unfiltered clients.
    return assetRes;
  }

  if (!assetRes.ok) {
    return assetRes;
  }

  let catalog;
  try {
    catalog = await assetRes.json();
  } catch {
    return new Response("Invalid more-apps.json", { status: 500 });
  }

  const apps = Array.isArray(catalog.apps) ? catalog.apps : [];
  catalog.apps = apps
    .filter((app) => app && app.showInMobileApp !== false)
    .map((app) => stripForPlatform(app, platform));

  catalog.filteredFor = platform;
  catalog.filteredAt = new Date().toISOString();

  return new Response(JSON.stringify(catalog), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=300",
      "access-control-allow-origin": "*",
    },
  });
}

function stripForPlatform(app, platform) {
  const out = { ...app };
  if (platform === "ios") {
    delete out.playStoreUrl;
    delete out.androidPackage;
    if (Array.isArray(out.platforms)) {
      out.platforms = out.platforms.filter((p) => p === "ios");
    }
    if (out.status && typeof out.status === "object") {
      out.status = { ...out.status };
      delete out.status.android;
    }
  } else if (platform === "android") {
    delete out.appStoreUrl;
    delete out.iosAppStoreId;
    if (Array.isArray(out.platforms)) {
      out.platforms = out.platforms.filter((p) => p === "android");
    }
    if (out.status && typeof out.status === "object") {
      out.status = { ...out.status };
      delete out.status.ios;
    }
  }
  return out;
}
