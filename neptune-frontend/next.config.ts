import type { NextConfig } from "next";

// Add the Three.js configuration to your existing next.config.ts

/** @type {import('next').NextConfig} */
const nextConfig: NextConfig = {
  // Keep your existing config here
  
  // Add these lines for Three.js:
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
