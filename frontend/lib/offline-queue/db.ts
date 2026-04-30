/**
 * IndexedDB Database Connection
 * ============================
 * Database setup, schema creation, and migration from localStorage.
 */

import { openDB, DBSchema, IDBPDatabase } from 'idb';
import type { OfflineQueueItem } from './types';
import { DB_NAME, DB_VERSION, STORE_NAME, MIGRATION_FLAG_KEY, LEGACY_STORAGE_KEY } from './types';

interface OfflineQueueDB extends DBSchema {
  queue: {
    key: string; // id
    value: OfflineQueueItem;
    indexes: {
      'byTimestamp': number;
      'byRetryCount': number;
    };
  };
}

let dbPromise: Promise<IDBPDatabase<OfflineQueueDB> | null> | null = null;

/**
 * Open or create the IndexedDB database.
 * Handles schema creation and one-time migration from localStorage.
 */
async function openOfflineQueueDB(): Promise<IDBPDatabase<OfflineQueueDB>> {
  // Read localStorage data BEFORE async open (synchronous)
  const legacyData = readLegacyLocalStorage();
  const needsMigration = legacyData.length > 0 && !localStorage.getItem(MIGRATION_FLAG_KEY);

  const db = await openDB<OfflineQueueDB>(DB_NAME, DB_VERSION, {
    upgrade(db, _oldVersion, _newVersion, transaction) {
      // Create object store with indexes
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        store.createIndex('byTimestamp', 'timestamp');
        store.createIndex('byRetryCount', 'retryCount');
      }

      // Perform one-time migration from localStorage
      if (needsMigration) {
        const store = transaction.objectStore(STORE_NAME);
        for (const item of legacyData) {
          store.put(item);
        }
        localStorage.setItem(MIGRATION_FLAG_KEY, '1');
      }
    },
    blocked(currentVersion, blockedVersion, _event) {
      console.warn(
        `Database upgrade blocked: version ${blockedVersion} waiting for version ${currentVersion} to close. ` +
        'Please close other tabs with this app open.'
      );
    },
  });

  // Clean up localStorage after successful migration
  if (needsMigration && localStorage.getItem(MIGRATION_FLAG_KEY)) {
    localStorage.removeItem(LEGACY_STORAGE_KEY);
  }

  // Listen for version changes from other tabs
  db.addEventListener('versionchange', () => {
    db.close();
    console.log('Database connection closed due to version change in another tab');
    dbPromise = null; // Force re-open on next access
  });

  return db;
}

/**
 * Get database instance (cached).
 * Falls back to null if IndexedDB is unavailable.
 */
export async function getDB(): Promise<IDBPDatabase<OfflineQueueDB> | null> {
  if (typeof window === 'undefined') return null; // SSR

  if (dbPromise) return dbPromise;

  dbPromise = openOfflineQueueDB().catch((err) => {
    console.warn('IndexedDB unavailable, will use fallback storage', err);
    return null;
  });

  return dbPromise;
}

/**
 * Check if IndexedDB is available.
 */
export async function isIndexedDBAvailable(): Promise<boolean> {
  const db = await getDB();
  return db !== null;
}

/**
 * Read legacy localStorage data synchronously.
 */
function readLegacyLocalStorage(): OfflineQueueItem[] {
  if (typeof window === 'undefined') return [];
  
  try {
    const raw = localStorage.getItem(LEGACY_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

/**
 * Clear the database connection (for testing).
 */
export function clearDBConnection(): void {
  dbPromise = null;
}

export type { OfflineQueueDB };
