import type { Config } from "postcss-load-config";

/**
 * Wellfond BMS - PostCSS Configuration
 * Tailwind CSS v4 with @tailwindcss/postcss plugin
 */
const config: Config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
