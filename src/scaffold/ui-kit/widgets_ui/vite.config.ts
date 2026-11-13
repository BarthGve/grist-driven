import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";
import path from "node:path";

export default defineConfig({
  root: path.resolve(__dirname, "src"),
  plugins: [react(), viteSingleFile()],
  // iife : le déployeur rejoue le JS dans un <script> classique (pas de module), sans export ni import.meta.
  build: {
    outDir: path.resolve(__dirname, "dist"),
    emptyOutDir: true,
    target: "es2022",
    rollupOptions: { output: { format: "iife" as const, inlineDynamicImports: true } },
  },
});
