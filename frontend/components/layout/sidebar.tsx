/**
 * Wellfond BMS - Sidebar Component
 * =================================
 * Desktop sidebar with role-aware navigation.
 * Collapsible, entity selector, role badge.
 */

'use client';

import {
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Dog,
  DollarSign,
  Heart,
  LayoutDashboard,
  LogOut,
  PawPrint,
  ShieldCheck,
  ShoppingCart,
  Users,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { NAV_ITEMS, ROLE_LABELS } from '@/lib/constants';
import type { User } from '@/lib/types';

interface SidebarProps {
  user: User | null;
}

const iconMap: Record<string, React.ElementType> = {
  LayoutDashboard,
  Dog,
  Heart,
  ShoppingCart,
  ShieldCheck,
  Users,
  DollarSign,
  ClipboardList,
};

export function Sidebar({ user }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const currentRole = user?.role;

  // Filter nav items by role
  const visibleNavItems = NAV_ITEMS.filter((item) =>
    currentRole ? item.roles.includes(currentRole) : false
  );

  const toggleSidebar = () => setCollapsed(!collapsed);

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 flex h-screen flex-col bg-[#E8F4FF]',
        'transition-all duration-300 ease-in-out',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          'flex h-16 items-center border-b border-[#C0D8EE] px-4',
          collapsed ? 'justify-center' : 'justify-between'
        )}
      >
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#F97316]">
            <PawPrint className="h-5 w-5 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-sm font-bold text-[#0D2030]">Wellfond</span>
              <span className="text-xs text-[#4A7A94]">BMS</span>
            </div>
          )}
        </Link>

        {!collapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="h-8 w-8 text-[#4A7A94] hover:bg-[#C0D8EE]/50"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Collapsed toggle button */}
      {collapsed && (
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="absolute -right-3 top-20 h-6 w-6 rounded-full border border-[#C0D8EE] bg-[#E8F4FF] text-[#4A7A94] shadow-sm hover:bg-[#C0D8EE]"
        >
          <ChevronRight className="h-3 w-3" />
        </Button>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-2">
          {visibleNavItems.map((item) => {
            const Icon = iconMap[item.icon] || LayoutDashboard;
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-[#F97316] text-white'
                      : 'text-[#4A7A94] hover:bg-[#C0D8EE]/50 hover:text-[#0D2030]',
                    collapsed && 'justify-center px-2'
                  )}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className={cn('h-5 w-5', isActive && 'text-white')} />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Bottom section */}
      <div className="border-t border-[#C0D8EE] p-4">
        {/* Entity Selector - Simple native select for now */}
        {!collapsed && (
          <div className="mb-3">
            <label className="mb-1 block text-xs text-[#4A7A94]">Entity</label>
            <select
              className="w-full rounded-md border border-[#C0D8EE] bg-white px-2 py-1.5 text-sm text-[#0D2030]"
              defaultValue="HOLDINGS"
            >
              <option value="HOLDINGS">Holdings</option>
              <option value="KATONG">Katong</option>
              <option value="THOMSON">Thomson</option>
            </select>
          </div>
        )}

        {/* Role Badge */}
        {currentRole && !collapsed && (
          <div className="mb-3 flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {ROLE_LABELS[currentRole] || currentRole}
            </Badge>
          </div>
        )}

        {/* Logout */}
        <Button
          variant="ghost"
          className={cn(
            'w-full justify-start gap-2 text-[#4A7A94] hover:bg-[#C0D8EE]/50 hover:text-[#0D2030]',
            collapsed && 'justify-center px-2'
          )}
          onClick={() => {
            // Handle logout
            window.location.href = '/login';
          }}
        >
          <LogOut className="h-4 w-4" />
          {!collapsed && <span>Logout</span>}
        </Button>
      </div>
    </aside>
  );
}

export default Sidebar;
