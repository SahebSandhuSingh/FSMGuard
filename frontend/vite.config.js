import { defineConfig } from "vite";
// @ts-ignore Vite resolves this plugin at build time
import react from "@vitejs/plugin-react";
// @ts-ignore Tailwind CSS Vite plugin types not resolved by current TS config
import tailwindcss from "@tailwindcss/vite";
// @ts-ignore Default import for Node's path is fine at runtime
import path from "path";
export default defineConfig({
    plugins: [react(), tailwindcss()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
});
