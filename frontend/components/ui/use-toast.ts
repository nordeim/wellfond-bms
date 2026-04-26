/**
 * Wellfond BMS - useToast Hook
 * ============================
 * Toast notifications wrapper using Sonner.
 */

import { toast as sonnerToast } from "sonner";

type ToastVariant = "default" | "destructive" | "success" | "info" | "warning";

interface ToastOptions {
  title?: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
}

function useToast() {
  const toast = (options: ToastOptions) => {
    const { title, description, variant = "default", duration } = options;

    const message = title || description || "";
    const desc = title && description ? description : undefined;

    switch (variant) {
      case "destructive":
      case "error":
        return sonnerToast.error(message, {
          description: desc,
          duration,
        });
      case "success":
        return sonnerToast.success(message, {
          description: desc,
          duration,
        });
      case "warning":
        return sonnerToast.warning(message, {
          description: desc,
          duration,
        });
      case "info":
      default:
        return sonnerToast(message, {
          description: desc,
          duration,
        });
    }
  };

  return { toast };
}

export { useToast };
