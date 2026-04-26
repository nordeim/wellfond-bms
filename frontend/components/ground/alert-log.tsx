"use client";

import { AlertTriangle, Info } from "lucide-react";

import { Badge } from "@/components/ui/badge";

interface Alert {
  id: number;
  type: string;
  dog_id: string;
  dog_name: string;
  message: string;
  severity: "info" | "warning" | "serious";
  created_at: string;
}

interface AlertLogProps {
  alerts: Alert[];
}

export function AlertLog({ alerts }: AlertLogProps) {
  if (alerts.length === 0) {
    return (
      <div className="text-center py-8 text-[#888888]">
        <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>No recent alerts</p>
      </div>
    );
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "serious":
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      default:
        return <Info className="w-4 h-4 text-blue-400" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "serious":
        return (
          <Badge className="bg-red-900/50 text-red-200 border-red-500/50">
            Serious
          </Badge>
        );
      case "warning":
        return (
          <Badge className="bg-amber-900/50 text-amber-200 border-amber-500/50">
            Warning
          </Badge>
        );
      default:
        return (
          <Badge className="bg-blue-900/50 text-blue-200 border-blue-500/50">
            Info
          </Badge>
        );
    }
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className="flex items-start gap-3 p-3 rounded-lg bg-[#1A1A1A] border border-[#333333]"
        >
          {getSeverityIcon(alert.severity)}

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="font-medium text-white truncate">
                {alert.dog_name}
              </span>
              {getSeverityBadge(alert.severity)}
            </div>
            <p className="text-sm text-[#888888] truncate">{alert.message}</p>
            <p className="text-xs text-[#666666] mt-1">{formatTime(alert.created_at)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
