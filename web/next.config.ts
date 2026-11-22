import type { NextConfig } from "next";

// The game is fully client-side: puzzles and player data are static JSON under /public/data,
// so we ship a static export (no server). cacheComponents/partialPrefetching are left off
// because they need the Node.js runtime.
const nextConfig: NextConfig = {
  output: "export",
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
