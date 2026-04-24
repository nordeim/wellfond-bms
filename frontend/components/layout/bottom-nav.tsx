/**
 * Wellfond BMS - Bottom Navigation Component
 * ==========================================
 * Mobile bottom nav: 5 tabs, 44px tap targets, visible <768px only.
 */

'use client';

import {
  ClipboardList,
  Dog,
  LayoutDashboard,
  MoreHorizontal,
  ShoppingCart,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';
import type { User } from '@/lib/types';

interface BottomNavProps {
  user: User | null;
}

// Mobile navigation items (simplified)
const MOBILE_NAV_ITEMS = [
  { label: 'Home', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Dogs', href: '/dogs', icon: Dog },
  { label: 'Sales', href: '/sales', icon: ShoppingCart },
  { label: 'Reports', href: '/reports', icon: ClipboardList },
  { label: 'More', href: '/more', icon: MoreHorizontal },
];

export function BottomNav({ user }: BottomNavProps) {
  const pathname = usePathname();
  const role = user?.role;

  // Filter items by role
  const visibleItems = MOBILE_NAV_ITEMS.filter((item) => {
    if (!role) return false;
    // Basic role filtering
    if (item.href === '/sales' && !['management', 'admin', 'sales'].includes(role)) {
      return false;
    }
    return true;
  });

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-[#C0D8EE] bg-white md:hidden">
      <div className="flex h-16 items-center justify-around">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-col items-center justify-center gap-1',
                'min-w-[64px] py-2',
                'transition-colors duration-150',
                isActive ? 'text-[#F97316]' : 'text-[#4A7A94]'
              )}
            >
              <Icon className="h-6 w-6" strokeWidth={isActive ? 2.5 : 2} />
              <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* Safe area padding for iOS */}
      <div className="h-[env(safe-area-inset-bottom)]" />
    </nav>
  );
}

export default BottomNav;
