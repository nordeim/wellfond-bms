/**
 * Revenue Chart Component
 * =======================
 * Monthly revenue bar chart using Recharts.
 *
 * Phase 8: Dashboard & Finance Exports
 * Design: Tangerine Sky theme with orange bars
 */

'use client';

import { TrendingUp, DollarSign } from 'lucide-react';
import { useRevenueChart } from '@/hooks/use-dashboard';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { RevenueMonthlyData } from '@/lib/types';

interface RevenueChartProps {
  className?: string;
}

// Simple bar chart using CSS (no Recharts dependency)
function SimpleBarChart({ data }: { data: RevenueMonthlyData[] }) {
  const maxValue = Math.max(...data.map((d) => d.total_sales), 1);

  return (
    <div className="space-y-4">
      {/* Chart */}
      <div className="flex items-end gap-2 h-40">
        {data.map((month) => {
          const heightPercent = (month.total_sales / maxValue) * 100;
          return (
            <div
              key={month.month}
              className="flex-1 flex flex-col items-center gap-1"
            >
              <div className="w-full flex flex-col items-center gap-1">
                <span className="text-xs text-[#4A7A94]">
                  ${(month.total_sales / 1000).toFixed(1)}k
                </span>
                <div
                  className="w-full bg-[#F97316] rounded-t-sm transition-all duration-500"
                  style={{ height: `${Math.max(heightPercent, 5)}%` }}
                />
              </div>
              <span className="text-xs text-[#4A7A94] truncate max-w-full">
                {month.month_label.split(' ')[0]}
              </span>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-[#C0D8EE]">
        <div>
          <p className="text-sm text-[#4A7A94]">Total Revenue</p>
          <p className="text-xl font-bold text-[#0D2030]">
            ${data.reduce((sum, d) => sum + d.total_sales, 0).toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-sm text-[#4A7A94]">GST Collected</p>
          <p className="text-xl font-bold text-[#0891B2]">
            ${data.reduce((sum, d) => sum + d.gst_collected, 0).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}

export function RevenueChart({ className }: RevenueChartProps) {
  const { data: monthlyData, isLoading } = useRevenueChart({ months: 6 });

  if (isLoading) {
    return (
      <Card className={cn('border-[#C0D8EE]', className)}>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-40 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!monthlyData || monthlyData.length === 0) {
    return (
      <Card className={cn('border-[#C0D8EE]', className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base font-semibold text-[#0D2030]">
            <TrendingUp className="h-5 w-5 text-[#0891B2]" />
            Revenue (6 Months)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-8 text-center">
            <DollarSign className="mx-auto h-12 w-12 text-[#C0D8EE]" />
            <p className="mt-2 text-sm text-[#4A7A94]">No revenue data available</p>
            <p className="text-xs text-[#4A7A94]">
              Complete sales agreements to see revenue trends
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('border-[#C0D8EE]', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-[#0D2030]">
          <TrendingUp className="h-5 w-5 text-[#0891B2]" />
          Revenue (6 Months)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <SimpleBarChart data={monthlyData} />
      </CardContent>
    </Card>
  );
}
