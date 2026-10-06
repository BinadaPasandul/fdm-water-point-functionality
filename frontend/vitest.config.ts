import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

export default defineConfig({
  esbuild: { jsx: "automatic" },
  resolve: { alias: { "@": resolve(fileURLToPath(new URL(".", import.meta.url))) } },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    restoreMocks: true,
  },
});
