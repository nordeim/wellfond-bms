/**
 * LocalStorage Fallback Adapter
 * =============================
 * Synchronous localStorage wrapper for fallback when IndexedDB is unavailable.
 */

import type { OfflineQueueItem, OfflineQueueItemCreate, StorageAdapter } from './types';
import { LEGACY_STORAGE_KEY } from './types';

function generateId(): string {
  return crypto.randomUUID();
}

function readStorage(): OfflineQueueItem[] {
  if (typeof window === 'undefined') return [];
  
  try {
    const raw = localStorage.getItem(LEGACY_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function writeStorage(items: OfflineQueueItem[]): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(LEGACY_STORAGE_KEY, JSON.stringify(items));
  } catch (err) {
    // Quota exceeded
    if (err instanceof DOMException && err.name === 'QuotaExceededError') {
      throw new Error('Offline queue storage quota exceeded');
    }
    throw err;
  }
}

class LocalStorageAdapter implements StorageAdapter {
  async getQueue(): Promise<OfflineQueueItem[]> {
    // Return copy sorted by timestamp
    return [...readStorage()].sort((a, b) => a.timestamp - b.timestamp);
  }

  async addToQueue(item: OfflineQueueItemCreate): Promise<OfflineQueueItem> {
    const queueItem: OfflineQueueItem = {
      ...item,
      id: generateId(),
      timestamp: Date.now(),
      retryCount: 0,
    };
    
    const queue = readStorage();
    queue.push(queueItem);
    writeStorage(queue);
    
    return queueItem;
  }

  async removeFromQueue(id: string): Promise<void> {
    const queue = readStorage().filter((i) => i.id !== id);
    writeStorage(queue);
  }

  async getQueueCount(): Promise<number> {
    return readStorage().length;
  }

  async clearQueue(): Promise<void> {
    writeStorage([]);
  }

  async incrementRetry(id: string): Promise<void> {
    const queue = readStorage().map((i) =>
      i.id === id ? { ...i, retryCount: i.retryCount + 1 } : i
    );
    writeStorage(queue);
  }
}

export const localStorageAdapter = new LocalStorageAdapter();
