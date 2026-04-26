"use client";

/**
 * Draminski Chart Component
 * =========================
 * 7-day trend visualization for Draminski DOD2 readings.
 * Displays readings as a bar chart with color-coded zones.
 *
 * @component
 * @example
 * ```tsx
 * <DraminskiChart
 *   data={[
 *     { date: "2024-01-01", reading: 300, zone: "RISING" },
 *     { date: "2024-01-02", reading: 400, zone: "FAST" },
 *   ]}
 *   baseline={350}
 * />
 * ```
 */

interface TrendData {
  date: string;
  reading: number;
  zone: "EARLY" | "RISING" | "FAST" | "PEAK" | "MATE_NOW";
}

interface DraminskiChartProps {
  /** 7-day trend data */
  data: TrendData[];
  /** Baseline reading for reference */
  baseline?: number;
  /** Current reading to highlight */
  currentReading?: number;
  /** Custom className */
  className?: string;
}

// Zone colors matching draminski-gauge.tsx
const ZONE_COLORS = {
  EARLY: {
    bar: "bg-blue-500",
    text: "text-blue-400",
    bg: "bg-blue-900/30",
  },
  RISING: {
    bar: "bg-amber-500",
    text: "text-amber-400",
    bg: "bg-amber-900/30",
  },
  FAST: {
    bar: "bg-orange-500",
    text: "text-orange-400",
    bg: "bg-orange-900/30",
  },
  PEAK: {
    bar: "bg-red-500",
    text: "text-red-400",
    bg: "bg-red-900/30",
  },
  MATE_NOW: {
    bar: "bg-green-500",
    text: "text-green-400",
    bg: "bg-green-900/30",
  },
};

export function DraminskiChart({
  data,
  baseline,
  currentReading,
  className = "",
}: DraminskiChartProps) {
  // Calculate min/max for scaling
  const readings = data.map((d) => d.reading);
  const minReading = Math.min(...readings, baseline || Infinity, currentReading || Infinity);
  const maxReading = Math.max(...readings, baseline || 0, currentReading || 0);
  const range = maxReading - minReading || 1;

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-SG", { weekday: "short" });
  };

  // Calculate bar height percentage
  const getBarHeight = (reading: number) => {
    const normalized = ((reading - minReading) / range) * 100;
    return Math.max(normalized, 10); // Minimum 10% height
  };

  return (
    <div className={`bg-[#1A1A1A] rounded-lg p-4 border border-[#333333] ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-semibold">7-Day Trend</h3>
        {baseline && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-[#888888]">Baseline:</span>
            <span className="text-[#AAAAAA] font-medium">{baseline}</span>
          </div>
        )}
      </div>

      {/* Chart */}
      {data.length === 0 ? (
        <div className="h-32 flex items-center justify-center text-[#666666]">
          No trend data available
        </div>
      ) : (
        <div className="space-y-4">
          {/* Y-axis labels */}
          <div className="flex gap-2">
            {/* Y-axis */}
            <div className="flex flex-col justify-between text-xs text-[#666666] pr-2 border-r border-[#333333]">
              <span>{maxReading}</span>
              <span>{Math.round((maxReading + minReading) / 2)}</span>
              <span>{minReading}</span>
            </div>

            {/* Bars */}
            <div className="flex-1 flex items-end gap-1 h-32">
              {data.map((point, index) => {
                const isCurrent = currentReading && point.reading === currentReading;
                const colors = ZONE_COLORS[point.zone];

                return (
                  <div
                    key={index}
                    className="flex-1 flex flex-col items-center gap-1 group"
                  >
                    {/* Tooltip */}
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute -mt-16 bg-[#2A2A2A] text-white text-xs px-2 py-1 rounded pointer-events-none z-10">
                      {point.reading} ({point.zone})
                    </div>

                    {/* Bar */}
                    <div
                      className={`
                        w-full rounded-t transition-all duration-300
                        ${colors.bar}
                        ${isCurrent ? "ring-2 ring-white ring-offset-2 ring-offset-[#1A1A1A]" : ""}
                      `}
                      style={{ height: `${getBarHeight(point.reading)}%` }}
                    />

                    {/* Date label */}
                    <span className="text-[10px] text-[#888888]">
                      {formatDate(point.date)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Legend */}
          <div className="flex flex-wrap gap-2 pt-2 border-t border-[#333333]">
            {(Object.keys(ZONE_COLORS) as Array<keyof typeof ZONE_COLORS>).map(
              (zone) => (
                <div key={zone} className="flex items-center gap-1">
                  <div className={`w-3 h-3 rounded ${ZONE_COLORS[zone].bar}`} />
                  <span className={`text-xs ${ZONE_COLORS[zone].text}`}>
                    {zone.replace("_", " ")}
                  </span>
                </div>
              )
            )}
          </div>

          {/* Baseline reference line */}
          {baseline && (
            <div className="relative h-px bg-[#444444] mt-2">
              <div className="absolute -top-2 left-0 right-0 flex items-center justify-center">
                <span className="text-xs text-[#666666] bg-[#1A1A1A] px-2">
                  Baseline
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
