/**
 * Test: BFF Proxy Runtime Configuration
 * Critical Issue C1: Edge Runtime cannot read process.env at request time
 *
 * This test ensures the proxy uses Node.js runtime, not Edge.
 */

import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('BFF Proxy Runtime (Critical Issue C1)', () => {
  const routeFile = path.join(__dirname, '../[...path]/route.ts');
  const routeContent = fs.readFileSync(routeFile, 'utf-8');

  it('should NOT use Edge Runtime', () => {
    // Edge Runtime is problematic because process.env is only available
    // at build time, not at request time
    // Check for uncommented Edge runtime export (not in comments)
    const lines = routeContent.split('\n');
    const hasActiveEdgeRuntime = lines.some(line =>
      line.trim().startsWith("export const runtime = 'edge'")
    );

    expect(hasActiveEdgeRuntime).toBe(false);
  });

  it('should use default Node.js runtime (or explicitly nodejs)', () => {
    // Either no runtime export (defaults to nodejs)
    // or explicit runtime = 'nodejs'
    const lines = routeContent.split('\n');
    const hasActiveEdge = lines.some(line =>
      line.trim().startsWith("export const runtime = 'edge'")
    );
    const hasActiveNode = lines.some(line =>
      line.trim().startsWith("export const runtime = 'nodejs'")
    );

    // Should not have active edge export
    expect(hasActiveEdge).toBe(false);

    // If there's an active runtime export, it should be nodejs
    const hasActiveRuntimeExport = lines.some(line =>
      line.trim().startsWith('export const runtime')
    );
    if (hasActiveRuntimeExport) {
      expect(hasActiveNode).toBe(true);
    }
  });

  it('should access process.env.BACKEND_INTERNAL_URL', () => {
    // The route should read BACKEND_INTERNAL_URL from process.env
    // which requires Node.js runtime
    const hasEnvAccess = routeContent.includes('process.env.BACKEND_INTERNAL_URL');

    expect(hasEnvAccess).toBe(true);
  });
});
