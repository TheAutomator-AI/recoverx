/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  rewrites: async () => {
    // Only in local standalone Next.js development (without Vercel CLI) proxy /api/* to port 8000
    // In production and Vercel environments, allow Vercel to natively route /api/* to api/index.py
    if (process.env.NODE_ENV === "development") {
      const target = (process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/api\/?$/, "");
      return [
        {
          source: "/api/:path*",
          destination: `${target}/api/:path*`,
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;
