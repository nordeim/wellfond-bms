# Phase‑0 Audit — Current Code & Callers

## 1. Code Audit Results

### 1.1 What `frontend/lib/offline-queue.ts` Actually Does

| Function | Storage Operation | Notes |
|---|---|---|
| `getQueue()` | `localStorage.getItem` → `JSON.parse` | Synchronous, blocks main thread |
| `addToQueue(item)` | read → push → `JSON.stringify` → `setItem` | Full array serialisation on every enqueue |
| `removeFromQueue(id)` | read → filter → write | O(n) scan + full re-serialisation |
| `getQueueCount()` | `readStorage().length` | Reads & parses entire array just to get length |
| `clearQueue()` | `setItem(STORAGE_KEY, '[]')` | Simple overwrite, no delete |
| `incrementRetry(id)` | read → map → write | Full array read-modify-write |

### 1.2 Critical Issues with Current Approach

*   **Synchronous blocking**: `JSON.parse`/`JSON.stringify` on a growing array runs on the main thread, causing UI jank. MDN confirms: “This synchronous behavior can potentially affect the performance of the web application, especially if there is a large amount of data being stored or retrieved. Asynchronous alternatives, such as **IndexedDB**, may be more suitable.”
*   **No partial updates**: The entire queue is serialised/deserialised for every operation, even for incrementing a counter. IndexedDB supports **single-record updates** without touching the rest of the store.
*   **Storage cap ~5 MB**: localStorage is typically limited to 5 MB per origin, shared across the whole app.
*   **No transaction isolation**: Multiple tabs can read/write simultaneously, corrupting data.
*   **No quota awareness**: Writing to a full localStorage just throws `QuotaExceededError` without any recovery.

### 1.3 Data Volume Estimate

For a typical offline queue in a PWA (ground‑operations app):

| Item | Typical JSON size | At 100 items | At 1 000 items |
|---|---|---|---|
| `OfflineQueueItem` | ~200–500 bytes | ~20–50 KB | ~200–500 KB |
| Edge case (POST with large body) | ~5 KB | ~500 KB | ~5 MB |

Even at 1 000 items, the serialisation cost is noticeable. IndexedDB’s **`store.count()`** avoids reading data entirely, and **`getAll()`** returns structured objects without manual JSON parsing.

---

# Phase‑1 — IndexedDB Fundamentals

## 2. Key IndexedDB Concepts

### 2.1 The `onupgradeneeded` Event — Schema Management

IndexedDB uses a **version number** for schema changes. The `onupgradeneeded` event fires when a database is first created or when the version number is increased — this is where you create object stores and indexes.

```
request.onupgradeneeded = (event) => {
  const db = event.target.result;
  // Only place to create/delete object stores & indexes
  const store = db.createObjectStore('queue', { keyPath: 'id' });
  store.createIndex('byTimestamp', 'timestamp');
  store.createIndex('byRetryCount', 'retryCount');
};
```

### 2.2 Transaction Lifetime — Auto‑Commit

IndexedDB transactions **auto‑commit** when the browser determines there are no more pending requests. As Jake Archibald’s `idb` documentation warns: **“Do not `await` other things between the start and end of your transaction, otherwise the transaction will close before you're done.”**

This means:

*   All IndexedDB operations within a transaction must be chained together without interleaved `await` calls for external work.
*   The `idb` library provides `tx.done` — a promise that resolves when the transaction successfully commits. Always `await tx.done` after all store operations.

### 2.3 `getAll()` vs Cursor — Performance

For fetching **all records** (which is what `getQueue()` does), `IDBObjectStore.getAll()` is significantly faster than cursor iteration. Cursors require explicit `continue()` calls per record, creating overhead: “Since cursors return a single value at a time, and returning values is an asynchronous operation, the performance will be lower than getAll() to fetch multiple values.” `getAll()` gets a further ~50% performance boost in modern Chrome (SQLite backend).

**Recommendation for `getQueue()`**: Use `db.getAll('queue')` (or `store.getAll()`), not a cursor.

### 2.4 Atomic Updates with `IDBCursor.update()`

For `incrementRetry()`, the optimal pattern uses `IDBCursor.update()` within a read‑write transaction. This allows updating the `retryCount` field **without a separate read‑then‑write** and without serialising/deserialising other records.

```
const tx = db.transaction('queue', 'readwrite');
let cursor = await tx.store.openCursor(id);
if (cursor) {
  const item = cursor.value;
  item.retryCount += 1;
  await cursor.update(item);
}
await tx.done;
```

This is the **clean, atomic** equivalent of the current `incrementRetry` that reads, maps, and rewrites the whole array.

---

# Phase‑2 — Technology Survey & Library Selection

## 3. Comparison Matrix

| Library | Brotli Size | API Level | Transaction Support | Multi‑tab Safe | Migration Helper | TypeScript Types |
|---|---|---|---|---|---|---|
| **Raw IndexedDB** | 0 KB | Low‑level events | Full | Yes ⚠ | Manual | Via `lib.dom` |
| **`idb`** (Jake Archibald) | **~1.19 KB** | Promise‑based, mirrors IDB | Full (`tx.done`) | Yes ⚠ | Manual | Built‑in + generic |
| **`idb-keyval`** | ~250–534 B | Minimal `get`/`set` | Limited (single‑key) | Yes | Manual | Basic |
| **`localforage`** | ~7.4 KB | localStorage‑like API | Abstracted | Yes | Via driver config | Via `@types` |
| **`Dexie.js`** | ~15 KB | ORM‑like, query builder | Rich | Yes | `Dexie.on.populate` | Full generics |

### 3.1 Why `idb` Wins for This Project

*   **Minimal cost**: 1.19 KB brotli’d — negligible bundle impact.
*   **Full IndexedDB power**: Object stores, indexes, cursors, transactions — all available.
*   **Promise‑based**: Eliminates the event‑driven boilerplate (“turns all `IDBRequest` objects into promises”).
*   **`tx.done`**: Provides a clear commit signal.
*   **TypeScript generics**: `openDB<MyDB>(...)` with schema definitions that catch errors at compile time.
*   **Async iterators**: `for await (const cursor of tx.store)` simplifies batch operations.

**What about `idb-keyval`?** It’s too minimal — it wraps IndexedDB into a key‑value store, but lacks index support for ordering or querying by retry count. We need indexes for `getQueue()` ordering and `incrementRetry` atomicity.

**What about `localforage`?** Too heavy (~7.4 KB) for what we need, and abstracts away IndexedDB specifics that we actually want to control (transactions, indexes).

**What about raw IndexedDB?** Viable, but the boilerplate for error handling, transaction management, and `onupgradeneeded` versioning adds significant code that `idb` handles cleanly.

**Decision: Use `idb` (~1.19 KB), the thinnest practical wrapper.**

---

# Phase‑3 — Schema & API Design

## 4. Database Schema

```
Database: "offline-queue-db"
Version: 1

Object Store: "queue"
  keyPath: "id"                    // UUID string

Indexes:
  "byTimestamp"    → timestamp     // For ordered retrieval
  "byRetryCount"   → retryCount    // For retry prioritisation
```

### 4.1 TypeScript Schema Definition

```typescript
import { DBSchema } from 'idb';

interface OfflineQueueItem {
  id: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  url: string;
  body?: unknown;
  headers?: Record<string, string>;
  timestamp: number;
  retryCount: number;
}

interface OfflineQueueDB extends DBSchema {
  queue: {
    key: string;                    // id
    value: OfflineQueueItem;
    indexes: {
      'byTimestamp': number;        // timestamp
      'byRetryCount': number;       // retryCount
    };
  };
}
```

## 5. API Mapping — Each Function’s IndexedDB Equivalent

| Function | IndexedDB Operation | Notes |
|---|---|---|
| `getQueue()` | `db.getAll('queue')` | Returns all records. For ordering: use `db.getAllFromIndex('queue', 'byTimestamp')` |
| `addToQueue(item)` | `db.put('queue', queueItem)` | `put` with explicit key (`id` generated via `crypto.randomUUID()`) |
| `removeFromQueue(id)` | `db.delete('queue', id)` | Direct key deletion |
| `getQueueCount()` | `db.count('queue')` | O(1) — no data read |
| `clearQueue()` | `db.clear('queue')` | Single operation, no iteration |
| `incrementRetry(id)` | Cursor → `cursor.update()` | Atomic read‑modify‑write |

### 5.1 Why `put` Instead of `add` for `addToQueue`

*   `add` fails if a record with the same key already exists.
*   `put` inserts or overwrites. Since we generate a unique UUID for each item, either works, but `put` is safer in case idempotent retry or migration re‑inserts are needed.

### 5.2 `getQueue()` — Ordered Retrieval

```typescript
// Returns queue items ordered by timestamp ascending (oldest first)
export async function getQueue(): Promise<OfflineQueueItem[]> {
  const db = await dbPromise;
  return db.getAllFromIndex('queue', 'byTimestamp');
}
```

### 5.3 `incrementRetry(id)` — Atomic Update

```typescript
export async function incrementRetry(id: string): Promise<void> {
  const db = await dbPromise;
  const tx = db.transaction('queue', 'readwrite');
  const store = tx.objectStore('queue');
  const cursor = await store.openCursor(id);
  if (cursor) {
    const item = { ...cursor.value, retryCount: cursor.value.retryCount + 1 };
    await cursor.update(item);
  }
  await tx.done;
}
```

---

# Phase‑4 — Migration Strategy

## 6. One‑Time Migration from localStorage to IndexedDB

### 6.1 Approach

Perform migration **inside the `upgrade` callback** of `openDB`. This ensures the migration happens atomically as part of the schema creation, and no other consumer can access the database until migration completes.

```typescript
const MIGRATION_FLAG_KEY = 'offline_queue_migrated';

async function openOfflineQueueDB(): Promise<IDBPDatabase<OfflineQueueDB>> {
  const storedQueue = readStoredQueue(); // read localStorage once, synchronously

  const db = await openDB<OfflineQueueDB>('offline-queue-db', 1, {
    upgrade(db) {
      // Create object store & indexes
      const store = db.createObjectStore('queue', { keyPath: 'id' });
      store.createIndex('byTimestamp', 'timestamp');
      store.createIndex('byRetryCount', 'retryCount');

      // Perform one-time migration if localStorage has data
      if (
        storedQueue.length > 0 &&
        !localStorage.getItem(MIGRATION_FLAG_KEY)
      ) {
        for (const item of storedQueue) {
          store.put(item);
        }
        localStorage.setItem(MIGRATION_FLAG_KEY, '1');
      }
    },
  });

  // Clean up localStorage after successful migration
  if (localStorage.getItem(MIGRATION_FLAG_KEY)) {
    localStorage.removeItem(STORAGE_KEY);
  }

  return db;
}
```

### 6.2 Key Design Decisions

*   **Read localStorage before `openDB`**: localStorage is synchronous and immediate; IndexedDB opening is async. We capture the existing queue while we still have a synchronous reference.
*   **Migration flag in localStorage**: Prevents re‑importing on subsequent opens even if `onupgradeneeded` fires again (which it shouldn’t at the same version).
*   **Cleanup**: Remove the old `offline_queue` key from localStorage only **after** confirming the migration flag is set, avoiding data loss if the database open fails.
*   **Flat data model**: Since the existing localStorage data is already an array of `OfflineQueueItem` objects, the migration is a simple direct `put` for each item — no transformation needed.

---

# Phase‑5 — Error Handling & Edge Cases

## 7. Comprehensive Error Handling Strategy

### 7.1 Database Open Failures (Private Browsing)

Safari private mode may silently reject IndexedDB opens; Firefox private windows fire `error` events on `indexedDB.open()` even though `window.indexedDB` exists. Relying on feature detection (checking if `window.indexedDB` exists) is insufficient.

**Solution**: Feature‑test by actually opening the database and catching failures:

```typescript
let dbPromise: Promise<IDBPDatabase<OfflineQueueDB>> | null = null;

async function getDB(): Promise<IDBPDatabase<OfflineQueueDB>> {
  if (dbPromise) return dbPromise;

  dbPromise = openOfflineQueueDB().catch((err) => {
    console.warn('IndexedDB unavailable, falling back to localStorage', err);
    // Re-export sync localStorage adapter functions here
    throw err; // Let callers handle the fallback
  });

  return dbPromise;
}
```

If the database cannot be opened:

*   The module falls back to the **existing localStorage implementation** as a temporary adapter.
*   A `getQueue()` that used to be synchronous must become **async** in the public API — consumers need to `await` it whether it hits IndexedDB or localStorage.
*   For private browsing contexts where even localStorage may fail (Safari 17+), the fallback is an **in‑memory Map** that logs a warning but keeps the app functional for the session.

### 7.2 `QuotaExceededError` Handling

IndexedDB writes can fail with `QuotaExceededError` when the browser’s storage limit is hit — particularly in incognito/private mode (sometimes <1 MB).

```typescript
export async function addToQueue(item: Omit<OfflineQueueItem, 'id' | 'timestamp' | 'retryCount'>): Promise<OfflineQueueItem> {
  const db = await getDBIfAvailable();
  if (!db) return addToLocalStorageFallback(item);

  const queueItem: OfflineQueueItem = {
    ...item,
    id: generateId(),
    timestamp: Date.now(),
    retryCount: 0,
  };

  try {
    await db.put('queue', queueItem);
    return queueItem;
  } catch (err) {
    if (err instanceof DOMException && err.name === 'QuotaExceededError') {
      // Option 1: Reject with distinguishable error
      throw new QuotaExceededError('Offline queue storage full');
      // Option 2: Silent fallback to localStorage (smaller quota)
      // Option 3: Trim oldest items (LRU eviction)
    }
    throw err;
  }
}
```

For proactive monitoring, use `navigator.storage.estimate()` to check usage ratio before writes:

```typescript
async function getStorageUsage(): Promise<{ usage: number; quota: number } | null> {
  if (navigator.storage?.estimate) {
    return navigator.storage.estimate();
  }
  return null;
}
```

### 7.3 `blocked` Event — Multi‑Tab Version Changes

When the database version is bumped (e.g., schema upgrade), other open tabs hold connections that block the version change transaction. IndexedDB fires a `blocked` event on the `IDBOpenDBRequest` in the tab initiating the upgrade, and a `versionchange` event on existing connections in other tabs.

**Mitigation with `idb`**: Use the `blocked` callback in `openDB`:

```typescript
await openDB<OfflineQueueDB>('offline-queue-db', 1, {
  upgrade(db) { /* ... */ },
  blocked(currentVersion, blockedVersion, event) {
    // Inform the user to close other tabs, or call db.close() in other tabs
    console.warn(
      `Database upgrade blocked: version ${blockedVersion} waiting for version ${currentVersion} to close`
    );
  },
});
```

In production, the typical approach is to listen for `versionchange` on the open database and gracefully close it:

```typescript
db.addEventListener('versionchange', () => {
  db.close();
  console.log('Database connection closed due to version change in another tab');
  dbPromise = null; // Force re-open on next access
});
```

### 7.4 Transaction Failures

Any unhandled exception within a transaction aborts the entire transaction. The `tx.done` promise rejects with the abort error. Always await `tx.done` after transactional operations and handle the rejection:

```typescript
try {
  const tx = db.transaction('queue', 'readwrite');
  await tx.store.put(item);
  await tx.done; // Ensure commit
} catch (err) {
  // Transaction aborted — item not persisted
  // Retry or report error
}
```

---

# Phase‑6 — Performance & Testing Strategy

## 8. Performance Validation

### 8.1 Benchmarks to Run

| Scenario | Metric | Target |
|---|---|---|
| `getQueue()` with 1 000 items | Time to return | < 50 ms |
| `addToQueue()` with 10 000 items | Time per enqueue | < 10 ms |
| `getQueueCount()` (vs localStorage read+parse) | Speedup | > 10× |
| Concurrent writes (2 tabs) | Data integrity | No loss or corruption |
| `incrementRetry()` on single item | Time | < 5 ms |

### 8.2 Why These Targets Are Achievable

*   `store.count()` is an O(1) operation in IndexedDB — no data read.
*   `getAll()` avoids per‑record cursor overhead.
*   Bulk migration of 1 000 items within a single transaction is efficient; safe chunk size is 500–1 000 records per transaction.
*   IndexedDB’s transaction model guarantees isolation between tabs, preventing the race conditions that can corrupt localStorage data.

## 9. Testing Strategy

### 9.1 Unit Testing with `fake-indexeddb`

Use `fake-indexeddb` to simulate IndexedDB in a Jest/Node environment. This is the established approach for testing IndexedDB code without a browser.

**Jest setup** (`jest.setup.ts`):

```typescript
import 'fake-indexeddb/auto';
```

Or in `jest.config`:

```json
{
  "setupFiles": ["fake-indexeddb/auto"]
}
```

### 9.2 Test Cases

| Test | What it Verifies |
|---|---|
| `addToQueue` → `getQueue` | Items are persisted and retrievable in timestamp order |
| `addToQueue` with 1 000 items | No errors, reasonable performance |
| `removeFromQueue` (existing id) | Item removed, count decrements |
| `removeFromQueue` (non‑existent id) | No error, queue unchanged |
| `incrementRetry` | `retryCount` increments by exactly 1 |
| `clearQueue` | All items removed, count = 0 |
| `getQueueCount` on empty store | Returns 0 |
| Concurrency: 2 writes in parallel | Both items appear in final queue |
| Migration: localStorage has data | After first `openDB`, all items in IndexedDB, localStorage cleared |
| Migration: no localStorage data | Empty IndexedDB store |
| Migration: flag already set | No re‑import |
| `QuotaExceededError` simulation | Error propagates correctly, data not corrupted |
| Fallback when IndexedDB unavailable | Falls back to localStorage adapter |

### 9.3 Edge‑Case Tests

*   **Empty queue operations**: `removeFromQueue` and `incrementRetry` on an empty store should not throw.
*   **Large payload**: Enqueue an item with a 10 KB body; verify retrieval is byte‑perfect.
*   **Duplicate ID**: `put` with an existing ID should overwrite (idempotent).
*   **Database deletion**: Calling `clearQueue` then `getQueue` returns `[]` immediately.
*   **Version upgrade**: Opening DB with version 2 should handle existing v1 data gracefully.

### 9.4 Integration Testing

*   **Offline → online sync simulation**: In a browser test (Cypress/Playwright), toggle network offline, enqueue items, toggle online, verify flush.
*   **Multi‑tab test**: Open two browser tabs to the app; add items in one tab; verify they appear in the other tab’s read (IndexedDB changes propagate across same‑origin connections).

---

# Implementation Blueprint — Summary

## 10. Final Architecture

```
src/lib/offline-queue/
├── index.ts          # Public async API (re-exports)
├── db.ts             # IndexedDB connection, schema, migration
├── adapter.idb.ts    # IndexedDB-backed queue operations
├── adapter.ls.ts     # localStorage fallback (sync, wrapper over existing)
├── adapter.memory.ts # In-memory fallback (for private browsing)
├── types.ts          # OfflineQueueItem, OfflineQueueDB schema
└── __tests__/
    ├── offline-queue.test.ts     # Unit tests (fake-indexeddb)
    └── migration.test.ts         # Migration tests
```

### 10.1 Key Decisions Summary

| Decision | Choice | Rationale |
|---|---|---|
| **Wrapper library** | `idb` (~1.19 KB) | Thinnest practical layer; full transaction + index support |
| **API signature** | All functions return `Promise` | IndexedDB is async; localStorage fallback wraps in `Promise.resolve()` |
| **Schema** | Single object store `queue`, keyed by `id` | Direct mapping from existing `OfflineQueueItem` |
| **Indexes** | `byTimestamp`, `byRetryCount` | Supports ordered retrieval and future retry‑priority features |
| **Migration trigger** | Inside `upgrade` callback of version 1 | Atomic, no race with other consumers |
| **Quota exceeded** | Catch `DOMException`, reject with typed error | Caller decides: alert user, fall back, or trim |
| **Private browsing** | Try IndexedDB → localStorage → in‑memory Map | Graceful degradation without data loss within a session |
| **Testing** | `fake-indexeddb` for unit tests; browser for integration | Industry standard for IndexedDB unit testing |

### 10.2 Next Steps (Execution Order)

1.  Install `idb` dependency: `npm install idb`.
2.  Create `src/lib/offline-queue/db.ts` with database schema, `openDB` call, and migration logic.
3.  Create `src/lib/offline-queue/adapter.idb.ts` with all six queue functions implemented against IndexedDB.
4.  Create `src/lib/offline-queue/adapter.ls.ts` wrapping the existing localStorage code in Promises.
5.  Create `src/lib/offline-queue/adapter.memory.ts` as last‑resort fallback.
6.  Create `src/lib/offline-queue/index.ts` that autodetects storage availability and delegates to the correct adapter.
7.  Update all callers to `await` the now‑async functions.
8.  Write unit tests covering all scenarios in §9.2.
9.  Run performance benchmarks, iterate if needed.
10. Remove the old `frontend/lib/offline-queue.ts` after validation.

This plan produces a production‑grade, IndexedDB‑backed offline queue that is fully backward‑compatible (via one‑time migration), gracefully handles edge cases, adds < 2 KB to the bundle, and passes comprehensive automated tests.
