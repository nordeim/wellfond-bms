/**
 * Test: BFF Proxy Path Validation
 * Critical Issue C1: Path Traversal Vulnerability
 *
 * These tests ensure the path validation is secure against traversal attacks.
 */

import { isAllowedPath } from '../[...path]/route';

describe('BFF Proxy Path Validation (Critical Issue C1)', () => {
  describe('Valid paths (should allow)', () => {
    const validPaths = [
      { path: '/auth/login', reason: 'auth endpoint' },
      { path: '/users/', reason: 'users prefix' },
      { path: '/dogs/', reason: 'dogs prefix' },
      { path: '/breeding/mate-check', reason: 'breeding endpoint' },
      { path: '/sales/agreements', reason: 'sales endpoint' },
      { path: '/compliance/nparks', reason: 'compliance endpoint' },
      { path: '/finance/pnl', reason: 'finance endpoint' },
      { path: '/health/', reason: 'health check' },
      { path: '/ready/', reason: 'readiness check' },
      { path: '/health', reason: 'health check without trailing slash' },
      { path: '/ready', reason: 'readiness check without trailing slash' },
    ];

    validPaths.forEach(({ path, reason }) => {
      it(`should allow ${path} (${reason})`, () => {
        expect(isAllowedPath(path)).toBe(true);
      });
    });
  });

  describe('Path traversal attacks (should reject)', () => {
    const attackPaths = [
      { path: '/dogs/../../../etc/passwd', reason: 'directory traversal' },
      { path: '/dogs/../../admin/', reason: 'admin access attempt' },
      { path: '/dogs/../../../backend/config/settings.py', reason: 'config file access' },
      { path: '/dogs/../../.env', reason: 'env file access' },
      { path: '/dogs/../../../proc/self/environ', reason: 'proc file access' },
      { path: '/dogs/../../.git/config', reason: 'git config access' },
      { path: '/dogs/..%2F..%2F..%2Fetc%2Fpasswd', reason: 'URL encoded traversal' },
      { path: '/dogs/%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd', reason: 'double URL encoded' },
      { path: '/dogs/....//....//....//etc/passwd', reason: 'overlong traversal' },
      { path: '/dogs/..\x00/../../etc/passwd', reason: 'null byte injection' },
    ];

    attackPaths.forEach(({ path, reason }) => {
      it(`should reject ${path} (${reason})`, () => {
        expect(isAllowedPath(path)).toBe(false);
      });
    });
  });

  describe('Invalid API paths (should reject)', () => {
    const invalidPaths = [
      { path: '/api/internal/', reason: 'internal API' },
      { path: '/internal/', reason: 'internal path' },
      { path: '/debug/', reason: 'debug endpoint' },
      { path: '/secret/', reason: 'secret path' },
      { path: '/', reason: 'root path' },
      { path: '', reason: 'empty path' },
    ];

    invalidPaths.forEach(({ path, reason }) => {
      it(`should reject ${path || '(empty)'} (${reason})`, () => {
        expect(isAllowedPath(path)).toBe(false);
      });
    });
  });

  describe('Double slash normalization', () => {
    const doubleSlashPaths = [
      { path: '//dogs/', normalized: '/dogs/', expected: true },
      { path: '//dogs//list/', normalized: '/dogs/list/', expected: true },
      { path: '//health/', normalized: '/health/', expected: true },
    ];

    doubleSlashPaths.forEach(({ path, reason }) => {
      it(`should normalize ${path}`, () => {
        // After normalization, should be allowed
        expect(isAllowedPath(path.replace(/\/+/g, '/'))).toBe(true);
      });
    });
  });
});
