import {
  useState,
  useCallback,
  useMemo,
  useEffect,
  useId,
  useRef,
  type FC,
} from 'react';
import { Check, ChevronsUpDown, Search, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button, Badge } from '@/components/ui';
import { usePSCDefCodes } from '@/hooks/use-masters';
import type { PSCDefCode } from '@/types';

/**
 * Deficiency code select component
 * CRITICAL: DefCode must be prominently displayed per CLAUDE.md Business Rules
 *
 * Features:
 * - Searchable by code or description
 * - Shows DefCode prominently
 * - Category grouping/filtering
 * - Uses usePSCDefCodes hook from Step 3.2
 */

export interface DefCodeSelectProps {
  /** Selected DefCode value */
  value?: string;
  /** Change handler */
  onChange?: (code: string, defCode: PSCDefCode | null) => void;
  /** Placeholder text */
  placeholder?: string;
  /** Filter by category */
  categoryCode?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Error state */
  error?: boolean;
  /** Additional class names */
  className?: string;
}

export const DefCodeSelect: FC<DefCodeSelectProps> = ({
  value,
  onChange,
  placeholder = 'Select deficiency code...',
  categoryCode,
  disabled,
  error,
  className,
}) => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const triggerRef = useRef<HTMLButtonElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const listboxId = useId();

  const closeDropdown = useCallback(() => {
    setOpen(false);
    setSearch('');
    triggerRef.current?.focus();
  }, []);

  // Fetch deficiency codes with search/filter
  const { data: defCodes = [], isLoading } = usePSCDefCodes({
    search: search || undefined,
    category: categoryCode,
  });

  // Find selected deficiency code
  const selectedDefCode = useMemo(() => {
    if (!value) return null;
    return defCodes.find((dc) => dc.def_code === value) || null;
  }, [value, defCodes]);

  const handleSelect = useCallback(
    (defCode: PSCDefCode) => {
      onChange?.(defCode.def_code, defCode);
      closeDropdown();
    },
    [closeDropdown, onChange]
  );

  const handleClear = useCallback(() => {
    onChange?.('', null);
    closeDropdown();
  }, [closeDropdown, onChange]);

  // Group by category for display
  const groupedDefCodes = useMemo(() => {
    const groups: Record<string, PSCDefCode[]> = {};
    defCodes.forEach((dc) => {
      const category = dc.category_name || 'Other';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(dc);
    });
    return groups;
  }, [defCodes]);

  useEffect(() => {
    if (!open) return;

    searchInputRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeDropdown();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [closeDropdown, open]);

  return (
    <div className={cn('relative', className)}>
      {/* Trigger Button */}
      <Button
        ref={triggerRef}
        type="button"
        variant="outline"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={open ? listboxId : undefined}
        disabled={disabled}
        onClick={() => (open ? closeDropdown() : setOpen(true))}
        className={cn(
          'w-full justify-between font-normal',
          !value && 'text-neutral-400',
          error && 'border-error-500 focus:border-error-500 focus:ring-error-100'
        )}
      >
        {selectedDefCode ? (
          <span className="flex items-center gap-2 truncate">
            <Badge variant="secondary" className="font-mono text-xs">
              {selectedDefCode.def_code}
            </Badge>
            <span className="truncate">{selectedDefCode.def_name}</span>
          </span>
        ) : (
          <span>{placeholder}</span>
        )}
        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </Button>

      {/* Dropdown */}
      {open && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={closeDropdown}
          />

          {/* Dropdown Content */}
          <div
            id={listboxId}
            role="listbox"
            aria-label="Deficiency code options"
            className="absolute z-50 mt-1 w-full rounded-md border border-neutral-200 bg-white shadow-lg"
          >
            {/* Search Input */}
            <div className="border-b border-neutral-200 p-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  aria-label="Search deficiency codes"
                  placeholder="Search by code or description..."
                  className="w-full rounded-md border border-neutral-300 bg-white py-1.5 pl-8 pr-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
            </div>

            {/* Options List */}
            <div className="max-h-64 overflow-y-auto p-1">
              {isLoading ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="h-5 w-5 animate-spin text-neutral-400" />
                </div>
              ) : defCodes.length === 0 ? (
                <div className="py-6 text-center text-sm text-neutral-500">
                  No deficiency codes found
                </div>
              ) : (
                Object.entries(groupedDefCodes).map(([category, codes]) => (
                  <div key={category}>
                    {/* Category Header */}
                    <div className="px-2 py-1.5 text-xs font-semibold text-neutral-500">
                      {category}
                    </div>

                    {/* Codes in Category */}
                    {codes.map((defCode) => (
                      <button
                        key={defCode.def_code}
                        type="button"
                        role="option"
                        aria-selected={value === defCode.def_code}
                        onClick={() => handleSelect(defCode)}
                        className={cn(
                          'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm transition-colors',
                          'hover:bg-neutral-100 focus:bg-neutral-100 focus:outline-none',
                          value === defCode.def_code && 'bg-primary-50'
                        )}
                      >
                        {/* Check indicator */}
                        <span className="flex h-4 w-4 items-center justify-center">
                          {value === defCode.def_code && (
                            <Check className="h-4 w-4 text-primary-500" />
                          )}
                        </span>

                        {/* DefCode - PROMINENTLY DISPLAYED */}
                        <Badge
                          variant="secondary"
                          className="font-mono text-xs font-semibold"
                        >
                          {defCode.def_code}
                        </Badge>

                        {/* Description */}
                        <span className="flex-1 truncate text-neutral-700">
                          {defCode.def_name}
                        </span>
                      </button>
                    ))}
                  </div>
                ))
              )}
            </div>

            {/* Clear Button */}
            {value && (
              <div className="border-t border-neutral-200 p-2">
                <button
                  type="button"
                  onClick={handleClear}
                  className="w-full rounded-md px-2 py-1.5 text-center text-sm text-neutral-600 hover:bg-neutral-100"
                >
                  Clear selection
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

/**
 * Display component for showing a deficiency code (read-only)
 * CRITICAL: Shows DefCode prominently per business rules
 */
export interface DefCodeDisplayProps {
  /** DefCode value */
  code: string;
  /** Description/name */
  name?: string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Additional class names */
  className?: string;
}

export const DefCodeDisplay: FC<DefCodeDisplayProps> = ({
  code,
  name,
  size = 'md',
  className,
}) => {
  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      <Badge
        variant="secondary"
        className={cn(
          'font-mono font-semibold',
          size === 'sm' && 'px-1.5 py-0 text-xs',
          size === 'md' && 'text-xs',
          size === 'lg' && 'px-2.5 py-0.5 text-sm'
        )}
      >
        {code}
      </Badge>
      {name && (
        <span className={cn('text-neutral-700', sizeClasses[size])}>
          {name}
        </span>
      )}
    </span>
  );
};
