/**
 * Wellfond BMS - Login Page
 * ===========================
 * Username input, password input, login button.
 * Redirects by role on success.
 */

'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Eye, EyeOff, Lock, User } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { login } from '@/lib/api';
import { toast } from 'sonner';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnUrl = searchParams.get('returnUrl') || '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login({ username: email, password });

      // Redirect based on return URL or default to dashboard
      const redirectPath = returnUrl.startsWith('/login') ? '/dashboard' : returnUrl;
      router.push(redirectPath);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="border-[#C0D8EE] shadow-xl">
      <CardHeader className="space-y-1">
        <CardTitle className="text-center text-2xl font-bold text-[#0D2030]">
          Welcome Back
        </CardTitle>
        <CardDescription className="text-center text-[#4A7A94]">
          Sign in to your Wellfond BMS account
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div className="space-y-2">
            <label
              htmlFor="email"
              className="text-sm font-medium text-[#0D2030]"
            >
              Email
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#4A7A94]" />
              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-lg border border-[#C0D8EE] bg-white py-2.5 pl-10 pr-4 text-sm text-[#0D2030] placeholder:text-[#4A7A94]/50 focus:border-[#F97316] focus:outline-none focus:ring-2 focus:ring-[#F97316]/20"
              />
            </div>
          </div>

          {/* Password */}
          <div className="space-y-2">
            <label
              htmlFor="password"
              className="text-sm font-medium text-[#0D2030]"
            >
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#4A7A94]" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full rounded-lg border border-[#C0D8EE] bg-white py-2.5 pl-10 pr-10 text-sm text-[#0D2030] placeholder:text-[#4A7A94]/50 focus:border-[#F97316] focus:outline-none focus:ring-2 focus:ring-[#F97316]/20"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#4A7A94] hover:text-[#0D2030]"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <div className="rounded-lg bg-[#D94040]/10 px-4 py-3 text-sm text-[#D94040]">
              {error}
            </div>
          )}

          {/* Submit button */}
          <Button
            type="submit"
            variant="primary"
            size="lg"
            loading={isLoading}
            className="w-full"
          >
            Sign In
          </Button>
        </form>

        {/* Demo credentials hint */}
        <div className="mt-6 rounded-lg bg-[#E8F4FF] p-4 text-center">
          <p className="text-xs text-[#4A7A94]">
            <strong>Demo Credentials:</strong>
          </p>
          <p className="mt-1 text-xs text-[#4A7A94]">
            Email: admin@wellfond.sg
          </p>
          <p className="text-xs text-[#4A7A94]">Password: admin123</p>
        </div>
      </CardContent>
    </Card>
  );
}
