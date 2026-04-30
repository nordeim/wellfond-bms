/**
 * Offline Queue Tests
 * ===================
 * Unit tests for IndexedDB-backed offline queue.
 * Uses fake-indexeddb for Node.js environment testing.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import 'fake-indexeddb/auto';

import {
  getQueue,
  addToQueue,
  removeFromQueue,
  getQueueCount,
  clearQueue,
  incrementRetry,
  resetAdapter,
} from '../index';

describe('Offline Queue', () => {
  beforeEach(async () => {
    resetAdapter();
    await clearQueue();
  });

  afterEach(() => {
    resetAdapter();
  });

  describe('Basic Operations', () => {
    it('should return empty array when queue is empty', async () => {
      const queue = await getQueue();
      expect(queue).toEqual([]);
    });

    it('should add item to queue', async () => {
      const item = await addToQueue({
        method: 'POST',
        url: '/api/test',
        body: { data: 'test' },
      });

      expect(item).toMatchObject({
        method: 'POST',
        url: '/api/test',
        retryCount: 0,
      });
      expect(item.id).toBeDefined();
      expect(item.timestamp).toBeGreaterThan(0);

      const queue = await getQueue();
      expect(queue).toHaveLength(1);
      expect(queue[0].id).toBe(item.id);
    });

    it('should remove item from queue', async () => {
      const item = await addToQueue({
        method: 'POST',
        url: '/api/test',
      });

      await removeFromQueue(item.id);
      
      const queue = await getQueue();
      expect(queue).toHaveLength(0);
    });

    it('should return correct queue count', async () => {
      expect(await getQueueCount()).toBe(0);

      await addToQueue({ method: 'POST', url: '/api/1' });
      expect(await getQueueCount()).toBe(1);

      await addToQueue({ method: 'POST', url: '/api/2' });
      expect(await getQueueCount()).toBe(2);
    });

    it('should clear all items', async () => {
      await addToQueue({ method: 'POST', url: '/api/1' });
      await addToQueue({ method: 'POST', url: '/api/2' });

      await clearQueue();
      
      expect(await getQueueCount()).toBe(0);
      expect(await getQueue()).toEqual([]);
    });

    it('should increment retry count atomically', async () => {
      const item = await addToQueue({
        method: 'POST',
        url: '/api/test',
      });

      expect(item.retryCount).toBe(0);

      await incrementRetry(item.id);
      
      const queue = await getQueue();
      expect(queue[0].retryCount).toBe(1);

      await incrementRetry(item.id);
      const queue2 = await getQueue();
      expect(queue2[0].retryCount).toBe(2);
    });

    it('should handle incrementRetry on non-existent item gracefully', async () => {
      await incrementRetry('non-existent-id');
      // Should not throw
    });

    it('should handle removeFromQueue on non-existent item gracefully', async () => {
      await removeFromQueue('non-existent-id');
      // Should not throw
    });
  });

  describe('Ordering', () => {
    it('should return items ordered by timestamp (oldest first)', async () => {
      // Add items with small delays to ensure different timestamps
      const item1 = await addToQueue({ method: 'POST', url: '/api/1' });
      await new Promise(r => setTimeout(r, 10));
      const item2 = await addToQueue({ method: 'POST', url: '/api/2' });
      await new Promise(r => setTimeout(r, 10));
      const item3 = await addToQueue({ method: 'POST', url: '/api/3' });

      const queue = await getQueue();
      
      expect(queue[0].id).toBe(item1.id);
      expect(queue[1].id).toBe(item2.id);
      expect(queue[2].id).toBe(item3.id);
    });
  });

  describe('Data Integrity', () => {
    it('should preserve all item properties', async () => {
      const item = await addToQueue({
        method: 'POST',
        url: '/api/test',
        body: { complex: { nested: 'data', number: 123 } },
        headers: { 'Content-Type': 'application/json' },
      });

      const queue = await getQueue();
      const retrieved = queue[0];

      expect(retrieved.method).toBe('POST');
      expect(retrieved.url).toBe('/api/test');
      expect(retrieved.body).toEqual({ complex: { nested: 'data', number: 123 } });
      expect(retrieved.headers).toEqual({ 'Content-Type': 'application/json' });
      expect(retrieved.id).toBe(item.id);
      expect(retrieved.timestamp).toBe(item.timestamp);
      expect(retrieved.retryCount).toBe(0);
    });

  it('should handle large payloads', async () => {
    const largeBody = { data: 'x'.repeat(10000) }; // 10KB

    await addToQueue({
      method: 'POST',
      url: '/api/test',
      body: largeBody,
    });

    const queue = await getQueue();
    expect(queue[0].body).toEqual(largeBody);
  });

    it('should handle 1000 items', async () => {
      for (let i = 0; i < 1000; i++) {
        await addToQueue({
          method: 'POST',
          url: `/api/item-${i}`,
        });
      }

      const count = await getQueueCount();
      expect(count).toBe(1000);

      const queue = await getQueue();
      expect(queue).toHaveLength(1000);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty body', async () => {
      const item = await addToQueue({
        method: 'GET',
        url: '/api/test',
      });

      expect(item.body).toBeUndefined();
      
      const queue = await getQueue();
      expect(queue[0].body).toBeUndefined();
    });

    it('should handle all HTTP methods', async () => {
      const methods: Array<'GET' | 'POST' | 'PUT' | 'DELETE'> = ['GET', 'POST', 'PUT', 'DELETE'];
      
      for (const method of methods) {
        await addToQueue({ method, url: `/api/${method.toLowerCase()}` });
      }

      const queue = await getQueue();
      const urls = queue.map(i => i.method);
      expect(urls).toEqual(['GET', 'POST', 'PUT', 'DELETE']);
    });

    it('should generate unique ids', async () => {
      const ids = new Set<string>();
      
      for (let i = 0; i < 100; i++) {
        const item = await addToQueue({ method: 'POST', url: '/api/test' });
        expect(ids.has(item.id)).toBe(false);
        ids.add(item.id);
      }
      
      expect(ids.size).toBe(100);
    });
  });
});

describe('Queue Persistence', () => {
  beforeEach(async () => {
    resetAdapter();
    await clearQueue();
  });

  afterEach(() => {
    resetAdapter();
  });

  it('should persist data across adapter re-instantiations', async () => {
    // Add item
    const item = await addToQueue({ method: 'POST', url: '/api/test' });
    
    // Simulate reload by clearing adapter cache
    resetAdapter();
    
    // Data should still be there
    const queue = await getQueue();
    expect(queue).toHaveLength(1);
    expect(queue[0].id).toBe(item.id);
  });
});
