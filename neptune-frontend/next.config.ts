import type { NextConfig } from "next";

/** @type {import('next').NextConfig} */
const nextConfig: NextConfig = {
  // Add static export for Tauri
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true
  },
  distDir: 'out', // This is where static files will be generated
  
  // Disable ESLint during builds
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  
  // Keep your existing Three.js config
  transpilePackages: ['three'],
  webpack: (config) => {
    // Configuration for Three.js
    config.externals = config.externals || [];
    config.externals.push({
      'canvas': 'canvas',
    });
    
    // Return any existing config modifications you may have
    return config;
  }
};

export default nextConfig;
