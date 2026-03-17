import { useLocation, useNavigate } from 'react-router-dom';
import { MoreHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';

interface OrbHeaderLink {
  label: string;
  path: string;
}

const ORB_HEADER_LINKS: OrbHeaderLink[] = [
  { label: 'Approved', path: '/orb/approved-entries' },
  { label: 'Rejected', path: '/orb/rejected-entries' },
  { label: 'Deleted', path: '/orb/deleted-entries' },
  { label: 'PDFs', path: '/orb/pdf-archive' },
  { label: 'Guidelines', path: '/orb/orb-guidelines' },
];

function isOrbLinkActive(currentPath: string, linkPath: string): boolean {
  return currentPath === linkPath;
}

export function OrbHeaderActions() {
  const location = useLocation();
  const navigate = useNavigate();

  if (!location.pathname.startsWith('/orb')) {
    return null;
  }

  return (
    <>
      <div className="hidden items-center gap-1 md:flex" aria-label="ORB actions">
        {ORB_HEADER_LINKS.map((link) => (
          <button
            key={link.path}
            type="button"
            onClick={() => navigate(link.path)}
            className={cn(
              'rounded-full px-3 py-1.5 text-sm font-medium transition-colors',
              isOrbLinkActive(location.pathname, link.path)
                ? 'bg-primary-50 text-primary-700'
                : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
            )}
          >
            {link.label}
          </button>
        ))}
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="ORB actions"
            title="ORB actions"
          >
            <MoreHorizontal className="h-5 w-5 text-neutral-600" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56 md:hidden">
          {ORB_HEADER_LINKS.map((link) => (
            <DropdownMenuItem
              key={link.path}
              onClick={() => navigate(link.path)}
              className={cn(
                isOrbLinkActive(location.pathname, link.path) && 'bg-accent text-accent-foreground'
              )}
            >
              {link.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  );
}
