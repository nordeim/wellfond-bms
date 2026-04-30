/**
 * Offline Queue - Framework-Agnostic Module
 * ==========================================
 * IndexedDB-backed queue for offline ground operations (PWA).
 * TODO: Migrate from localStorage to IndexedDB for production.
 */

const STORAGE_KEY = "offline_queue";

export interface OfflineQueueItem {
  id: string;
  method: "GET" | "POST" | "PUT" | "DELETE";
  url: string;
  body?: unknown;
  headers?: Record<string, string>;
  timestamp: number;
  retryCount: number;
}

function generateId(): string {
  return crypto.randomUUID();
}

function readStorage(): OfflineQueueItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function writeStorage(items: OfflineQueueItem[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export function getQueue(): OfflineQueueItem[] {
  return readStorage();
}

export function addToQueue(
  item: Omit<OfflineQueueItem, "id" | "timestamp" | "retryCount">
): OfflineQueueItem {
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

export function removeFromQueue(id: string): void {
  const queue = readStorage().filter((i) => i.id !== id);
  writeStorage(queue);
}

export function getQueueCount(): number {
  return readStorage().length;
}

export function clearQueue(): void {
  writeStorage([]);
}

export function incrementRetry(id: string): void {
  const queue = readStorage().map((i) =>
    i.id === id ? { ...i, retryCount: i.retryCount + 1 } : i
  );
  writeStorage(queue);
}