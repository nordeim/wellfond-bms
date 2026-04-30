/**
 * Offline Queue - Main Entry Point
 * ==================================
 * Auto-detects storage availability and delegates to the appropriate adapter:
 * 1. IndexedDB (preferred) - ~unlimited storage, transactional, async
 * 2. localStorage (fallback) - ~5-10MB, synchronous
 * 3. In-Memory (last resort) - session-only, lost on refresh
 */

import type { OfflineQueueItem, OfflineQueueItemCreate, StorageAdapter } from './types';
import { indexedDBAdapter } from './adapter.idb';
import { localStorageAdapter } from './adapter.ls';
import { memoryAdapter } from './adapter.memory';
import { isIndexedDBAvailable, clearDBConnection } from './db';

// Adapter selection state
let selectedAdapter: StorageAdapter | null = null;
let adapterPromise: Promise<StorageAdapter> | null = null;

/**
 * Detect and return the best available storage adapter.
 * Priority: IndexedDB > localStorage > In-Memory
 */
async function getAdapter(): Promise<StorageAdapter> {
  if (selectedAdapter) return selectedAdapter;
  if (adapterPromise) return adapterPromise;

  adapterPromise = detectAndSelectAdapter();
  selectedAdapter = await adapterPromise;
  
  console.log(`[offline-queue] Using ${selectedAdapter.constructor.name}`);
  return selectedAdapter;
}

async function detectAndSelectAdapter(): Promise<StorageAdapter> {
  // Try IndexedDB first
  const idbAvailable = await isIndexedDBAvailable();
  if (idbAvailable) {
    return indexedDBAdapter;
  }

  // Fallback to localStorage if available
  if (typeof window !== 'undefined' && window.localStorage) {
    console.warn('[offline-queue] IndexedDB unavailable, using localStorage fallback');
    return localStorageAdapter;
  }

  // Last resort: in-memory
  console.warn('[offline-queue] No persistent storage available, using in-memory fallback (data lost on refresh)');
  return memoryAdapter;
}

/**
 * Get all queue items, ordered by timestamp (oldest first).
 */
export async function getQueue(): Promise<OfflineQueueItem[]> {
  const adapter = await getAdapter();
  return adapter.getQueue();
}

/**
 * Add an item to the queue.
 * Auto-generates id, timestamp, and sets retryCount to 0.
 */
export async function addToQueue(
  item: OfflineQueueItemCreate
): Promise<OfflineQueueItem> {
  const adapter = await getAdapter();
  return adapter.addToQueue(item);
}

/**
 * Remove an item from the queue by id.
 */
export async function removeFromQueue(id: string): Promise<void> {
  const adapter = await getAdapter();
  return adapter.removeFromQueue(id);
}

/**
 * Get the number of items in the queue.
 * O(1) for IndexedDB, O(n) for localStorage.
 */
export async function getQueueCount(): Promise<number> {
  const adapter = await getAdapter();
  return adapter.getQueueCount();
}

/**
 * Clear all items from the queue.
 */
export async function clearQueue(): Promise<void> {
  const adapter = await getAdapter();
  return adapter.clearQueue();
}

/**
 * Increment the retry count for an item.
 * Uses atomic update in IndexedDB.
 */
export async function incrementRetry(id: string): Promise<void> {
  const adapter = await getAdapter();
  return adapter.incrementRetry(id);
}

/**
 * Force re-detection of storage on next access.
 * Useful for testing or after storage conditions change.
 */
export function resetAdapter(): void {
  selectedAdapter = null;
  adapterPromise = null;
  clearDBConnection();
}

/**
 * Get current adapter name for debugging.
 */
export async function getAdapterName(): Promise<string> {
  const adapter = await getAdapter();
  return adapter.constructor.name;
}

// Re-export types
export type { OfflineQueueItem, OfflineQueueItemCreate };

// Default export for convenience
export default {
  getQueue,
  addToQueue,
  removeFromQueue,
  getQueueCount,
  clearQueue,
  incrementRetry,
  resetAdapter,
  getAdapterName,
};

// Legacy synchronous API (deprecated - for backward compatibility)
// These will be removed in a future version
export function getQueueSync(): OfflineQueueItem[] {
  console.warn('[offline-queue] getQueueSync is deprecated. Use await getQueue() instead.');
  if (typeof window !== 'undefined') {
    try {
      const raw = localStorage.getItem('offline_queue');
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }
  return [];
}

export function addToQueueSync(item: OfflineQueueItemCreate): OfflineQueueItem {
  console.warn('[offline-queue] addToQueueSync is deprecated. Use await addToQueue() instead.');
  const queueItem: OfflineQueueItem = {
    ...item,
    id: crypto.randomUUID(),
    timestamp: Date.now(),
    retryCount: 0,
  };
  const queue = getQueueSync();
  queue.push(queueItem);
  localStorage.setItem('offline_queue', JSON.stringify(queue));
  return queueItem;
}
