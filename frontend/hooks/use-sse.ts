"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface Alert {
  id: number;
  type: string;
  dog_id: string;
  dog_name: string;
  message: string;
  severity: "info" | "warning" | "serious";
  created_at: string;
}

interface UseSSEOptions {
  url?: string;
  autoConnect?: boolean;
  reconnectDelay?: number;
  onMessage?: (alert: Alert) => void;
}

export function useSSE(options: UseSSEOptions = {}) {
  const {
    url = "/api/proxy/stream/alerts",
    autoConnect = true,
    reconnectDelay = 3000,
    onMessage,
  } = options;

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastEventId, setLastEventId] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // Create EventSource with last event ID for resumption
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
      console.log("[SSE] Connected");
    };

    es.onmessage = (event) => {
      // Handle heartbeat
      if (event.data.startsWith(":")) {
        return;
      }

      try {
        const data = JSON.parse(event.data);

        // Update last event ID
        if (event.lastEventId) {
          setLastEventId(event.lastEventId);
        }

        // Add alert to list
        setAlerts((prev) => {
          // Deduplicate by ID
          if (prev.some((a) => a.id === data.id)) {
            return prev;
          }
          return [...prev, data];
        });

        // Callback
        onMessage?.(data);
      } catch (error) {
        console.error("[SSE] Failed to parse message:", error);
      }
    };

    es.onerror = (error) => {
      console.error("[SSE] Error:", error);
      setIsConnected(false);

      // Close connection
      es.close();

      // Schedule reconnect
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      reconnectTimeoutRef.current = setTimeout(() => {
        console.log("[SSE] Reconnecting...");
        connect();
      }, reconnectDelay);
    };
  }, [url, reconnectDelay, onMessage]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Reconnect when visibility changes (user returns to tab)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible" && !isConnected) {
        connect();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [isConnected, connect]);

  return {
    alerts,
    isConnected,
    lastEventId,
    connect,
    disconnect,
    clearAlerts,
  };
}
