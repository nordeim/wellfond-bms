/**
 * Test: Service Worker sync-offline Removal.
 * High Issue H-005: Service Worker calls non-existent endpoint.
 */

import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Service Worker sync-offline Removal (H-005)', () => {
  const swPath = path.join(__dirname, '../../../../public/sw.js');

  function getFileContent() {
    return fs.readFileSync(swPath, 'utf-8');
  }

  it('should NOT have sync event listener', () => {
    const content = getFileContent();
    expect(content).not.toContain('addEventListener("sync"');
    expect(content).not.toContain("addEventListener('sync'");
  });

  it('should NOT have syncOfflineQueue function', () => {
    const content = getFileContent();
    expect(content).not.toContain('async function syncOfflineQueue');
    expect(content).not.toContain('function syncOfflineQueue');
  });

  it('should NOT reference /api/proxy/sync-offline', () => {
    const content = getFileContent();
    expect(content).not.toContain('sync-offline');
    expect(content).not.toContain('sync_offline');
  });
});
