/**
 * Test: Build-time validation for BACKEND_INTERNAL_URL.
 * High Issue H-004: Add build-time validation for BACKEND_INTERNAL_URL.
 */
import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Build-time Validation for BACKEND_INTERNAL_URL (H-004)', () => {
  const configPath = path.join(__dirname, '../../../../next.config.ts');

  function getFileContent() {
    return fs.readFileSync(configPath, 'utf-8');
  }

  it('should validate BACKEND_INTERNAL_URL is set at build time', () => {
    /** RED: Test that next.config.ts validates BACKEND_INTERNAL_URL.
     * Currently it uses a fallback (http://127.0.0.1:8000).
     * Should fail the build if BACKEND_INTERNAL_URL is not set.
     */
    const content = getFileContent();
    
    // Should have validation that throws error if BACKEND_INTERNAL_URL is missing
    // This could be a check at the top of the config
    expect(content).toContain('BACKEND_INTERNAL_URL');
    expect(content).toContain('process.env');
    
    // Should NOT have a fallback (should fail loudly instead)
    // This test will fail initially because the config uses a fallback
    expect(content).not.toContain('|| "http://127.0.0.1:8000"');
  });

  it('should throw error if BACKEND_INTERNAL_URL is not set', () => {
    /** RED: Test that the config throws an error when BACKEND_INTERNAL_URL is missing.
     * This validates the build-time check works.
     */
    const content = getFileContent();
    
    // Should have a conditional that checks if BACKEND_INTERNAL_URL is set
    // and throws an error if it's missing
    expect(content).toContain('throw new Error');
    expect(content).toContain('BACKEND_INTERNAL_URL is required');
  });
});
