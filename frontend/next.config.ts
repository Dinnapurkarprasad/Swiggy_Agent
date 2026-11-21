import type { NextConfig } from "next";

// FastAPI address. The browser never calls it directly: it calls /api/... on this
// Next.js server, which forwards the request. Frontend and API then share one origin,
// so the httpOnly login cookie works locally and on Vercel.
const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backendUrl}/:path*` }];
  },
};

export default nextConfig;
