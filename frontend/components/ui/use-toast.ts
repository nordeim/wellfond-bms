/**
 * Wellfond BMS - useToast Hook
 * ============================
 * Toast notifications wrapper using Sonner.
 */

import { toast as sonnerToast } from "sonner";

type ToastVariant = "default" | "destructive" | "success" | "info" | "warning" | "error";

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
    
    // Build options object only with defined values
    const opts: { description?: string; duration?: number } = {};
    if (desc !== undefined) opts.description = desc;
    if (duration !== undefined) opts.duration = duration;

    switch (variant) {
      case "destructive":
      case "error":
        return sonnerToast.error(message, opts);
      case "success":
        return sonnerToast.success(message, opts);
      case "warning":
        return sonnerToast.warning(message, opts);
      case "info":
      default:
        return sonnerToast(message, opts);
    }
  };

  return { toast };
}

export { useToast };
