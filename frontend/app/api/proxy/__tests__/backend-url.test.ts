/**
 * Test: BACKEND_INTERNAL_URL Validation
 * Critical Issue C-003
 *
 * Ensures BACKEND_INTERNAL_URL is required and validated at module load.
 */

import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('BACKEND_INTERNAL_URL Validation (C-003)', () => {
  const routeFilePath = path.join(__dirname, '../[...path]/route.ts');

  it('should have no fallback in route.ts (static check)', () => {
    // Read the route.ts file and check for validation
    const content = fs.readFileSync(routeFilePath, 'utf-8');
    
    // Check that the insecure fallback is NOT present
    expect(content).not.toContain("|| 'http://127.0.0.1:8000'");
    expect(content).not.toContain('|| "http://127.0.0.1:8000"');
    expect(content).not.toContain('|| `http://127.0.0.1:8000`');
    
    // Check that validation is present
    expect(content).toContain('if (!BACKEND_URL)');
    expect(content).toContain('BACKEND_INTERNAL_URL is required');
  });

  it('should not use process.env.BACKEND_INTERNAL_URL with fallback', () => {
    const content = fs.readFileSync(routeFilePath, 'utf-8');
    
    // Should use direct access, not get() with fallback
    const hasFallback = content.match(/BACKEND_URL\s*=\s*process\.env\.BACKEND_INTERNAL_URL\s*\|\|/);
    expect(hasFallback).toBeNull();
  });

  it('should define BACKEND_URL from process.env.BACKEND_INTERNAL_URL', () => {
    const content = fs.readFileSync(routeFilePath, 'utf-8');
    
    // Should define BACKEND_URL from env
    expect(content).toContain("const BACKEND_URL = process.env.BACKEND_INTERNAL_URL;");
  });
});
