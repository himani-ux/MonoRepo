/**
 * Login form component.
 *
 * Features:
 * - Username and password fields
 * - Form validation with Zod
 * - Loading state during submission
 * - Error message display
 *
 * Per APP_FLOW.md Section 2.1 and FRONTEND_GUIDELINES.md Section 3.2
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/hooks/use-auth';
import { getErrorMessage } from '@/lib/api/client';

// Validation schema
const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export interface LoginFormProps {
  /** Callback when login is successful */
  onSuccess?: () => void;
  /** Additional CSS classes */
  className?: string;
}

export function LoginForm({ onSuccess, className }: LoginFormProps) {
  const { login, isLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setError(null);

    try {
      await login(data);
      onSuccess?.();
    } catch (err) {
      const message = getErrorMessage(err);
      // Map specific error messages per APP_FLOW.md
      if (message.toLowerCase().includes('invalid') || message.toLowerCase().includes('credentials')) {
        setError('Invalid email or password');
      } else if (message.toLowerCase().includes('locked')) {
        setError('Account locked. Contact administrator.');
      } else if (message.toLowerCase().includes('network') || message.toLowerCase().includes('connect')) {
        setError('Unable to connect. Check your connection.');
      } else {
        setError(message);
      }
    }
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className={cn('space-y-6', className)}
      noValidate
    >
      {/* Error Alert */}
      {error && (
        <div className="flex items-start gap-3 rounded-lg bg-red-50 p-4 text-sm text-red-600">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Username Field */}
      <div className="space-y-2">
        <Label htmlFor="username">Username</Label>
        <Input
          id="username"
          type="text"
          placeholder="Enter your username"
          autoComplete="username"
          autoFocus
          disabled={isLoading}
          {...register('username')}
          className={cn(errors.username && 'border-red-500 focus-visible:ring-red-500')}
        />
        {errors.username && (
          <p className="text-sm text-red-500">{errors.username.message}</p>
        )}
      </div>

      {/* Password Field */}
      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Enter your password"
            autoComplete="current-password"
            disabled={isLoading}
            {...register('password')}
            className={cn(
              'pr-10',
              errors.password && 'border-red-500 focus-visible:ring-red-500'
            )}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            aria-pressed={showPassword}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded-sm text-neutral-400 hover:text-neutral-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" aria-hidden="true" />
            ) : (
              <Eye className="h-4 w-4" aria-hidden="true" />
            )}
          </button>
        </div>
        {errors.password && (
          <p className="text-sm text-red-500">{errors.password.message}</p>
        )}
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        className="w-full"
        size="lg"
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Signing in...
          </>
        ) : (
          'Login'
        )}
      </Button>

      {/* Forgot Password Link */}
      <div className="text-center">
        <button
          type="button"
          className="text-sm text-primary-500 hover:text-primary-600 hover:underline"
          onClick={() => {
            // TODO: Implement forgot password flow
            alert('Password reset functionality coming soon.');
          }}
        >
          Forgot Password?
        </button>
      </div>
    </form>
  );
}
