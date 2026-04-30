/**
 * Wellfond BMS - Application Constants
 * =====================================
 */

// =============================================================================
// Roles & Entities
// =============================================================================

export const ROLES = {
  MANAGEMENT: 'management' as const,
  ADMIN: 'admin' as const,
  SALES: 'sales' as const,
  GROUND: 'ground' as const,
  VET: 'vet' as const,
};

export const ROLE_LABELS: Record<string, string> = {
  management: 'Management',
  admin: 'Admin',
  sales: 'Sales',
  ground: 'Ground Operations',
  vet: 'Veterinary',
};

export const ROLE_HIERARCHY: Record<string, number> = {
  ground: 1,
  vet: 1,
  sales: 2,
  admin: 3,
  management: 4,
};

export const ENTITIES = {
  HOLDINGS: 'HOLDINGS' as const,
  KATONG: 'KATONG' as const,
  THOMSON: 'THOMSON' as const,
};

export const ENTITY_LABELS: Record<string, string> = {
  HOLDINGS: 'Holdings',
  KATONG: 'Katong',
  THOMSON: 'Thomson',
};

// =============================================================================
// Navigation
// =============================================================================

export const NAV_ITEMS = [
  { label: 'Dashboard', href: '/dashboard', icon: 'LayoutDashboard', roles: ['management', 'admin', 'sales'] },
  { label: 'Dogs', href: '/dogs', icon: 'Dog', roles: ['management', 'admin', 'sales', 'ground', 'vet'] },
  { label: 'Ground Ops', href: '/ground', icon: 'ClipboardList', roles: ['management', 'admin', 'ground'] },
  { label: 'Breeding', href: '/breeding', icon: 'Heart', roles: ['management', 'admin'] },
  { label: 'Sales', href: '/sales', icon: 'ShoppingCart', roles: ['management', 'admin', 'sales'] },
  { label: 'Compliance', href: '/compliance', icon: 'ShieldCheck', roles: ['management', 'admin'] },
  { label: 'Customers', href: '/customers', icon: 'Users', roles: ['management', 'admin', 'sales'] },
  { label: 'Finance', href: '/finance', icon: 'DollarSign', roles: ['management', 'admin'] },
];

// =============================================================================
// COI & Saturation Thresholds
// =============================================================================

export const COI_THRESHOLDS = {
  SAFE: 6.25,    // Green - breedable
  CAUTION: 12.5, // Amber - consider alternatives
  DANGER: 25.0, // Red - avoid
};

export const SATURATION_THRESHOLDS = {
  SAFE: 15,    // Safe breeding count
  CAUTION: 30, // Review needed
  DANGER: 50,  // Approaching saturation
};

// =============================================================================
// Singapore GST
// =============================================================================

export const GST_RATE = 0.09; // 9% GST as of 2024

// =============================================================================
// Dog Statuses
// =============================================================================

export const DOG_STATUSES = {
  ACTIVE: 'ACTIVE' as const,
  RETIRED: 'RETIRED' as const,
  REHOMED: 'REHOMED' as const,
  DECEASED: 'DECEASED' as const,
};

export const DOG_STATUS_LABELS: Record<string, string> = {
  ACTIVE: 'Active',
  RETIRED: 'Retired',
  REHOMED: 'Rehomed',
  DECEASED: 'Deceased',
};

// =============================================================================
// DNA Statuses
// =============================================================================

export const DNA_STATUSES = {
  PENDING: 'PENDING' as const,
  SUBMITTED: 'SUBMITTED' as const,
  RESULTS_RECEIVED: 'RESULTS_RECEIVED' as const,
  EXCLUDED: 'EXCLUDED' as const,
};

export const DNA_STATUS_LABELS: Record<string, string> = {
  PENDING: 'Pending',
  SUBMITTED: 'Submitted',
  RESULTS_RECEIVED: 'Results Received',
  EXCLUDED: 'Excluded',
};

// =============================================================================
// Sale Stages
// =============================================================================

export const SALE_STAGES = {
  INQUIRY: 'INQUIRY' as const,
  RESERVED: 'RESERVED' as const,
  CONTRACT: 'CONTRACT' as const,
  AVS_SUBMITTED: 'AVS_SUBMITTED' as const,
  DELIVERED: 'DELIVERED' as const,
};

export const SALE_STAGE_LABELS: Record<string, string> = {
  INQUIRY: 'Inquiry',
  RESERVED: 'Reserved',
  CONTRACT: 'Contract',
  AVS_SUBMITTED: 'AVS Submitted',
  DELIVERED: 'Delivered',
};

// =============================================================================
// Design Tokens
// =============================================================================

export const DESIGN_TOKENS = {
  colors: {
    background: '#DDEEFF',
    sidebar: '#E8F4FF',
    card: '#FFFFFF',
    primary: '#F97316',
    secondary: '#0891B2',
    text: '#0D2030',
    muted: '#4A7A94',
    border: '#C0D8EE',
    success: '#4EAD72',
    warning: '#D4920A',
    error: '#D94040',
    roleBar: '#FFF0E6',
  },
  fonts: {
    primary: 'var(--font-figtree)',
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
  },
};

// =============================================================================
// API Configuration
// =============================================================================
// SECURITY FIX H2: API_CONFIG.baseUrl removed NEXT_PUBLIC_API_URL
// Server-side uses BACKEND_INTERNAL_URL, client-side uses /api/proxy

export const API_CONFIG = {
  baseUrl: '/api/proxy',  // Always use BFF proxy (security)
  timeout: 30000,
  retryAttempts: 1,
};

// =============================================================================
// Pagination
// =============================================================================

export const PAGINATION = {
  defaultPageSize: 25,
  pageSizeOptions: [10, 25, 50, 100],
};

// =============================================================================
// Session
// =============================================================================

export const SESSION_DURATION = 15 * 60 * 1000; // 15 minutes in ms
