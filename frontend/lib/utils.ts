/**
 * Wellfond BMS - Utility Functions
 * ==================================
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// =============================================================================
// Tailwind Class Merging
// =============================================================================

/**
 * Merge Tailwind CSS classes with proper precedence.
 * Uses clsx for conditional classes and tailwind-merge for deduplication.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// =============================================================================
// Date Formatting
// =============================================================================

/**
 * Format date to display string.
 * @param date - Date to format
 * @param format - Format pattern: 'short', 'long', 'relative', 'iso'
 */
export function formatDate(
  date: Date | string | null,
  format: 'short' | 'long' | 'relative' | 'iso' = 'short'
): string {
  if (!date) return '-';

  const d = typeof date === 'string' ? new Date(date) : date;

  switch (format) {
    case 'short':
      return d.toLocaleDateString('en-SG', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    case 'long':
      return d.toLocaleDateString('en-SG', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      });
    case 'relative':
      return getRelativeTimeString(d);
    case 'iso':
      return d.toISOString().split('T')[0];
    default:
      return d.toLocaleDateString();
  }
}

/**
 * Format datetime to display string.
 */
export function formatDateTime(
  date: Date | string | null,
  format: 'short' | 'long' = 'short'
): string {
  if (!date) return '-';

  const d = typeof date === 'string' ? new Date(date) : date;

  return d.toLocaleString('en-SG', {
    day: 'numeric',
    month: format === 'long' ? 'long' : 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Get relative time string (e.g., "2 days ago").
 */
function getRelativeTimeString(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const months = Math.floor(days / 30);
  const years = Math.floor(days / 365);

  if (years > 0) return `${years} year${years > 1 ? 's' : ''} ago`;
  if (months > 0) return `${months} month${months > 1 ? 's' : ''} ago`;
  if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
  if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  return 'just now';
}

// =============================================================================
// Age Calculation
// =============================================================================

/**
 * Calculate age from date of birth.
 * @returns Object with years and months
 */
export function calculateAge(dob: Date | string | null): { years: number; months: number } | null {
  if (!dob) return null;

  const birthDate = typeof dob === 'string' ? new Date(dob) : dob;
  const today = new Date();

  let years = today.getFullYear() - birthDate.getFullYear();
  let months = today.getMonth() - birthDate.getMonth();

  if (months < 0) {
    years--;
    months += 12;
  }

  // Adjust for day of month
  if (today.getDate() < birthDate.getDate()) {
    months--;
    if (months < 0) {
      years--;
      months += 12;
    }
  }

  return { years, months };
}

/**
 * Format age as display string.
 */
export function formatAge(dob: Date | string | null): string {
  const age = calculateAge(dob);
  if (!age) return '-';

  const { years, months } = age;
  if (years === 0) return `${months}mo`;
  if (months === 0) return `${years}yr`;
  return `${years}yr ${months}mo`;
}

// =============================================================================
// Microchip Formatting
// =============================================================================

/**
 * Format microchip number with last 4 digits bold.
 * @example "SGD12345678" → "SGD1234**5678**"
 */
export function formatChip(chip: string | null): string {
  if (!chip) return '-';
  if (chip.length <= 4) return chip;

  const prefix = chip.slice(0, -4);
  const last4 = chip.slice(-4);
  return `${prefix}**${last4}**`;
}

// =============================================================================
// GST & Currency
// =============================================================================

/**
 * Extract GST from price (inclusive).
 * Formula: GST = price * (GST_RATE / (1 + GST_RATE))
 * @param price - Price inclusive of GST
 * @param gstRate - GST rate as decimal (default 0.09)
 * @returns Object with basePrice, gst, and total
 */
export function gstExtract(
  price: number,
  gstRate: number = 0.09
): { basePrice: number; gst: number; total: number } {
  const total = price;
  const gst = price * (gstRate / (1 + gstRate));
  const basePrice = price - gst;

  return {
    basePrice: roundToTwo(basePrice),
    gst: roundToTwo(gst),
    total: roundToTwo(total),
  };
}

/**
 * Add GST to base price.
 * @param basePrice - Price before GST
 * @param gstRate - GST rate as decimal (default 0.09)
 * @returns Object with basePrice, gst, and total
 */
export function gstAdd(
  basePrice: number,
  gstRate: number = 0.09
): { basePrice: number; gst: number; total: number } {
  const gst = basePrice * gstRate;
  const total = basePrice + gst;

  return {
    basePrice: roundToTwo(basePrice),
    gst: roundToTwo(gst),
    total: roundToTwo(total),
  };
}

/**
 * Format currency as SGD string.
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-SG', {
    style: 'currency',
    currency: 'SGD',
  }).format(amount);
}

function roundToTwo(num: number): number {
  return Math.round(num * 100) / 100;
}

// =============================================================================
// String Utilities
// =============================================================================

/**
 * Truncate string to specified length with ellipsis.
 */
export function truncate(str: string, length: number): string {
  if (!str || str.length <= length) return str;
  return str.slice(0, length) + '...';
}

/**
 * Capitalize first letter of string.
 */
export function capitalize(str: string): string {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Convert snake_case to Title Case.
 */
export function toTitleCase(str: string): string {
  return str
    .split('_')
    .map(word => capitalize(word.toLowerCase()))
    .join(' ');
}

// =============================================================================
// Debounce
// =============================================================================

/**
 * Debounce function calls.
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

// =============================================================================
// UUID Generation
// =============================================================================

/**
 * Generate UUID v4 for idempotency keys.
 */
export function generateIdempotencyKey(): string {
  return crypto.randomUUID();
}

// =============================================================================
// COI Calculation (Preview)
// =============================================================================

import { COI_THRESHOLDS } from './constants';

/**
 * Get COI color based on percentage.
 */
export function getCoiColor(coi: number): string {
  if (coi < COI_THRESHOLDS.SAFE) return 'text-green-600';
  if (coi < COI_THRESHOLDS.CAUTION) return 'text-amber-600';
  return 'text-red-600';
}

/**
 * Get COI status label.
 */
export function getCoiStatus(coi: number): string {
  if (coi < COI_THRESHOLDS.SAFE) return 'Safe';
  if (coi < COI_THRESHOLDS.CAUTION) return 'Caution';
  return 'Danger';
}
