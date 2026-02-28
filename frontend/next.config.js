/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "*.ppomppu.co.kr" },
      { protocol: "https", hostname: "*.clien.net" },
      { protocol: "https", hostname: "*.quasarzone.com" },
      { protocol: "https", hostname: "*.ruliweb.com" },
      { protocol: "http",  hostname: "*.ppomppu.co.kr" },
    ],
  },
};

module.exports = nextConfig;
