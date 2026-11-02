import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// W dev API idzie do lokalnego backendu (tylko 127.0.0.1).
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8765" } },
  build: { outDir: "dist", emptyOutDir: true },
});
