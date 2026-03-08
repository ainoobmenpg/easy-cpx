import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable Turbopack for Tailwind CSS compatibility
  turbopack: false,
};

export default nextConfig;
