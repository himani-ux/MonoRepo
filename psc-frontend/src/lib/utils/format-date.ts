import { format, parseISO } from 'date-fns';

/**
 * Format a date string for display
 */
export function formatDisplayDate(isoDate: string | null | undefined): string {
  if (!isoDate) return '';
  try {
    return format(parseISO(isoDate), 'dd MMM yyyy');
  } catch {
    return isoDate;
  }
}

/**
 * Format a date string for API submission (ISO format)
 */
export function formatAPIDate(date: Date): string {
  return format(date, 'yyyy-MM-dd');
}
