"use client";

/**
 * Camera Scan Component
 * =====================
 * Microchip barcode scanner using BarcodeDetector API with file fallback.
 * Optimized for mobile kennel environments.
 *
 * @component
 * @example
 * ```tsx
 * <CameraScan
 *   onScan={(chip) => console.log("Scanned:", chip)}
 *   onError={(err) => console.error(err)}
 * />
 * ```
 */

import { useState, useRef, useCallback, useEffect } from "react";
import { Camera, Upload, X, AlertCircle } from "lucide-react";

interface CameraScanProps {
  /** Callback when chip is successfully scanned */
  onScan: (chipNumber: string) => void;
  /** Callback on error */
  onError?: (error: string) => void;
  /** Custom className */
  className?: string;
}

// Check if BarcodeDetector is supported
// BarcodeDetector type declaration
interface BarcodeDetector {
  detect(image: ImageBitmapSource): Promise<Array<{ rawValue: string }>>;
}

declare global {
  interface Window {
    BarcodeDetector?: new (options: { formats: string[] }) => BarcodeDetector;
  }
}

const isBarcodeDetectorSupported = (): boolean => {
  return typeof window !== "undefined" && "BarcodeDetector" in window;
};

export function CameraScan({ onScan, onError, className = "" }: CameraScanProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useFileFallback, setUseFileFallback] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const barcodeDetectorRef = useRef<BarcodeDetector | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  /**
   * Initialize BarcodeDetector
   */
  useEffect(() => {
    if (isBarcodeDetectorSupported()) {
      try {
        // @ts-ignore - BarcodeDetector types not in all browsers
        barcodeDetectorRef.current = new BarcodeDetector({
          formats: ["code_128", "code_39", "ean_13", "ean_8", "upc_a", "upc_e"],
        });
      } catch (err) {
        console.warn("BarcodeDetector initialization failed:", err);
      }
    }
  }, []);

  /**
   * Start camera stream
   */
  const startCamera = useCallback(async () => {
    try {
      setError(null);
      setIsScanning(true);

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment",
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      // Start barcode detection
      detectBarcodes();
    } catch (err) {
      console.error("Camera access error:", err);
      setError("Camera access denied. Please use file upload instead.");
      setUseFileFallback(true);
      onError?.("Camera access denied");
    }
  }, [onError]);

  /**
   * Stop camera stream
   */
  const stopCamera = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsScanning(false);
  }, []);

  /**
   * Detect barcodes from video stream
   */
  const detectBarcodes = useCallback(async () => {
    if (!videoRef.current || !barcodeDetectorRef.current) return;

    try {
      const barcodes = await barcodeDetectorRef.current.detect(videoRef.current);

      if (barcodes.length > 0) {
        const barcode = barcodes[0];
        const rawValue = barcode.rawValue;

        // Validate microchip format (9-15 digits)
        if (/^\d{9,15}$/.test(rawValue)) {
          stopCamera();
          setIsOpen(false);
          onScan(rawValue);
          return;
        }
      }
    } catch (err) {
      console.warn("Barcode detection error:", err);
    }

    // Continue detection
    animationFrameRef.current = requestAnimationFrame(detectBarcodes);
  }, [onScan, stopCamera]);

  /**
   * Handle file upload for fallback
   */
  const handleFileUpload = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      try {
        setError(null);

        // Create image from file
        const img = new Image();
        img.src = URL.createObjectURL(file);

        await new Promise((resolve, reject) => {
          img.onload = resolve;
          img.onerror = reject;
        });

        // Try to detect barcodes in image
        if (barcodeDetectorRef.current) {
          const barcodes = await barcodeDetectorRef.current.detect(img);

          if (barcodes.length > 0) {
            const rawValue = barcodes[0].rawValue;
            if (/^\d{9,15}$/.test(rawValue)) {
              setIsOpen(false);
              onScan(rawValue);
              return;
            }
          }
        }

        // If no barcode detected, show error
        setError("No valid microchip barcode detected in image");
        onError?.("No barcode detected");
      } catch (err) {
        console.error("File upload error:", err);
        setError("Failed to process image");
        onError?.("Image processing failed");
      }
    },
    [onScan, onError]
  );

  /**
   * Open scanner modal
   */
  const openScanner = useCallback(() => {
    setIsOpen(true);
    setError(null);
    setUseFileFallback(!isBarcodeDetectorSupported());

    if (isBarcodeDetectorSupported()) {
      startCamera();
    }
  }, [startCamera]);

  /**
   * Close scanner modal
   */
  const closeScanner = useCallback(() => {
    stopCamera();
    setIsOpen(false);
    setError(null);
    setUseFileFallback(false);
  }, [stopCamera]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  // Scanner modal
  if (isOpen) {
    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
        onClick={closeScanner}
      >
        <div
          className="bg-[#1A1A1A] rounded-lg max-w-md w-full overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-[#333333]">
            <h3 className="text-white font-semibold">Scan Microchip</h3>
            <button
              onClick={closeScanner}
              className="text-[#888888] hover:text-white transition-colors p-2"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 space-y-4">
            {error && (
              <div className="flex items-center gap-2 text-amber-400 bg-amber-900/20 p-3 rounded-lg">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            {!useFileFallback ? (
              // Camera view
              <div className="relative aspect-[4/3] bg-black rounded-lg overflow-hidden">
                <video
                  ref={videoRef}
                  className="w-full h-full object-cover"
                  playsInline
                  muted
                />

                {/* Scan overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-48 h-32 border-2 border-[#F37022] rounded-lg relative">
                    {/* Corner markers */}
                    <div className="absolute -top-1 -left-1 w-4 h-4 border-t-2 border-l-2 border-[#F37022]" />
                    <div className="absolute -top-1 -right-1 w-4 h-4 border-t-2 border-r-2 border-[#F37022]" />
                    <div className="absolute -bottom-1 -left-1 w-4 h-4 border-b-2 border-l-2 border-[#F37022]" />
                    <div className="absolute -bottom-1 -right-1 w-4 h-4 border-b-2 border-r-2 border-[#F37022]" />

                    {/* Scan line */}
                    <div className="absolute top-0 left-0 right-0 h-0.5 bg-[#F37022] animate-scan" />
                  </div>
                </div>

                {/* Scanning indicator */}
                {isScanning && (
                  <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
                    <div className="flex items-center gap-2 text-white text-sm bg-black/50 px-3 py-1.5 rounded-full">
                      <div className="w-2 h-2 bg-[#F37022] rounded-full animate-pulse" />
                      Scanning...
                    </div>
                  </div>
                )}
              </div>
            ) : (
              // File upload fallback
              <div className="space-y-4">
                <div className="border-2 border-dashed border-[#444444] rounded-lg p-8 text-center hover:border-[#666666] transition-colors">
                  <Upload className="w-12 h-12 mx-auto text-[#666666] mb-3" />
                  <p className="text-white font-medium mb-1">
                    Upload barcode image
                  </p>
                  <p className="text-[#888888] text-sm">
                    PNG, JPG up to 5MB
                  </p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="barcode-upload"
                  />
                  <label
                    htmlFor="barcode-upload"
                    className="inline-block mt-4 px-4 py-2 bg-[#333333] text-white rounded-lg cursor-pointer hover:bg-[#444444] transition-colors"
                  >
                    Select File
                  </label>
                </div>

                {!isBarcodeDetectorSupported() && (
                  <p className="text-[#888888] text-sm text-center">
                    Barcode scanning not supported in this browser.
                    <br />
                    Please upload a clear photo of the microchip barcode.
                  </p>
                )}
              </div>
            )}

            {/* Switch to file upload */}
            {!useFileFallback && (
              <button
                onClick={() => {
                  stopCamera();
                  setUseFileFallback(true);
                }}
                className="w-full py-3 text-[#888888] hover:text-white text-sm transition-colors"
              >
                Use file upload instead
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Trigger button
  return (
    <button
      onClick={openScanner}
      className={`
        flex items-center gap-2 px-4 py-3
        bg-[#2A2A2A] text-white rounded-lg
        hover:bg-[#333333] active:bg-[#444444]
        transition-all duration-200
        min-h-[48px] min-w-[48px]
        touch-manipulation
        ${className}
      `}
      type="button"
    >
      <Camera className="w-5 h-5" />
      <span className="font-medium">Scan Chip</span>
    </button>
  );
}
