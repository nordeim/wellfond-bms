"use client";

import { useState, useEffect, useCallback } from "react";
import { useToast } from "@/components/ui/use-toast";
import type { OfflineQueueItem } from "@/lib/offline-queue";
import {
  getQueue,
  addToQueue,
  removeFromQueue,
  getQueueCount,
} from "@/lib/offline-queue";

export function useOfflineQueue() {
  const [isOnline, setIsOnline] = useState(true);
  const [queue, setQueue] = useState<OfflineQueueItem[]>([]);
  const [queueLoaded, setQueueLoaded] = useState(false);
  const [queueLength, setQueueLength] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const { toast } = useToast();

  // Async load queue from IndexedDB on mount
  useEffect(() => {
    (async () => {
      try {
        const items = await getQueue();
        setQueue(items);
        setQueueLength(await getQueueCount());
      } finally {
        setQueueLoaded(true);
      }
    })();
  }, []);

  const refreshQueue = useCallback(async () => {
    const items = await getQueue();
    setQueue(items);
    setQueueLength(await getQueueCount());
  }, []);

  // Track online status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      toast({
        title: "Back online",
        description: "Syncing pending logs...",
      });
      processQueue();
    };

    const handleOffline = () => {
      setIsOnline(false);
      toast({
        title: "Offline mode",
        description: "Logs will be saved locally",
      });
    };

    setIsOnline(navigator.onLine);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [toast]);

  const processQueue = useCallback(async () => {
    if (isProcessing || !navigator.onLine) return;

    const currentQueue = await getQueue();
    if (currentQueue.length === 0) return;

    setIsProcessing(true);

    const failed: OfflineQueueItem[] = [];
    let synced = 0;

    for (const item of currentQueue) {
      try {
        const response = await fetch(item.url, {
          method: item.method,
          headers: {
            "Content-Type": "application/json",
            ...item.headers,
          },
          body: item.body ? JSON.stringify(item.body) : null,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        await removeFromQueue(item.id);
        synced++;
      } catch {
        if (item.retryCount < 3) {
          const { incrementRetry } = await import("@/lib/offline-queue");
          await incrementRetry(item.id);
          failed.push({ ...item, retryCount: item.retryCount + 1 });
        }
      }
    }

    await refreshQueue();
    setIsProcessing(false);

    if (synced > 0) {
      toast({
        title: "Sync complete",
        description: `${synced} logs synced`,
      });
    }
  }, [isProcessing, toast, refreshQueue]);

  const queueRequest = useCallback(
    async <T>(requestFn: () => Promise<T>): Promise<T> => {
      if (navigator.onLine) {
        return requestFn();
      }

      await addToQueue({
        method: "POST",
        url: "",
        body: undefined,
        headers: {},
      });

      await refreshQueue();

      return new Promise((resolve, reject) => {
        const checkInterval = setInterval(() => {
          if (navigator.onLine) {
            clearInterval(checkInterval);
            processQueue().then(() => {
              requestFn().then(resolve).catch(reject);
            });
          }
        }, 1000);

        setTimeout(() => {
          clearInterval(checkInterval);
          reject(new Error("Request queued for sync"));
        }, 30000);
      });
    },
    [processQueue, refreshQueue]
  );

  return {
    isOnline,
    queue,
    queueLoaded,
    queueLength,
    isProcessing,
    queueRequest,
    processQueue,
  };
}