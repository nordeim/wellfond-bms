"use client";

/**
 * COI Gauge Component
 * ===================
 * Phase 4: Breeding & Genetics Engine
 *
 * Circular gauge showing COI percentage with animated fill.
 * Color coding: Green (<6.25%), Yellow (6.25-12.5%), Red (>12.5%)
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface COIGaugeProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  showLabel?: boolean;
  className?: string;
}

// Color thresholds matching backend logic
const getColor = (pct: number): { stroke: string; bg: string; text: string } => {
  if (pct < 6.25) {
    return {
      stroke: "#4EAD72", // Green - SAFE
      bg: "bg-green-100",
      text: "text-green-700",
    };
  } else if (pct < 12.5) {
    return {
      stroke: "#D4920A", // Yellow/Orange - CAUTION
      bg: "bg-amber-100",
      text: "text-amber-700",
    };
  }
  return {
    stroke: "#D94040", // Red - HIGH_RISK
    bg: "bg-red-100",
    text: "text-red-700",
  };
};

const getVerdict = (pct: number): string => {
  if (pct < 6.25) return "SAFE";
  if (pct < 12.5) return "CAUTION";
  return "HIGH RISK";
};

export function COIGauge({
  percentage,
  size = 160,
  strokeWidth = 12,
  showLabel = true,
  className,
}: COIGaugeProps) {
  const [animatedPercentage, setAnimatedPercentage] = useState(0);
  const { stroke, bg, text } = getColor(percentage);
  const verdict = getVerdict(percentage);

  // Animate the gauge on mount
  useEffect(() => {
    const timeout = setTimeout(() => {
      setAnimatedPercentage(percentage);
    }, 100);
    return () => clearTimeout(timeout);
  }, [percentage]);

  // SVG calculations
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  // Background circle (gray track)
  const trackStyle = {
    stroke: "#E5E7EB",
    strokeWidth,
    fill: "none",
  };

  // Progress circle
  const progressStyle = {
    stroke,
    strokeWidth,
    fill: "none",
    strokeLinecap: "round" as const,
    strokeDasharray: circumference,
    strokeDashoffset: circumference * (1 - animatedPercentage / 100),
  };

  return (
    <div className={cn("flex flex-col items-center", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        {/* Background circle */}
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
          style={{ overflow: "visible" }}
        >
          {/* Track */}
          <circle cx={center} cy={center} r={radius} style={trackStyle} />

          {/* Progress arc */}
          <motion.circle
            cx={center}
            cy={center}
            r={radius}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: circumference * (1 - percentage / 100) }}
            transition={{ duration: 1, ease: "easeOut" }}
            style={progressStyle}
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className={cn("text-4xl font-bold tabular-nums", text)}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            {percentage.toFixed(1)}%
          </motion.span>
          <motion.span
            className={cn("text-xs font-medium mt-1 px-2 py-0.5 rounded-full", bg, text)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.3 }}
          >
            {verdict}
          </motion.span>
        </div>
      </div>

      {showLabel && (
        <div className="mt-2 text-center">
          <p className="text-sm text-[#0D2030]/70">Coefficient of Inbreeding</p>
        </div>
      )}
    </div>
  );
}

// Compact version for table/list displays
export function COIGaugeCompact({
  percentage,
  size = 48,
  className,
}: Omit<COIGaugeProps, "showLabel" | "strokeWidth">) {
  const { stroke, bg } = getColor(percentage);
  const radius = (size - 6) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#E5E7EB"
          strokeWidth={6}
        />
        {/* Progress */}
        <motion.circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={stroke}
          strokeWidth={6}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - percentage / 100) }}
          transition={{ duration: 0.8 }}
        />
      </svg>
      <span className={cn("absolute text-xs font-semibold", getColor(percentage).text)}>
        {percentage.toFixed(0)}%
      </span>
    </div>
  );
}

// Badge version for inline display
export function COIBadge({ percentage, className }: { percentage: number; className?: string }) {
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
