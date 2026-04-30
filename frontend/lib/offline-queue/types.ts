/**
 * Offline Queue Types
 * =================
 * TypeScript types for IndexedDB-backed offline queue.
 */

export interface OfflineQueueItem {
  id: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  url: string;
  body?: unknown;
  headers?: Record<string, string>;
  timestamp: number;
  retryCount: number;
}

// For creating new items (id, timestamp, retryCount auto-generated)
export type OfflineQueueItemCreate = Omit<OfflineQueueItem, 'id' | 'timestamp' | 'retryCount'>;

// Storage adapter interface
export interface StorageAdapter {
  getQueue(): Promise<OfflineQueueItem[]>;
  addToQueue(item: OfflineQueueItemCreate): Promise<OfflineQueueItem>;
  removeFromQueue(id: string): Promise<void>;
  getQueueCount(): Promise<number>;
  clearQueue(): Promise<void>;
  incrementRetry(id: string): Promise<void>;
}

// Database constants
export const DB_NAME = 'wellfond-offline-queue';
export const DB_VERSION = 1;
export const STORE_NAME = 'queue';

// Migration flag
export const MIGRATION_FLAG_KEY = 'offline_queue_migrated_v1';
export const LEGACY_STORAGE_KEY = 'offline_queue';
