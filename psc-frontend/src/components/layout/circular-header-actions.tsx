import type { ComponentType, SVGProps } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Hourglass, MoreHorizontal, Pencil, Wallet } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/use-auth';

type HeaderIcon = ComponentType<SVGProps<SVGSVGElement>>;

function CreateCircularIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
      <path d="M12 11v6" />
      <path d="M9 14h6" />
    </svg>
  );
}

interface CircularHeaderLink {
  to: string;
  label: string;
  title: string;
  icon: HeaderIcon;
  visible: boolean;
}

function CircularActionLink({
  to,
  label,
  title,
  icon: Icon,
  isActive,
}: {
  to: string;
  label: string;
  title: string;
  icon: HeaderIcon;
  isActive: boolean;
}) {
  return (
    <Link
      to={to}
      aria-label={label}
      title={title}
      className={cn(
        'inline-flex h-9 w-9 items-center justify-center rounded-full border transition-colors',
        isActive
          ? 'border-primary-200 bg-primary-50 text-primary-700'
          : 'border-transparent text-neutral-600 hover:bg-neutral-100'
      )}
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
    </Link>
  );
}

export function CircularHeaderActions() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  if (!location.pathname.startsWith('/circular')) {
    return null;
  }

  const isOfficeUser = user?.user_type === 'office';
  const isShipUser = user?.user_type === 'vessel';
  const isAdmin = isOfficeUser && user?.role?.toLowerCase() === 'admin';

  if (!isOfficeUser && !isShipUser) {
    return null;
  }

  const links: CircularHeaderLink[] = [
    {
      to: '/circular/office',
      label: 'Open create circular panel',
      title: 'Create Circular',
      icon: CreateCircularIcon,
      visible: isOfficeUser,
    },
    {
      to: '/circular/admin/all-notifications',
      label: 'View all circular notifications',
      title: 'View All Notifications',
      icon: Wallet,
      visible: isAdmin,
    },
    {
      to: '/circular/user/notifications',
      label: 'View your circular notifications',
      title: 'View Your Notifications',
      icon: Hourglass,
      visible: isOfficeUser,
    },
    {
      to: '/circular/user/drafts',
      label: 'View your circular drafts',
      title: 'View Draft Notifications',
      icon: Pencil,
      visible: isOfficeUser,
    },
  ];

  const visibleLinks = links.filter((link) => link.visible);
  if (visibleLinks.length === 0) {
    return null;
  }

  return (
    <>
      <div className="hidden items-center gap-1 md:flex" aria-label="Circular actions">
        {visibleLinks.map((link) => (
          <CircularActionLink
            key={link.to}
            to={link.to}
            label={link.label}
            title={link.title}
            icon={link.icon}
            isActive={location.pathname === link.to}
          />
        ))}
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Circular actions"
            title="Circular actions"
          >
            <MoreHorizontal className="h-5 w-5 text-neutral-600" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56 md:hidden">
          {visibleLinks.map((link) => {
            const Icon = link.icon;
            return (
              <DropdownMenuItem
                key={link.to}
                onClick={() => navigate(link.to)}
                className={cn(location.pathname === link.to && 'bg-accent text-accent-foreground')}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {link.title}
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  );
}
