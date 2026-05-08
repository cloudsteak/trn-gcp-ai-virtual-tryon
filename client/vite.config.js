import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // /try-on → http://localhost:8000/try-on
      "/try-on": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
