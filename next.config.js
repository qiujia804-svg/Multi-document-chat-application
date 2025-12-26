/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable experimental features for better performance
  experimental: {
    serverComponentsExternalPackages: ['pdf-parse', 'hnswlib-node'],
  },

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

  // API configuration
  api: {
    bodyParser: {
      sizeLimit: '10mb',
    },
    responseLimit: false,
  },

  // Image optimization
  images: {
    domains: [],
  },
};

module.exports = nextConfig;
