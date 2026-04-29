/**
 * Test: Next.js Config Security
 * Critical Issue C2: BACKEND_INTERNAL_URL must not leak to browser
 *
 * This test ensures no internal URLs are exposed via next.config.ts env block.
 */

import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Next.js Config Security (Critical Issue C2)', () => {
  const configFile = path.join(__dirname, '../next.config.ts');
  const configContent = fs.readFileSync(configFile, 'utf-8');

  it('should NOT expose BACKEND_INTERNAL_URL in env block', () => {
    // The env block in next.config.ts makes variables available client-side
    // BACKEND_INTERNAL_URL should only be server-side
    const hasEnvBlockWithBackendUrl = configContent.includes('BACKEND_INTERNAL_URL:');

    expect(hasEnvBlockWithBackendUrl).toBe(false);
  });

  it('should use process.env.BACKEND_INTERNAL_URL only in server-side contexts', () => {
    // process.env.BACKEND_INTERNAL_URL can be used in:
    // - rewrites() function (runs server-side)
    // - API routes (runs server-side)
    // But should NOT be in env: {} block

    const lines = configContent.split('\n');
    let inEnvBlock = false;
    let envBlockStart = -1;
    let envBlockEnd = -1;

    // Find env block boundaries
    lines.forEach((line, index) => {
      if (line.trim().startsWith('env:')) {
        inEnvBlock = true;
        envBlockStart = index;
      }
      if (inEnvBlock && line.trim() === '},') {
        envBlockEnd = index;
        inEnvBlock = false;
      }
    });

    // If there's an env block, check it doesn't contain BACKEND_INTERNAL_URL
    if (envBlockStart !== -1 && envBlockEnd !== -1) {
      const envBlock = lines.slice(envBlockStart, envBlockEnd + 1).join('\n');
      expect(envBlock).not.toContain('BACKEND_INTERNAL_URL');
    }
  });

  it('should have server-side rewrites using BACKEND_INTERNAL_URL', () => {
    // The rewrites() function is server-side only and can safely use
    // process.env.BACKEND_INTERNAL_URL
    expect(configContent).toContain('BACKEND_INTERNAL_URL');
    expect(configContent).toContain('rewrites');
  });
});
