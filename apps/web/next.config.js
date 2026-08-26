/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  rewrites: async () => {
    // In local development, proxy /api/* requests from Next.js port 3000 to FastAPI backend on port 8000
    // In production, Vercel routes /api/* directly to the Python serverless entrypoint
    const target = (process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/api\/?$/, "");
    return [
      {
        source: "/api/:path*",
        destination: `${target}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
