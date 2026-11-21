import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { offlineShell } from "./pwa";
export default defineConfig({
  plugins: [react(), offlineShell()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  test: { environment: "jsdom" },
  build: { chunkSizeWarningLimit: 1250 },
});
