/** @type {import('next').NextConfig} */
const nextConfig = {
  // Configure webpack for Node.js modules
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Don't resolve Node.js modules on client-side
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        crypto: false,
      };
    }
    return config;
  },

  // Image optimization
  images: {
    domains: [],
  },

  // Optimize for serverless
  output: 'standalone',
};

module.exports = nextConfig;
