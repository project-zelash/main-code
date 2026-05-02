import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        shell: "#070a12",
        panel: "#0d1324",
        line: "#1f2a44",
        signal: "#67e8f9"
      }
    }
  },
  plugins: []
};

export default config;
