import { createHash } from "node:crypto";
import type { Plugin } from "vite";
// Only build outputs listed here can enter Cache Storage. Never store HTTP API responses.
export function offlineShell(): Plugin {
  return {
    name: "invisivel-offline-shell",
    apply: "build",
    enforce: "post",
    generateBundle(_options, bundle) {
      const paths = [
        "/index.html",
        "/manifest.webmanifest",
        "/marca.svg",
        "/icon-192.png",
        "/icon-512.png",
        ...Object.keys(bundle)
          .filter((p) => p.startsWith("assets/") && /\.(js|css)$/.test(p))
          .sort()
          .map((p) => "/" + p),
      ];
      const version = createHash("sha256")
        .update(JSON.stringify(paths))
        .digest("hex")
        .slice(0, 12);
      const code = [
        "const shell = " + JSON.stringify(paths) + ";",
        'const prefix = "invisivel-shell-";',
        "const name = prefix + " + JSON.stringify(version) + ";",
        'self.addEventListener("install", event => {',
        "  event.waitUntil((async () => {",
        "    const cache = await caches.open(name);",
        '    await cache.addAll(shell.map(p => new Request(p, {credentials:"omit",cache:"reload"})));',
        "    await self.skipWaiting();",
        "  })());",
        "});",
        'self.addEventListener("activate", event => {',
        "  event.waitUntil((async () => {",
        "    for (const key of await caches.keys()) if (key.startsWith(prefix) && key !== name) await caches.delete(key);",
        "    await self.clients.claim();",
        "  })());",
        "});",
        'self.addEventListener("fetch", event => {',
        "  const request = event.request, url = new URL(request.url);",
        '  if (url.origin !== self.location.origin || request.method !== "GET" || url.pathname.startsWith("/api") || request.headers.has("Authorization")) return;',
        '  if (request.mode === "navigate") {',
        '    event.respondWith(fetch(request).catch(() => caches.open(name).then(cache => cache.match("/index.html"))));',
        "  } else if (!url.search && shell.includes(url.pathname)) {",
        "    event.respondWith(caches.open(name).then(async cache => (await cache.match(url.pathname)) || fetch(request)));",
        "  }",
        "});",
      ].join("\n");
      this.emitFile({ type: "asset", fileName: "sw.js", source: code });
    },
  };
}
