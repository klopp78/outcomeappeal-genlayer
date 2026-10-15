import { defineConfig } from "vite";

export default defineConfig({
  root: "site-static",
  base: "/outcomeappeal-genlayer/",
  build: { outDir: "../pages-dist", emptyOutDir: true },
});
