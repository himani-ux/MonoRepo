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
import { Loader2, AlertCircle, Eye, EyeOff, Lock, User } from 'lucide-react';
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
        <div className="flex items-start gap-3 rounded-xl border border-red-100 bg-red-50/80 p-4 text-sm font-medium text-red-600 shadow-sm">
          <AlertCircle className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {/* Username Field */}
      <div className="space-y-2.5">
        <Label htmlFor="username" className="text-sm font-semibold text-[#0F172A]">Username</Label>
        <div className="relative">
          <User className="pointer-events-none absolute left-4 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-[#94A3B8]" aria-hidden="true" />
          <Input
            id="username"
            type="text"
            placeholder="Enter your username"
            autoComplete="username"
            autoFocus
            disabled={isLoading}
            {...register('username')}
            className={cn(
              'h-[54px] rounded-xl border-[#E2E8F0] bg-white pl-11 pr-4 text-[15px] text-[#0F172A] shadow-[0_1px_2px_rgba(15,23,42,0.03)] transition-all duration-[250ms] placeholder:text-[#94A3B8] hover:border-[#CBD5E1] focus-visible:border-[#2563EB] focus-visible:ring-[#2563EB]/20 focus-visible:ring-offset-0 focus-visible:shadow-[0_0_0_4px_rgba(37,99,235,0.08),0_6px_18px_rgba(15,23,42,0.06)]',
              errors.username && 'border-red-400 focus-visible:border-red-500 focus-visible:ring-red-500/20'
            )}
          />
        </div>
        {errors.username && (
          <p className="text-sm font-medium text-red-500">{errors.username.message}</p>
        )}
      </div>

      {/* Password Field */}
      <div className="space-y-2.5">
        <Label htmlFor="password" className="text-sm font-semibold text-[#0F172A]">Password</Label>
        <div className="relative">
          <Lock className="pointer-events-none absolute left-4 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-[#94A3B8]" aria-hidden="true" />
          <Input
            id="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Enter your password"
            autoComplete="current-password"
            disabled={isLoading}
            {...register('password')}
            className={cn(
              'h-[54px] rounded-xl border-[#E2E8F0] bg-white pl-11 pr-12 text-[15px] text-[#0F172A] shadow-[0_1px_2px_rgba(15,23,42,0.03)] transition-all duration-[250ms] placeholder:text-[#94A3B8] hover:border-[#CBD5E1] focus-visible:border-[#2563EB] focus-visible:ring-[#2563EB]/20 focus-visible:ring-offset-0 focus-visible:shadow-[0_0_0_4px_rgba(37,99,235,0.08),0_6px_18px_rgba(15,23,42,0.06)]',
              errors.password && 'border-red-400 focus-visible:border-red-500 focus-visible:ring-red-500/20'
            )}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            aria-pressed={showPassword}
            className="absolute right-4 top-1/2 -translate-y-1/2 rounded-md p-1 text-[#94A3B8] transition-colors duration-[250ms] hover:text-[#2563EB] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB] focus-visible:ring-offset-2"
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" aria-hidden="true" />
            ) : (
              <Eye className="h-4 w-4" aria-hidden="true" />
            )}
          </button>
        </div>
        {errors.password && (
          <p className="text-sm font-medium text-red-500">{errors.password.message}</p>
        )}
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        className="h-[54px] w-full rounded-xl bg-gradient-to-r from-[#4F8EF7] to-[#2563EB] text-[15px] font-bold text-white shadow-[0_14px_28px_rgba(37,99,235,0.24)] transition-all duration-[250ms] hover:-translate-y-0.5 hover:from-[#3F7FE8] hover:to-[#1D4ED8] hover:shadow-[0_18px_36px_rgba(37,99,235,0.28)] focus-visible:ring-[#2563EB]/30 disabled:translate-y-0 disabled:opacity-70"
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
          className="text-sm font-medium text-[#2563EB] transition-colors duration-[250ms] hover:text-[#1D4ED8] hover:underline focus-visible:rounded-md focus-visible:ring-[#2563EB]/30"
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
