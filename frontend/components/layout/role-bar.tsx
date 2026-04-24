/**
 * Wellfond BMS - Role Bar Component
 * ===================================
 * Shows role + entity context. #FFF0E6 bg, orange left border.
 */

import { Building2, UserCircle } from 'lucide-react';

import { cn } from '@/lib/utils';
import { ROLE_LABELS, ENTITY_LABELS } from '@/lib/constants';
import type { User } from '@/lib/types';

interface RoleBarProps {
  user: User | null;
  className?: string;
}

export function RoleBar({ user, className }: RoleBarProps) {
  if (!user) {
    return null;
  }

  const roleLabel = ROLE_LABELS[user.role] || user.role;
  const entityName = user.entityId
    ? ENTITY_LABELS[user.entityId as keyof typeof ENTITY_LABELS] || 'Unknown Entity'
    : 'No Entity';

  return (
    <div
      className={cn(
        'flex items-center gap-4 border-l-4 border-[#F97316] bg-[#FFF0E6] px-4 py-2',
        className
      )}
    >
      {/* Role indicator */}
      <div className="flex items-center gap-2">
        <UserCircle className="h-4 w-4 text-[#F97316]" />
        <span className="text-sm font-medium text-[#0D2030]">
          Logged in as <span className="text-[#F97316]">{roleLabel}</span>
        </span>
      </div>

      {/* Separator */}
      <span className="text-[#C0D8EE]">·</span>

      {/* Entity indicator */}
      <div className="flex items-center gap-2">
        <Building2 className="h-4 w-4 text-[#4A7A94]" />
        <span className="text-sm text-[#4A7A94]">{entityName}</span>
      </div>
    </div>
  );
}

export default RoleBar;
