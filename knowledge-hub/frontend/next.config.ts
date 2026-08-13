import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Lambda (Web Adapter) / コンテナで動かしやすいよう standalone 出力にする
  output: "standalone",
};

export default nextConfig;
