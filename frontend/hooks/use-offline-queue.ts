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
  const [isProcessing, setIsProcessing] = useState(false);
  const { toast } = useToast();

  // Sync queue state with storage on mount
  useEffect(() => {
    setQueue(getQueue());
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

    const currentQueue = getQueue();
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

        removeFromQueue(item.id);
        synced++;
      } catch {
        if (item.retryCount < 3) {
          const { incrementRetry } = await import("@/lib/offline-queue");
          incrementRetry(item.id);
          failed.push({ ...item, retryCount: item.retryCount + 1 });
        }
      }
    }

    setQueue(getQueue());
    setIsProcessing(false);

    if (synced > 0) {
      toast({
        title: "Sync complete",
        description: `${synced} logs synced`,
      });
    }
  }, [isProcessing, toast]);

  const queueRequest = useCallback(
    async <T>(requestFn: () => Promise<T>): Promise<T> => {
      if (navigator.onLine) {
        return requestFn();
      }

      addToQueue({
        method: "POST",
        url: "",
        body: undefined,
        headers: {},
      });

      setQueue(getQueue());

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
    [processQueue]
  );

  return {
    isOnline,
    queue,
    queueLength: getQueueCount(),
    isProcessing,
    queueRequest,
    processQueue,
  };
}