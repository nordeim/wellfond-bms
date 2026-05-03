// TDD: Breeding Hook Paths
// ==========================
// Phase 1 — Verify all hooks use relative paths (no /api/v1/ prefix).

import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

describe("hook API path convention", () => {
  it("use-breeding.ts must not use /api/v1/ prefix paths", () => {
    const source = fs.readFileSync(
      path.resolve(__dirname, "../../hooks/use-breeding.ts"),
      "utf-8"
    );

    // Simple string matching — find any /api/v1/breeding/ in the file
    const lines = source.split("\n");
    const violations: { line: number; text: string }[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      // Match calls like api.post("/api/v1/...", or api.post(`/api/v1/...`,
      if (/\bapi\.\w+\(\s*["'`]\/api\/v1\//.test(line)) {
        violations.push({ line: i + 1, text: line.trim() });
      }
    }

    expect(
      violations,
      `Found ${violations.length} lines with "/api/v1/" prefix paths in use-breeding.ts. ` +
        `violations:\n${violations.map((v) => `  line ${v.line}: ${v.text}`).join("\n")}\n\n` +
        `Fix: Replace "/api/v1/breeding/..." with "/breeding/..." in all 12 occurrences.`
    ).toHaveLength(0);
  });

  it("no other hook file should use /api/v1/ prefix paths", () => {
    const hooksDir = path.resolve(__dirname, "../../hooks");
    const files = fs
      .readdirSync(hooksDir)
      .filter((f) => f.endsWith(".ts") && f !== "index.ts");

    const allViolations: { file: string; line: number; text: string }[] = [];

    for (const file of files) {
      const source = fs.readFileSync(path.join(hooksDir, file), "utf-8");
      const lines = source.split("\n");

      for (let i = 0; i < lines.length; i++) {
        if (/\bapi\.\w+\(\s*["'`]\/api\/v1\//.test(lines[i])) {
          allViolations.push({
            file,
            line: i + 1,
            text: lines[i].trim(),
          });
        }
      }
    }

    // We expect use-breeding.ts violations until fixed
    // But no other file should have this pattern
    const otherViolations = allViolations.filter(
      (v) => v.file !== "use-breeding.ts"
    );

    expect(
      otherViolations,
      `Found ${otherViolations.length} violations in non-breeding hooks: ${JSON.stringify(otherViolations)}`
    ).toHaveLength(0);
  });
});