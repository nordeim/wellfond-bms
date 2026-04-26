/**
 * Ground Operations Dashboard
 * ===========================
 * Mobile-first dashboard for ground staff with quick actions.
 */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Activity, Heart, Baby, Stethoscope, Scale, AlertTriangle, Clock } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertLog } from "@/components/ground/alert-log";
import { useSSE } from "@/hooks/use-sse";
import { useToast } from "@/components/ui/use-toast";

const QUICK_ACTIONS = [
  {
    id: "heat",
    label: "In Heat",
    icon: Activity,
    href: "/ground/heat",
    color: "text-pink-400",
    bgColor: "bg-pink-900/20",
  },
  {
    id: "mate",
    label: "Mating",
    icon: Heart,
    href: "/ground/mate",
    color: "text-red-400",
    bgColor: "bg-red-900/20",
  },
  {
    id: "whelp",
    label: "Whelping",
    icon: Baby,
    href: "/ground/whelp",
    color: "text-green-400",
    bgColor: "bg-green-900/20",
  },
  {
    id: "health",
    label: "Health",
    icon: Stethoscope,
    href: "/ground/health",
    color: "text-amber-400",
    bgColor: "bg-amber-900/20",
  },
  {
    id: "weight",
    label: "Weight",
    icon: Scale,
    href: "/ground/weight",
    color: "text-blue-400",
    bgColor: "bg-blue-900/20",
  },
  {
    id: "nursing",
    label: "Nursing",
    icon: AlertTriangle,
    href: "/ground/nursing",
    color: "text-orange-400",
    bgColor: "bg-orange-900/20",
  },
  {
    id: "not-ready",
    label: "Not Ready",
    icon: Clock,
    href: "/ground/not-ready",
    color: "text-[#888888]",
    bgColor: "bg-[#333333]",
  },
];

export default function GroundDashboardPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { alerts, isConnected } = useSSE();
  const [pendingSync, setPendingSync] = useState(0);

  // Check pending offline queue
  useEffect(() => {
    const checkQueue = () => {
      const queue = JSON.parse(localStorage.getItem("offline_queue") || "[]");
      setPendingSync(queue.length);
    };
    checkQueue();
    const interval = setInterval(checkQueue, 5000);
    return () => clearInterval(interval);
  }, []);

  // Show alerts from SSE
  useEffect(() => {
    if (alerts.length > 0) {
      const latest = alerts[alerts.length - 1];
      if (latest.severity === "serious") {
        toast({
          title: "🚨 Alert",
          description: latest.message,
          variant: "destructive",
        });
      }
    }
  }, [alerts, toast]);

  return (
    <div className="px-4 py-4">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Ground Ops</h1>
        <div className="flex items-center gap-2 mt-1">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? "bg-green-500" : "bg-amber-500"
            }`}
          />
          <p className="text-sm text-[#888888]">
            {isConnected ? "Live alerts" : "Offline mode"}
          </p>
          {pendingSync > 0 && (
            <Badge
              variant="secondary"
              className="bg-amber-600/30 text-amber-200 border-amber-500/50"
            >
              {pendingSync} pending
            </Badge>
          )}
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        {QUICK_ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <Button
              key={action.id}
              variant="outline"
              onClick={() => router.push(action.href)}
              className={`h-24 flex flex-col items-center justify-center gap-2 ${action.bgColor} border-[#444444] hover:border-[#F37022] hover:bg-[#333333]`}
            >
              <Icon className={`w-6 h-6 ${action.color}`} />
              <span className="text-white font-medium">{action.label}</span>
            </Button>
          );
        })}
      </div>

      {/* Recent Alerts */}
      <Card className="bg-[#2A2A2A] border-[#333333] p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Recent Alerts</h2>
          {alerts.length > 0 && (
            <Badge className="bg-[#F37022] text-white">{alerts.length}</Badge>
          )}
        </div>

        <AlertLog alerts={alerts.slice(0, 5)} />
      </Card>
    </div>
  );
}
