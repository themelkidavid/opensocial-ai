import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ["discussed-destination-tender-celebrate.trycloudflare.com"],
    proxy: { "/api": "http://127.0.0.1:8000" }
  },
  test: { environment: "jsdom", setupFiles: ["./src/test/setup.ts"] }
});
