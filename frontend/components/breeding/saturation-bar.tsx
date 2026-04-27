"use client";

/**
 * Saturation Bar Component
 * ========================
 * Phase 4: Breeding & Genetics Engine
 *
 * Horizontal bar showing farm saturation percentage.
 * Color coding: Green (<15%), Yellow (15-30%), Red (>30%)
 */

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface SaturationBarProps {
  percentage: number;
  entityName?: string;
  showLabel?: boolean;
  showStats?: boolean;
  dogsWithAncestry?: number;
  totalActiveDogs?: number;
  className?: string;
}

// Color thresholds matching backend logic
const getColor = (pct: number): { bar: string; bg: string; text: string } => {
  if (pct < 15) {
    return {
      bar: "bg-[#4EAD72]", // Green - SAFE
      bg: "bg-green-100",
      text: "text-green-700",
    };
  } else if (pct < 30) {
    return {
      bar: "bg-[#D4920A]", // Yellow/Orange - CAUTION
      bg: "bg-amber-100",
      text: "text-amber-700",
    };
  }
  return {
    bar: "bg-[#D94040]", // Red - HIGH_RISK
    bg: "bg-red-100",
    text: "text-red-700",
  };
};

const getVerdict = (pct: number): string => {
  if (pct < 15) return "SAFE";
  if (pct < 30) return "CAUTION";
  return "HIGH RISK";
};

export function SaturationBar({
  percentage,
  entityName,
  showLabel = true,
  showStats = true,
  dogsWithAncestry,
  totalActiveDogs,
  className,
}: SaturationBarProps) {
  const { bar, bg, text } = getColor(percentage);
  const verdict = getVerdict(percentage);

  return (
    <div className={cn("w-full", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {entityName && (
            <span className="text-sm font-medium text-[#0D2030]">
              {entityName}
            </span>
          )}
        </div>
        <span
          className={cn(
            "text-xs font-semibold px-2 py-0.5 rounded-full",
            bg,
            text
          )}
        >
          {verdict}
        </span>
      </div>

      {/* Progress bar */}
      <div className="relative">
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <motion.div
            className={cn("h-full rounded-full", bar)}
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(percentage, 100)}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>

        {/* Percentage label inside bar (if > 10%) */}
        {percentage > 10 && (
          <motion.span
            className="absolute inset-y-0 left-0 flex items-center pl-2 text-xs font-medium text-white"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            {percentage.toFixed(1)}%
          </motion.span>
        )}
      </div>

      {/* Stats */}
      {showStats && (
        <div className="flex items-center justify-between mt-2 text-xs text-[#0D2030]/60">
          <span>0%</span>
          <div className="flex items-center gap-1">
            {dogsWithAncestry !== undefined && totalActiveDogs !== undefined && (
              <span className="text-[#0D2030]/80">
                {dogsWithAncestry} of {totalActiveDogs} dogs
              </span>
            )}
          </div>
          <span>{percentage.toFixed(1)}%</span>
        </div>
      )}

      {showLabel && (
        <p className="mt-2 text-xs text-[#0D2030]/50">
          Farm Saturation - % of active dogs sharing ancestry
        </p>
      )}
    </div>
  );
}

// Compact version for table/list displays
export function SaturationBarCompact({
  percentage,
  className,
}: Omit<SaturationBarProps, "entityName" | "showLabel" | "showStats" | "dogsWithAncestry" | "totalActiveDogs">) {
  const { bar, text } = getColor(percentage);

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex-1 min-w-[60px]">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <motion.div
            className={cn("h-full rounded-full", bar)}
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(percentage, 100)}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </div>
      <span className={cn("text-xs font-medium whitespace-nowrap", text)}>
        {percentage.toFixed(1)}%
      </span>
    </div>
  );
}

// Badge version for inline display
export function SaturationBadge({
  percentage,
  className,
}: {
  percentage: number;
  className?: string;
}) {
  const { bg, text } = getColor(percentage);
  const verdict = getVerdict(percentage);

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
        bg,
        text,
        className
      )}
    >
      {percentage.toFixed(1)}% - {verdict}
    </span>
  );
}
