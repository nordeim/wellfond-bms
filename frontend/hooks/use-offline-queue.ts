"use client";

import { useState, useEffect, useCallback } from "react";
import { useToast } from "@/components/ui/use-toast";

interface OfflineQueueItem {
  id: string;
  method: "GET" | "POST" | "PUT" | "DELETE";
  url: string;
  body?: unknown;
  headers?: Record<string, string>;
  timestamp: number;
  retryCount: number;
}

export function useOfflineQueue() {
  const [isOnline, setIsOnline] = useState(true);
  const [queue, setQueue] = useState<OfflineQueueItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const { toast } = useToast();

  // Track online status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      toast({
        title: "Back online",
        description: "Syncing pending logs...",
      });
      // Trigger sync
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

    // Load queue from storage
    const stored = localStorage.getItem("offline_queue");
    if (stored) {
      try {
        setQueue(JSON.parse(stored));
      } catch {
        // Ignore parse errors
      }
    }

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [toast]);

  // Save queue to storage
  useEffect(() => {
    localStorage.setItem("offline_queue", JSON.stringify(queue));
  }, [queue]);

  // Process queue
  const processQueue = useCallback(async () => {
    if (isProcessing || !navigator.onLine || queue.length === 0) return;

    setIsProcessing(true);

    const failed: OfflineQueueItem[] = [];

    for (const item of queue) {
      try {
        const response = await fetch(item.url, {
          method: item.method,
          headers: {
            "Content-Type": "application/json",
            ...item.headers,
          },
          body: item.body ? JSON.stringify(item.body) : undefined,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
      } catch (error) {
        // Retry up to 3 times
        if (item.retryCount < 3) {
          failed.push({ ...item, retryCount: item.retryCount + 1 });
        }
      }
    }

    setQueue(failed);
    setIsProcessing(false);

    if (failed.length === 0 && queue.length > 0) {
      toast({
        title: "Sync complete",
        description: `${queue.length} logs synced`,
      });
    }
  }, [queue, isProcessing, toast]);

  // Queue a request
  const queueRequest = useCallback(
    async <T>(requestFn: () => Promise<T>): Promise<T> => {
      // If online, execute immediately
      if (navigator.onLine) {
        return requestFn();
      }

      // Offline - add to queue
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const item: OfflineQueueItem = {
        id,
        method: "POST",
        url: "", // Will be extracted from requestFn
        body: undefined,
        headers: {},
        timestamp: Date.now(),
        retryCount: 0,
      };

      setQueue((prev) => [...prev, item]);

      // Return a promise that resolves when synced
      return new Promise((resolve, reject) => {
        const checkInterval = setInterval(() => {
          if (navigator.onLine) {
            clearInterval(checkInterval);
            processQueue().then(() => {
              // Re-execute the request
              requestFn().then(resolve).catch(reject);
            });
          }
        }, 1000);

        // Timeout after 30 seconds
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
    queueLength: queue.length,
    isProcessing,
    queueRequest,
    processQueue,
  };
}
