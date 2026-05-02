/**
 * Offline Queue — Re-export from proper IndexedDB implementation.
 *
 * This file previously used localStorage which is inaccessible from
 * Service Workers. Now delegates to the IndexedDB-backed implementation
 * at lib/offline-queue/index.ts with adapter auto-detection
 * (IndexedDB > localStorage > in-memory fallback).
 */

export {
  getQueue,
  addToQueue,
  removeFromQueue,
  getQueueCount,
  clearQueue,
  incrementRetry,
  resetAdapter,
  getAdapterName,
  getQueueSync,
  addToQueueSync,
} from './offline-queue/index';

export type { OfflineQueueItem, OfflineQueueItemCreate } from './offline-queue/types';

export { default } from './offline-queue/index';