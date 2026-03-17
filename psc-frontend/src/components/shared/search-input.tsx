import { useState, useEffect, useRef, type FC, type InputHTMLAttributes } from 'react';
import { Search, X, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Search input with debounce per DESIGN_SYSTEM.md
 * - Search icon on left
 * - Clear button when has value
 * - 300ms debounce by default
 * - Loading indicator during search
 */

export interface SearchInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'value'> {
  /** Current search value */
  value?: string;
  /** Change handler (receives debounced value) */
  onChange?: (value: string) => void;
  /** Immediate change handler (no debounce) */
  onChangeImmediate?: (value: string) => void;
  /** Debounce delay in ms (default: 300) */
  debounceMs?: number;
  /** Show loading indicator */
  isLoading?: boolean;
  /** Additional class names for the container */
  containerClassName?: string;
}

export const SearchInput: FC<SearchInputProps> = ({
  value: externalValue,
  onChange,
  onChangeImmediate,
  debounceMs = 300,
  isLoading,
  placeholder = 'Search...',
  disabled,
  className,
  containerClassName,
  ...props
}) => {
  const [internalValue, setInternalValue] = useState(externalValue || '');
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Sync internal value with external value
  useEffect(() => {
    if (externalValue !== undefined && externalValue !== internalValue) {
      setInternalValue(externalValue);
    }
    // Only sync when external value changes, not internal
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [externalValue]);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInternalValue(newValue);
    onChangeImmediate?.(newValue);

    // Clear existing debounce
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Set new debounce
    debounceRef.current = setTimeout(() => {
      onChange?.(newValue);
    }, debounceMs);
  };

  const handleClear = () => {
    setInternalValue('');
    onChangeImmediate?.('');
    onChange?.('');

    // Clear any pending debounce
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
  };

  const showClear = internalValue.length > 0 && !disabled;

  return (
    <div className={cn('relative', containerClassName)}>
      <Search
        className={cn(
          'absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2',
          disabled ? 'text-neutral-300' : 'text-neutral-400'
        )}
      />
      <input
        type="text"
        value={internalValue}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          'flex h-10 w-full rounded-md border bg-white py-2 pl-9 pr-9 text-base text-neutral-800 transition-colors duration-200',
          'placeholder:text-neutral-400',
          'focus:outline-none focus:ring-2 focus:ring-offset-0',
          'disabled:cursor-not-allowed disabled:bg-neutral-100 disabled:text-neutral-400',
          'border-neutral-300 focus:border-primary-500 focus:ring-primary-100',
          className
        )}
        {...props}
      />
      <div className="absolute right-3 top-1/2 -translate-y-1/2">
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin text-neutral-400" />
        ) : showClear ? (
          <button
            type="button"
            onClick={handleClear}
            className="rounded p-0.5 text-neutral-400 hover:text-neutral-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Clear search</span>
          </button>
        ) : null}
      </div>
    </div>
  );
};
