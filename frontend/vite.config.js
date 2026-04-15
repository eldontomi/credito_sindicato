import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  server: {
    port: 5173,
    host: "0.0.0.0",
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        faq: resolve(__dirname, "faq.html"),
      },
    },
  },
});
