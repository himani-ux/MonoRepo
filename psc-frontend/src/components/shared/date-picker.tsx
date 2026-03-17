import { forwardRef, type InputHTMLAttributes } from 'react';
import { Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

/**
 * Date picker component per DESIGN_SYSTEM.md
 * Uses native date input with custom styling for best mobile support
 */

export interface DatePickerProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'value' | 'onChange'> {
  /** Selected date value (ISO string format YYYY-MM-DD) */
  value?: string;
  /** Change handler receiving ISO string */
  onChange?: (value: string) => void;
  /** Show error styling */
  error?: boolean;
  /** Minimum selectable date (ISO string) */
  minDate?: string;
  /** Maximum selectable date (ISO string) */
  maxDate?: string;
  /** Prevent future dates */
  disableFuture?: boolean;
  /** Prevent past dates */
  disablePast?: boolean;
}

export const DatePicker = forwardRef<HTMLInputElement, DatePickerProps>(
  (
    {
      className,
      value,
      onChange,
      error,
      minDate,
      maxDate,
      disableFuture,
      disablePast,
      disabled,
      // Native date input doesn't support placeholder, but keeping for API compatibility
      placeholder: _placeholder = 'Select date',
      ...props
    },
    ref
  ) => {
    // Calculate min/max based on props
    const today = format(new Date(), 'yyyy-MM-dd');
    const computedMin = disablePast ? today : minDate;
    const computedMax = disableFuture ? today : maxDate;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange?.(e.target.value);
    };

    return (
      <div className="relative">
        <input
          ref={ref}
          type="date"
          value={value || ''}
          onChange={handleChange}
          min={computedMin}
          max={computedMax}
          disabled={disabled}
          className={cn(
            'flex h-10 w-full rounded-md border bg-white px-3 py-2 pr-10 text-base text-neutral-800 transition-colors duration-200',
            'placeholder:text-neutral-400',
            'focus:outline-none focus:ring-2 focus:ring-offset-0',
            'disabled:cursor-not-allowed disabled:bg-neutral-100 disabled:text-neutral-400',
            '[&::-webkit-calendar-picker-indicator]:absolute [&::-webkit-calendar-picker-indicator]:right-3 [&::-webkit-calendar-picker-indicator]:cursor-pointer [&::-webkit-calendar-picker-indicator]:opacity-0',
            error
              ? 'border-error-500 focus:border-error-500 focus:ring-error-100'
              : 'border-neutral-300 focus:border-primary-500 focus:ring-primary-100',
            className
          )}
          {...props}
        />
        <Calendar
          className={cn(
            'pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2',
            disabled ? 'text-neutral-400' : 'text-neutral-500'
          )}
        />
      </div>
    );
  }
);

DatePicker.displayName = 'DatePicker';
