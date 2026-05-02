/**
 * TDD Test: lib/offline-queue.ts
 * ===============================
 * Framework-agnostic offline queue module (IndexedDB-backed with adapters).
 */

import { describe, it, expect, beforeEach } from "vitest";

let offlineQueue: typeof import("@/lib/offline-queue");

beforeEach(async () => {
  // Clean up from previous test runs
  if (typeof localStorage !== "undefined") {
    localStorage.clear();
  }
  offlineQueue = await import("@/lib/offline-queue");
  // Reset adapter to force localStorage fallback in test environment (no IndexedDB)
  if (offlineQueue.resetAdapter) {
    offlineQueue.resetAdapter();
  }
  // Clear any queued items
  await offlineQueue.clearQueue();
});

describe("offline-queue module", () => {
  it("getQueue returns empty array initially", async () => {
    expect(await offlineQueue.getQueue()).toEqual([]);
  });

  it("getQueueCount returns 0 initially", async () => {
    expect(await offlineQueue.getQueueCount()).toBe(0);
  });

  it("addToQueue adds an item with UUIDv4 id", async () => {
    await offlineQueue.addToQueue({
      method: "POST",
      url: "/api/proxy/logs/in-heat",
      body: { draminski_reading: 350 },
    });
    const queue = await offlineQueue.getQueue();
    expect(queue).toHaveLength(1);
    expect(queue[0].id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
    );
  });

  it("getQueueCount reflects queue size", async () => {
    await offlineQueue.addToQueue({
      method: "POST",
      url: "/api/proxy/logs/health",
      body: { category: "LIMPING" },
    });
    await offlineQueue.addToQueue({
      method: "POST",
      url: "/api/proxy/logs/weight",
      body: { weight: 5.5 },
    });
    expect(await offlineQueue.getQueueCount()).toBe(2);
  });

  it("removeFromQueue removes item by id", async () => {
    await offlineQueue.addToQueue({
      method: "POST",
      url: "/api/proxy/logs/weight",
      body: { weight: 8.0 },
    });
    const [item] = await offlineQueue.getQueue();
    await offlineQueue.removeFromQueue(item.id);
    expect(await offlineQueue.getQueueCount()).toBe(0);
  });

  it("clearQueue empties all items", async () => {
    await offlineQueue.addToQueue({ method: "POST", url: "/test", body: {} });
    await offlineQueue.addToQueue({ method: "POST", url: "/test", body: {} });
    await offlineQueue.addToQueue({ method: "POST", url: "/test", body: {} });
    expect(await offlineQueue.getQueueCount()).toBe(3);
    await offlineQueue.clearQueue();
    expect(await offlineQueue.getQueueCount()).toBe(0);
  });

  it("addToQueue sets timestamp and retryCount", async () => {
    await offlineQueue.addToQueue({
      method: "DELETE",
      url: "/api/proxy/test",
    });
    const [item] = await offlineQueue.getQueue();
    expect(typeof item.timestamp).toBe("number");
    expect(item.retryCount).toBe(0);
  });
});