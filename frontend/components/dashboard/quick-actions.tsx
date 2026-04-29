/**
 * Quick Actions Component
 * ======================
 * Role-aware quick action buttons for dashboard.
 *
 * Phase 8: Dashboard & Finance Exports
 * Design: Tangerine Sky theme with contextual actions
 */

'use client';

import { Plus, FileText, Users, Activity, Dog, ClipboardList } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import type { Role } from '@/lib/types';

interface QuickActionsProps {
  role: Role;
  className?: string;
}

interface ActionButton {
  label: string;
  href: string;
  icon: React.ReactNode;
  variant: 'primary' | 'secondary' | 'outline' | 'ghost';
}

const ROLE_ACTIONS: Record<Role, ActionButton[]> = {
  management: [
    { label: 'Add Dog', href: '/dogs/new', icon: <Plus className="h-4 w-4" />, variant: 'primary' },
    { label: 'Create Agreement', href: '/sales/new', icon: <FileText className="h-4 w-4" />, variant: 'secondary' },
    { label: 'Run Report', href: '/compliance', icon: <Activity className="h-4 w-4" />, variant: 'outline' },
  ],
  admin: [
    { label: 'Add Dog', href: '/dogs/new', icon: <Plus className="h-4 w-4" />, variant: 'primary' },
    { label: 'Create Agreement', href: '/sales/new', icon: <FileText className="h-4 w-4" />, variant: 'secondary' },
    { label: 'Ground Log', href: '/ground', icon: <ClipboardList className="h-4 w-4" />, variant: 'outline' },
  ],
  sales: [
    { label: 'Create Agreement', href: '/sales/new', icon: <FileText className="h-4 w-4" />, variant: 'primary' },
    { label: 'View Pipeline', href: '/sales', icon: <Activity className="h-4 w-4" />, variant: 'secondary' },
    { label: 'Customers', href: '/customers', icon: <Users className="h-4 w-4" />, variant: 'outline' },
  ],
  ground: [
    { label: 'Log Event', href: '/ground', icon: <ClipboardList className="h-4 w-4" />, variant: 'primary' },
    { label: 'View Dogs', href: '/dogs', icon: <Dog className="h-4 w-4" />, variant: 'secondary' },
  ],
  vet: [
    { label: 'Health Check', href: '/ground/log/health-obs', icon: <Activity className="h-4 w-4" />, variant: 'primary' },
    { label: 'Vaccination Round', href: '/ground/log/vaccine', icon: <Plus className="h-4 w-4" />, variant: 'secondary' },
    { label: 'View Dogs', href: '/dogs', icon: <Dog className="h-4 w-4" />, variant: 'outline' },
  ],
};

export function QuickActions({ role, className }: QuickActionsProps) {
  const actions = ROLE_ACTIONS[role] || ROLE_ACTIONS.ground;

  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {actions.map((action) => (
        <Link key={action.href} href={action.href}>
          <Button
            variant={action.variant === 'primary' ? 'primary' : action.variant === 'secondary' ? 'secondary' : 'outline'}
            className={cn(
              'gap-2',
              action.variant === 'primary' && 'bg-[#F97316] hover:bg-[#EA580C] text-white',
              action.variant === 'secondary' && 'bg-[#0891B2] hover:bg-[#0E7490] text-white',
              action.variant === 'outline' && 'border-[#C0D8EE] text-[#4A7A94] hover:bg-[#E8F4FF]'
            )}
          >
            {action.icon}
            <span className="hidden sm:inline">{action.label}</span>
          </Button>
        </Link>
      ))}
    </div>
  );
}
