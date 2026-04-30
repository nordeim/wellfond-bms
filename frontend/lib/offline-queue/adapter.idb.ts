/**
 * IndexedDB Storage Adapter
 * ========================
 * Full IndexedDB-backed implementation with atomic operations.
 */

import type { OfflineQueueItem, OfflineQueueItemCreate, StorageAdapter } from './types';
import { getDB } from './db';
import { STORE_NAME } from './types';

function generateId(): string {
  return crypto.randomUUID();
}

class IndexedDBAdapter implements StorageAdapter {
  async getQueue(): Promise<OfflineQueueItem[]> {
    const db = await getDB();
    if (!db) throw new Error('IndexedDB not available');
    
    // Get all items ordered by timestamp (oldest first)
    return db.getAllFromIndex(STORE_NAME, 'byTimestamp');
  }

  async addToQueue(item: OfflineQueueItemCreate): Promise<OfflineQueueItem> {
    const db = await getDB();
    if (!db) throw new Error('IndexedDB not available');

    const queueItem: OfflineQueueItem = {
      ...item,
      id: generateId(),
      timestamp: Date.now(),
      retryCount: 0,
    };

    try {
      await db.put(STORE_NAME, queueItem);
      return queueItem;
    } catch (err) {
      // Check for quota exceeded
      if (err instanceof DOMException && err.name === 'QuotaExceededError') {
        const quotaErr = new Error('Offline queue storage quota exceeded');
        (quotaErr as Error & { name: string }).name = 'QuotaExceededError';
        throw quotaErr;
      }
      throw err;
    }
  }

  async removeFromQueue(id: string): Promise<void> {
    const db = await getDB();
    if (!db) throw new Error('IndexedDB not available');
    
    await db.delete(STORE_NAME, id);
  }

  async getQueueCount(): Promise<number> {
    const db = await getDB();
    if (!db) throw new Error('IndexedDB not available');
    
    // O(1) count operation - no data read
    return db.count(STORE_NAME);
  }

  async clearQueue(): Promise<void> {
    const db = await getDB();
    if (!db) throw new Error('IndexedDB not available');
    
    await db.clear(STORE_NAME);
  }

  async incrementRetry(id: string): Promise<void> {
    const db = await getDB();
    if (!db) throw new Error('IndexedDB not available');

    // Use atomic cursor update
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const cursor = await store.openCursor(id);
    
    if (cursor) {
      const item = cursor.value;
      item.retryCount += 1;
      await cursor.update(item);
    }
    
    await tx.done;
  }
}

export const indexedDBAdapter = new IndexedDBAdapter();
