/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  output: 'export',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://61q69bcvs0.execute-api.us-east-1.amazonaws.com/dev'
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://61q69bcvs0.execute-api.us-east-1.amazonaws.com/dev/:path*'
      }
    ]
  }
};
