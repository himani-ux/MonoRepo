import { FormEvent, useEffect, useState } from 'react';
import { Lock, Loader2, LogOut } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import type { ReauthIdentifier } from '@/stores/auth-store';

export interface SessionReauthModalProps {
  open: boolean;
  identifier: ReauthIdentifier;
  isSubmitting: boolean;
  error: string | null;
  onSubmit: (password: string) => Promise<void> | void;
  onLogout: () => Promise<void> | void;
}

export function SessionReauthModal({
  open,
  identifier,
  isSubmitting,
  error,
  onSubmit,
  onLogout,
}: SessionReauthModalProps) {
  const [password, setPassword] = useState('');

  useEffect(() => {
    if (!open) {
      setPassword('');
    }
  }, [open]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSubmit(password);
  };

  return (
    <Dialog open={open}>
      <DialogContent
        className="[&>button]:hidden"
        onEscapeKeyDown={(event) => event.preventDefault()}
        onInteractOutside={(event) => event.preventDefault()}
      >
        <DialogHeader>
          <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-md bg-primary-50 text-primary-600">
            <Lock className="h-5 w-5" aria-hidden="true" />
          </div>
          <DialogTitle>Session expired</DialogTitle>
          <DialogDescription>
            Your work stays open after re-authentication.
          </DialogDescription>
        </DialogHeader>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="reauth-identifier">{identifier.label}</Label>
            <Input
              id="reauth-identifier"
              value={identifier.value}
              readOnly
              autoComplete="username"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="reauth-password">Password</Label>
            <Input
              id="reauth-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              autoFocus
              disabled={isSubmitting}
            />
          </div>

          {error && (
            <div className="rounded-md border border-error-200 bg-error-50 px-3 py-2 text-sm text-error-700">
              {error}
            </div>
          )}

          <div className="flex flex-col gap-2 sm:flex-row sm:justify-between">
            <Button
              type="button"
              variant="outline"
              onClick={onLogout}
              disabled={isSubmitting}
            >
              <LogOut className="mr-2 h-4 w-4" aria-hidden="true" />
              Sign out
            </Button>
            <Button type="submit" disabled={isSubmitting || !password.trim()}>
              {isSubmitting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
              ) : null}
              Resume session
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

