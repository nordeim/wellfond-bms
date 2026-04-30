/**
 * In-Memory Fallback Adapter
 * =========================
 * Last-resort fallback for private browsing mode where both IndexedDB
 * and localStorage are unavailable.
 */

import type { OfflineQueueItem, OfflineQueueItemCreate, StorageAdapter } from './types';

function generateId(): string {
  return crypto.randomUUID();
}

class MemoryAdapter implements StorageAdapter {
  private store = new Map<string, OfflineQueueItem>();

  async getQueue(): Promise<OfflineQueueItem[]> {
    // Return sorted by timestamp
    return Array.from(this.store.values()).sort((a, b) => a.timestamp - b.timestamp);
  }

  async addToQueue(item: OfflineQueueItemCreate): Promise<OfflineQueueItem> {
    const queueItem: OfflineQueueItem = {
      ...item,
      id: generateId(),
      timestamp: Date.now(),
      retryCount: 0,
    };
    
    this.store.set(queueItem.id, queueItem);
    return queueItem;
  }

  async removeFromQueue(id: string): Promise<void> {
    this.store.delete(id);
  }

  async getQueueCount(): Promise<number> {
    return this.store.size;
  }

  async clearQueue(): Promise<void> {
    this.store.clear();
  }

  async incrementRetry(id: string): Promise<void> {
    const item = this.store.get(id);
    if (item) {
      item.retryCount += 1;
      this.store.set(id, item);
    }
  }
}

export const memoryAdapter = new MemoryAdapter();
