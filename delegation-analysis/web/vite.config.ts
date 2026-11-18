import { defineConfig } from "vite";

export default defineConfig({
  root: ".",
  base: "./",
  build: {
    outDir: "dist",
    sourcemap: true,
    target: "es2022",
    rollupOptions: {
      output: {
        manualChunks: {
          "game-core": [
            "./src/core/state.ts",
            "./src/core/types.ts",
            "./src/core/combat_engine.ts",
          ],
          "story": [
            "./src/core/graphic_novel.ts",
            "./src/core/dialogue.ts",
            "./src/core/ending_resolver.ts",
          ],
          "audio": [
            "./src/audio/manager.ts",
            "./src/core/sound_system.ts",
          ],
          "ui": [
            "./src/renderer/menu.ts",
            "./src/renderer/settings.ts",
          ],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  server: {
    port: 5173,
    open: true,
  },
  test: {
    environment: "node",
    globals: true,
    include: ["tests/**/*.test.ts"],
    setupFiles: ["./vitest.setup.ts"],
  },
});
