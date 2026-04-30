/**
 * TDD Test: lib/offline-queue.ts
 * ===============================
 * Framework-agnostic offline queue module.
 */
import { describe, it, expect, beforeEach } from "vitest";

let offlineQueue: typeof import("@/lib/offline-queue");

beforeEach(async () => {
  localStorage.clear();
  offlineQueue = await import("@/lib/offline-queue");
});

describe("offline-queue module", () => {
  it("getQueue returns empty array initially", () => {
    expect(offlineQueue.getQueue()).toEqual([]);
  });

  it("getQueueCount returns 0 initially", () => {
    expect(offlineQueue.getQueueCount()).toBe(0);
  });

  it("addToQueue adds an item with UUIDv4 id", () => {
    offlineQueue.addToQueue({
      method: "POST",
      url: "/api/proxy/logs/in-heat",
      body: { draminski_reading: 350 },
    });
    const queue = offlineQueue.getQueue();
    expect(queue).toHaveLength(1);
    expect(queue[0].id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
    );
  });

  it("getQueueCount reflects queue size", () => {
    offlineQueue.addToQueue({
      method: "POST",
      url: "/api/proxy/logs/health",
      body: { category: "LIMPI NG" },
    });
    offlineQueue.addToQueue({
      method: "POST",
      url: "/api/proxy/logs/weight",
      body: { weight: 5.5 },
    });
    expect(offlineQueue.getQueueCount()).toBe(2);
  });

  it("removeFromQueue removes item by id", () => {
    offlineQueue.addToQueue({
      method: "POST",
      url: "/api/proxy/logs/weight",
      body: { weight: 8.0 },
    });
    const [item] = offlineQueue.getQueue();
    offlineQueue.removeFromQueue(item.id);
    expect(offlineQueue.getQueueCount()).toBe(0);
  });

  it("clearQueue empties all items", () => {
    offlineQueue.addToQueue({ method: "POST", url: "/test", body: {} });
    offlineQueue.addToQueue({ method: "POST", url: "/test", body: {} });
    offlineQueue.addToQueue({ method: "POST", url: "/test", body: {} });
    expect(offlineQueue.getQueueCount()).toBe(3);
    offlineQueue.clearQueue();
    expect(offlineQueue.getQueueCount()).toBe(0);
  });

  it("addToQueue sets timestamp and retryCount", () => {
    offlineQueue.addToQueue({
      method: "DELETE",
      url: "/api/proxy/test",
    });
    const [item] = offlineQueue.getQueue();
    expect(typeof item.timestamp).toBe("number");
    expect(item.retryCount).toBe(0);
  });
});