"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft, User } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface GroundHeaderProps {
  user: {
    username: string;
    role: string;
    entity?: {
      name: string;
    };
  };
}

export function GroundHeader({ user }: GroundHeaderProps) {
  const router = useRouter();

  return (
    <header className="sticky top-0 z-40 bg-[#1A1A1A] border-b border-[#333333]">
      <div className="flex items-center justify-between px-4 h-14">
        {/* Back button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push("/ground")}
          className="text-white hover:bg-[#333333]"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>

        {/* Title */}
        <div className="flex flex-col items-center">
          <span className="text-sm font-semibold text-white">Ground Ops</span>
          {user.entity && (
            <span className="text-xs text-[#888888]">{user.entity.name}</span>
          )}
        </div>

        {/* User badge */}
        <div className="flex items-center gap-2">
          <Badge
            variant="secondary"
            className="bg-[#F37022]/20 text-[#F37022] border-[#F37022]/50"
          >
            {user.role}
          </Badge>
          <Button
            variant="ghost"
            size="icon"
            className="text-white hover:bg-[#333333]"
          >
            <User className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </header>
  );
}
