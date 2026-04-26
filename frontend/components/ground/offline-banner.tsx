"use client";

import { useState, useEffect } from "react";
import { Wifi, WifiOff } from "lucide-react";

import { Alert } from "@/components/ui/alert";

export function OfflineBanner() {
  const [isOnline, setIsOnline] = useState(true);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const updateOnlineStatus = () => {
      const online = navigator.onLine;
      setIsOnline(online);
      setShowBanner(!online);
    };

    // Initial check
    updateOnlineStatus();

    // Event listeners
    window.addEventListener("online", () => {
      setIsOnline(true);
      // Show "back online" briefly then hide
      setTimeout(() => setShowBanner(false), 3000);
    });
    window.addEventListener("offline", () => {
      setIsOnline(false);
      setShowBanner(true);
    });

    return () => {
      window.removeEventListener("online", updateOnlineStatus);
      window.removeEventListener("offline", updateOnlineStatus);
    };
  }, []);

  if (!showBanner) return null;

  return (
    <Alert
      className={`fixed top-0 left-0 right-0 z-50 rounded-none ${
        isOnline
          ? "bg-green-900/90 border-green-600 text-green-100"
          : "bg-amber-900/90 border-amber-600 text-amber-100"
      }`}
    >
      <div className="flex items-center justify-center gap-2">
        {isOnline ? (
          <>
            <Wifi className="w-4 h-4" />
            <span className="font-medium">Back online</span>
          </>
        ) : (
          <>
            <WifiOff className="w-4 h-4" />
            <span className="font-medium">Offline mode - logs will sync when connected</span>
          </>
        )}
      </div>
    </Alert>
  );
}
