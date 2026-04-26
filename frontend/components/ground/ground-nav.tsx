"use client";

import { useRouter, usePathname } from "next/navigation";
import { Activity, Heart, Baby, Stethoscope, Scale, AlertTriangle, Clock } from "lucide-react";

import { Button } from "@/components/ui/button";

const NAV_ITEMS = [
  { id: "heat", label: "Heat", icon: Activity, href: "/ground/heat" },
  { id: "mate", label: "Mate", icon: Heart, href: "/ground/mate" },
  { id: "whelp", label: "Whelp", icon: Baby, href: "/ground/whelp" },
  { id: "health", label: "Health", icon: Stethoscope, href: "/ground/health" },
  { id: "weight", label: "Weight", icon: Scale, href: "/ground/weight" },
  { id: "nursing", label: "Nursing", icon: AlertTriangle, href: "/ground/nursing" },
  { id: "not-ready", label: "Wait", icon: Clock, href: "/ground/not-ready" },
];

export function GroundNav() {
  const router = useRouter();
  const pathname = usePathname();

  // Don't show nav on dashboard
  if (pathname === "/ground") return null;

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-[#1A1A1A] border-t border-[#333333] z-50">
      <div className="flex justify-around items-center h-16 px-2">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname.startsWith(item.href);

          return (
            <Button
              key={item.id}
              variant="ghost"
              onClick={() => router.push(item.href)}
              className={`flex flex-col items-center justify-center gap-1 h-14 w-14 min-w-0 ${
                isActive
                  ? "text-[#F37022]"
                  : "text-[#888888] hover:text-white"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{item.label}</span>
            </Button>
          );
        })}
      </div>
    </nav>
  );
}
