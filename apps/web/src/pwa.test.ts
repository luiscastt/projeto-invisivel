import { runInNewContext } from "node:vm";
import { describe, expect, it } from "vitest";
import { offlineShell } from "../pwa";
describe("cache do PWA", () => {
  it("limita as respostas interceptadas à navegação e aos arquivos da versão", () => {
    let code = "";
    const plugin = offlineShell();
    const generate = plugin.generateBundle as Function;
    generate.call(
      {
        emitFile: (file: { source: string }) => {
          code = file.source;
        },
      },
      {},
      { "assets/site-hash.js": {}, "assets/site-hash.css": {} },
    );
    const handlers = new Map<string, Function>();
    runInNewContext(code, {
      self: {
        location: { origin: "https://invisivel.test" },
        addEventListener: (type: string, fn: Function) =>
          handlers.set(type, fn),
      },
      URL,
      caches: { open: async () => ({ match: () => true }) },
    });
    const intercept = (path: string, method = "GET", token = false) => {
      let handled = false;
      handlers.get("fetch")!({
        request: {
          url: new URL(path, "https://invisivel.test").href,
          method,
          headers: { has: () => token },
          mode: "cors",
        },
        respondWith: () => {
          handled = true;
        },
      });
      return handled;
    };
    expect(intercept("/assets/site-hash.js")).toBe(true);
    for (const p of [
      "/api/v1/media/abc",
      "/api/v1/auth/me",
      "/api/v1/territories/3205002/summary",
      "/assets/unlisted.js",
      "/foto.jpg",
      "https://tile.openstreetmap.org/0/0/0.png",
    ])
      expect(intercept(p)).toBe(false);
    expect(intercept("/assets/site-hash.js", "POST")).toBe(false);
    expect(intercept("/assets/site-hash.js", "GET", true)).toBe(false);
  });
});
