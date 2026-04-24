import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

/**
 * Wellfond BMS - Vitest Configuration
 * ====================================
 * Unit and integration testing with jsdom environment
 */
export default defineConfig({
  plugins: [react()],
  test: {
    // Test environment - jsdom for DOM testing
    environment: "jsdom",

    // Test file patterns
    include: ["**/*.{test,spec}.{js,ts,jsx,tsx}"],
    exclude: ["node_modules", ".next", "playwright"],

    // Global test setup
    globals: true,

    // Setup files run before tests
    setupFiles: ["./tests/setup.ts"],

    // Coverage configuration
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html", "lcov"],
      exclude: [
        "node_modules/",
        ".next/",
        "tests/",
        "**/*.d.ts",
        "**/*.config.*",
        "**/mockData/**",
      ],
      thresholds: {
        branches: 70,
        functions: 70,
        lines: 70,
        statements: 70,
      },
    },

    // Mock configuration
    mockReset: true,
    restoreMocks: true,

    // Timeout settings
    testTimeout: 10000,
    hookTimeout: 10000,
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
