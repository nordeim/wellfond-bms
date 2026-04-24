/**
 * Wellfond BMS - Topbar Component
 * =================================
 * Breadcrumb, user info, notifications, role badge.
 */

'use client';

import { Bell, ChevronRight, User } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

// cn utility not used in this component
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ROLE_LABELS } from '@/lib/constants';
import type { User as UserType } from '@/lib/types';

interface TopbarProps {
  user: UserType | null;
}

// Breadcrumb mapping
const breadcrumbMap: Record<string, string> = {
  dashboard: 'Dashboard',
  dogs: 'Dogs',
  breeding: 'Breeding',
  sales: 'Sales',
  compliance: 'Compliance',
  customers: 'Customers',
  finance: 'Finance',
  ground: 'Ground Operations',
  users: 'Users',
  settings: 'Settings',
};

function generateBreadcrumbs(pathname: string) {
  const parts = pathname.split('/').filter(Boolean);
  const breadcrumbs = [];
  let currentPath = '';

  for (const part of parts) {
    currentPath += `/${part}`;
    breadcrumbs.push({
      label: breadcrumbMap[part] || part.charAt(0).toUpperCase() + part.slice(1),
      href: currentPath,
    });
  }

  return breadcrumbs;
}

export function Topbar({ user }: TopbarProps) {
  const pathname = usePathname();
  const breadcrumbs = generateBreadcrumbs(pathname);
  const role = user?.role;

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[#C0D8EE] bg-white px-6 shadow-sm">
      {/* Left: Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm">
        <Link
          href="/dashboard"
          className="text-[#4A7A94] hover:text-[#0D2030]"
        >
          Home
        </Link>
        {breadcrumbs.length > 0 && (
          <>
            <ChevronRight className="h-4 w-4 text-[#C0D8EE]" />
            {breadcrumbs.map((crumb, index) => {
              const isLast = index === breadcrumbs.length - 1;
              return (
                <span key={crumb.href} className="flex items-center gap-2">
                  {isLast ? (
                    <span className="font-medium text-[#0D2030]">
                      {crumb.label}
                    </span>
                  ) : (
                    <Link
                      href={crumb.href}
                      className="text-[#4A7A94] hover:text-[#0D2030]"
                    >
                      {crumb.label}
                    </Link>
                  )}
                  {!isLast && (
                    <ChevronRight className="h-4 w-4 text-[#C0D8EE]" />
                  )}
                </span>
              );
            })}
          </>
        )}
      </nav>

      {/* Right: Actions & User */}
      <div className="flex items-center gap-4">
        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="relative text-[#4A7A94] hover:bg-[#E8F4FF] hover:text-[#0D2030]"
            >
              <Bell className="h-5 w-5" />
              {/* Notification badge */}
              <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#D94040] text-[10px] font-medium text-white">
                3
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <div className="flex items-center justify-between px-4 py-2">
              <span className="font-medium text-[#0D2030]">Notifications</span>
              <Button variant="ghost" size="sm" className="h-auto text-xs text-[#F97316]">
                Mark all read
              </Button>
            </div>
            <DropdownMenuSeparator />
            <div className="max-h-80 overflow-y-auto">
              <DropdownMenuItem className="flex flex-col items-start gap-1">
                <span className="text-sm text-[#0D2030]">New sale inquiry</span>
                <span className="text-xs text-[#4A7A94]">5 minutes ago</span>
              </DropdownMenuItem>
              <DropdownMenuItem className="flex flex-col items-start gap-1">
                <span className="text-sm text-[#0D2030]">AVS submission approved</span>
                <span className="text-xs text-[#4A7A94]">1 hour ago</span>
              </DropdownMenuItem>
              <DropdownMenuItem className="flex flex-col items-start gap-1">
                <span className="text-sm text-[#0D2030]">Vaccination due</span>
                <span className="text-xs text-[#4A7A94]">Yesterday</span>
              </DropdownMenuItem>
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User Menu */}
        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="flex items-center gap-2 text-left hover:bg-[#E8F4FF]"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#F97316] text-white">
                  {user.firstName?.[0]?.toUpperCase() || <User className="h-4 w-4" />}
                </div>
                <div className="hidden flex-col items-start md:flex">
                  <span className="text-sm font-medium text-[#0D2030]">
                    {user.firstName} {user.lastName}
                  </span>
                  <span className="text-xs text-[#4A7A94]">{user.email}</span>
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="px-4 py-2">
                <p className="text-sm font-medium text-[#0D2030]">
                  {user.firstName} {user.lastName}
                </p>
                <p className="text-xs text-[#4A7A94]">{user.email}</p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <Link href="/profile" className="flex w-full">
                  Profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Link href="/settings" className="flex w-full">
                  Settings
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-[#D94040]">
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {/* Role Badge */}
        {role && (
          <Badge
            variant="outline"
            className="hidden border-[#F97316] text-[#F97316] md:inline-flex"
          >
            {ROLE_LABELS[role] || role}
          </Badge>
        )}
      </div>
    </header>
  );
}

export default Topbar;
