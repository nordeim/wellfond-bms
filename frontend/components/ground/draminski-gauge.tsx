"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface TrendPoint {
  day: number;
  value: number;
}

interface DraminskiGaugeProps {
  reading: number;
  zone: "EARLY" | "RISING" | "FAST" | "PEAK" | "MATE_NOW";
  trend: TrendPoint[];
}

const ZONE_CONFIG = {
  EARLY: {
    label: "Early",
    color: "text-blue-400",
    bgColor: "bg-blue-900/20",
    borderColor: "border-blue-500",
    message: "Not ready yet - check again in 2-3 days",
  },
  RISING: {
    label: "Rising",
    color: "text-amber-400",
    bgColor: "bg-amber-900/20",
    borderColor: "border-amber-500",
    message: "Fertility increasing - check daily",
  },
  FAST: {
    label: "Fast Rise",
    color: "text-orange-400",
    bgColor: "bg-orange-900/20",
    borderColor: "border-orange-500",
    message: "Approaching peak - check twice daily",
  },
  PEAK: {
    label: "Peak",
    color: "text-red-400",
    bgColor: "bg-red-900/20",
    borderColor: "border-red-500",
    message: "Peak fertility - mate within 24-48h",
  },
  MATE_NOW: {
    label: "Mate Now!",
    color: "text-green-400",
    bgColor: "bg-green-900/20",
    borderColor: "border-green-500",
    message: "Post-peak drop - mate immediately",
  },
};

export function DraminskiGauge({ reading, zone, trend }: DraminskiGaugeProps) {
  const config = ZONE_CONFIG[zone];

  // Calculate trend direction
  const trendDirection =
    trend.length >= 2
      ? trend[trend.length - 1].value > trend[trend.length - 2].value
        ? "up"
        : trend[trend.length - 1].value < trend[trend.length - 2].value
          ? "down"
          : "flat"
      : "flat";

  const TrendIcon =
    trendDirection === "up"
      ? TrendingUp
      : trendDirection === "down"
        ? TrendingDown
        : Minus;

  return (
    <div
      className={`rounded-lg border-2 p-4 ${config.bgColor} ${config.borderColor}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className={`text-lg font-bold ${config.color}`}>{config.label}</span>
        <div className="flex items-center gap-1">
          <TrendIcon className={`w-5 h-5 ${config.color}`} />
          <span className={`text-2xl font-bold ${config.color}`}>{reading}</span>
        </div>
      </div>

      {/* Message */}
      <p className="text-sm text-white/80 mb-4">{config.message}</p>

      {/* Trend visualization */}
      {trend.length > 0 && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-[#888888]">
            <span>7-day trend</span>
            <span>{trendDirection === "up" ? "Rising" : trendDirection === "down" ? "Falling" : "Stable"}</span>
          </div>

          {/* Bar chart */}
          <div className="flex items-end gap-1 h-16">
            {trend.map((point, i) => {
              const max = Math.max(...trend.map((t) => t.value));
              const min = Math.min(...trend.map((t) => t.value));
              const range = max - min || 1;
              const height = ((point.value - min) / range) * 100;
              const isCurrent = i === trend.length - 1;

              return (
                <div
                  key={i}
                  className="flex-1 flex flex-col items-center gap-1"
                >
                  <div
                    className={`w-full rounded-t transition-all ${
                      isCurrent ? config.bgColor.replace("/20", "") : "bg-[#444444]"
                    }`}
                    style={{ height: `${Math.max(height, 10)}%` }}
                  />
                  <span className="text-[10px] text-[#888888]">
                    {point.day === 0 ? "Now" : `${point.day}d`}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
