/**
 * Page header component for consistent page titles.
 *
 * Features:
 * - Page title and optional subtitle
 * - Back navigation button
 * - Action buttons slot
 *
 * Per DESIGN_SYSTEM.md typography tokens
 */

import { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

export interface PageHeaderProps {
  /** Page title */
  title: string;
  /** Optional subtitle/description */
  subtitle?: string;
  /** Show back button */
  showBack?: boolean;
  /** Custom back navigation path (defaults to history.back()) */
  backTo?: string;
  /** Action buttons or other elements */
  actions?: ReactNode;
  /** Additional CSS classes */
  className?: string;
}

export function PageHeader({
  title,
  subtitle,
  showBack = false,
  backTo,
  actions,
  className,
}: PageHeaderProps) {
  const navigate = useNavigate();

  const handleBack = () => {
    if (backTo) {
      navigate(backTo);
    } else {
      navigate(-1);
    }
  };

  return (
    <div
      className={cn(
        'flex flex-col gap-4 pb-4 pt-2 md:flex-row md:items-center md:justify-between md:pb-6 md:pt-4',
        className
      )}
    >
      <div className="flex items-start gap-3">
        {showBack && (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleBack}
            className="mt-0.5 shrink-0"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
        )}
        <div>
          <h1 className="text-xl font-semibold text-neutral-800 md:text-2xl">
            {title}
          </h1>
          {subtitle && (
            <p className="mt-1 text-sm text-neutral-500">{subtitle}</p>
          )}
        </div>
      </div>

      {actions && (
        <div className="flex items-center gap-2 md:shrink-0">
          {actions}
        </div>
      )}
    </div>
  );
}
