import type { Config } from "tailwindcss";

/**
 * Wellfond BMS - Tailwind CSS v4 Configuration
 * ============================================
 * Tangerine Sky Color Palette - Warm, professional, memorable
 */
const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Tangerine Sky Palette
        tangerine: {
          // Primary background - soft sky
          sky: "#DDEEFF",
          // Primary text - deep navy
          navy: "#0D2030",
          // Primary accent - vibrant tangerine
          primary: "#F97316",
          // Secondary accent - cyan
          secondary: "#0891B2",
          // Success - sage green
          success: "#4EAD72",
          // Warning - amber
          warning: "#D4920A",
          // Error - coral red
          error: "#D94040",
          // Sidebar background
          sidebar: "#E8F4FF",
          // Border color
          border: "#C0D8EE",
          // Muted text
          muted: "#4A7A94",
        },
      },
      fontFamily: {
        // Primary font - Figtree
        figtree: ["var(--font-figtree)", "sans-serif"],
      },
      fontSize: {
        // Consistent typography scale
        "2xs": "0.625rem", // 10px
        xs: "0.75rem", // 12px
        sm: "0.875rem", // 14px
        base: "1rem", // 16px
        lg: "1.125rem", // 18px
        xl: "1.25rem", // 20px
        "2xl": "1.5rem", // 24px
        "3xl": "1.875rem", // 30px
        "4xl": "2.25rem", // 36px
        "5xl": "3rem", // 48px
      },
      spacing: {
        // Consistent spacing scale
        18: "4.5rem",
        22: "5.5rem",
      },
      borderRadius: {
        // Soft, friendly rounded corners
        sm: "0.25rem",
        DEFAULT: "0.5rem",
        md: "0.75rem",
        lg: "1rem",
        xl: "1.5rem",
      },
      boxShadow: {
        // Soft shadows for depth
        soft: "0 2px 8px rgba(13, 32, 48, 0.08)",
        medium: "0 4px 16px rgba(13, 32, 48, 0.12)",
        strong: "0 8px 32px rgba(13, 32, 48, 0.16)",
      },
      animation: {
        // Micro-interactions
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(8px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
