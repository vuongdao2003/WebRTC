import type { NextConfig } from "next";

/** @type {import('next').NextConfig} */
const nextConfig = {

  eslint: {
    ignoreDuringBuilds: true,
  },

  // During dev, proxy certain API calls to the local backend to avoid
  // browser private-network CORS issues when the page is opened on a
  // network IP (e.g. 192.x.x.x) but the backend is on loopback.
  async rewrites() {
    return [
      {
        source: '/token',
        destination: 'http://127.0.0.1:8000/token',
      },
      {
        source: '/rooms',
        destination: 'http://127.0.0.1:8000/rooms',
      },
    ];
  },
};

export default nextConfig;
