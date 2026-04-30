/**
 * PWA Service Worker Registration
 * ===============================
 * Registers the service worker and handles updates.
 * Provides utilities for update detection and offline queue management.
 */

import { toast } from "sonner";

/**
 * Service worker registration result
 */
interface RegistrationResult {
  /** Whether registration was successful */
  success: boolean;
  /** Service worker registration object (if successful) */
  registration?: ServiceWorkerRegistration;
  /** Error message (if failed) */
  error?: string;
}

/**
 * PWA registration options
 */
interface RegistrationOptions {
    /** Path to service worker file */
    swPath?: string;
    /** Scope of the service worker */
    scope?: string;
    /** Callback when update is available */
    onUpdateAvailable?: () => void;
    /** Callback when offline */
    onOffline?: () => void;
    /** Callback when online */
    onOnline?: () => void;
  }

  /**
   * Register the service worker
   */
  export async function registerServiceWorker(
    options: RegistrationOptions = {}
  ): Promise<RegistrationResult> {
    const {
      swPath = "/sw.js",
      scope = "/ground/",
      onUpdateAvailable,
      onOffline,
      onOnline,
    } = options;

    // Check if service workers are supported
    if (!("serviceWorker" in navigator)) {
      return {
        success: false,
        error: "Service workers not supported in this browser",
      };
    }

    try {
      // Register service worker
      const registration = await navigator.serviceWorker.register(swPath, {
        scope,
      });

      console.log("[PWA] Service worker registered:", registration.scope);

      // Handle updates
      registration.addEventListener("updatefound", () => {
        const newWorker = registration.installing;

        if (newWorker) {
          newWorker.addEventListener("statechange", () => {
            if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
              // New version available
              console.log("[PWA] Update available");
              onUpdateAvailable?.();
              showUpdateNotification();
            }
          });
        }
      });

      // Handle online/offline events
      window.addEventListener("online", () => {
        console.log("[PWA] Back online");
        onOnline?.();
        syncOfflineQueue();
      });

      window.addEventListener("offline", () => {
        console.log("[PWA] Went offline");
        onOffline?.();
        showOfflineNotification();
      });

      // Check initial connectivity
      if (!navigator.onLine) {
        onOffline?.();
      }

      return { success: true, registration };
    } catch (error) {
      console.error("[PWA] Service worker registration failed:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  /**
   * Show update notification
   */
  function showUpdateNotification(): void {
    toast.info("Update Available", {
      description: "A new version is available. Refresh to update?",
      action: {
        label: "Refresh",
        onClick: () => window.location.reload(),
      },
      duration: 10000,
    });
  }

  /**
   * Show offline notification
   */
  function showOfflineNotification(): void {
    toast.warning("You're Offline", {
      description: "Changes will be saved locally and synced when you're back online.",
      duration: 5000,
    });
  }



  /**
   * Force update service worker
   */
  export async function forceUpdateServiceWorker(): Promise<void> {
    if (!("serviceWorker" in navigator)) return;

    const registration = await navigator.serviceWorker.ready;
    await registration.update();

    // Wait for update
    registration.addEventListener("updatefound", () => {
      const newWorker = registration.installing;

      if (newWorker) {
        newWorker.addEventListener("statechange", () => {
          if (newWorker.state === "installed") {
            // Force activation
            newWorker.postMessage({ type: "SKIP_WAITING" });
            window.location.reload();
          }
        });
      }
    });
  }

  /**
   * Check for updates
   */
  export async function checkForUpdates(): Promise<boolean> {
    if (!("serviceWorker" in navigator)) return false;

    try {
      const registration = await navigator.serviceWorker.ready;
      await registration.update();

      // If waiting worker exists, update is available
      return !!registration.waiting;
    } catch (error) {
      console.error("[PWA] Update check failed:", error);
      return false;
    }
  }

/**
 * Get service worker registration status
 */
export async function getRegistrationStatus(): Promise<{
  registered: boolean;
  state?: ServiceWorkerState | undefined;
  scope?: string | undefined;
}> {
  if (!("serviceWorker" in navigator)) {
    return { registered: false };
  }

  const registration = await navigator.serviceWorker.ready;

  return {
    registered: true,
    state: registration.active?.state,
    scope: registration.scope,
  };
}

// Reference for sync registration
let swRegistration: ServiceWorkerRegistration | null = null;

/**
 * Sync offline queue
 */
async function syncOfflineQueue(): Promise<void> {
  try {
    // Trigger background sync if supported
    if ("serviceWorker" in navigator && swRegistration && "sync" in swRegistration) {
      // @ts-ignore - BackgroundSync API
      await swRegistration.sync.register("sync-offline-queue");
      console.log("[PWA] Background sync registered");
    }
  } catch (error) {
    console.error("[PWA] Background sync failed:", error);
  }
}

/**
 * Initialize PWA with default configuration
 */
export async function initializePWA(): Promise<RegistrationResult> {
  const result = await registerServiceWorker({
    onUpdateAvailable: () => {
      console.log("[PWA] Update available - ready to refresh");
    },
    onOffline: () => {
      console.log("[PWA] App is offline");
    },
    onOnline: () => {
      console.log("[PWA] App is back online");
    },
  });

  if (result.success && result.registration) {
    swRegistration = result.registration;
  }

  return result;
}
