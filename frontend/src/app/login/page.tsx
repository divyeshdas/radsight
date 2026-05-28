"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Activity } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/store/auth";
import { login } from "@/lib/auth";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type LoginForm = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const { setUser } = useAuthStore();
  const [error, setError] = useState("");

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginForm>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: LoginForm) => {
    setError("");
    try {
      const user = await login(data.email, data.password);
      setUser(user);
      router.push("/dashboard");
    } catch {
      setError("Invalid email or password");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4"
      style={{ backgroundColor: "var(--bg-primary)" }}>

      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-9 h-9 rounded-xl bg-accent-blue flex items-center justify-center">
            <Activity size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-text-primary">RadSight</h1>
            <p className="text-xs text-text-muted">AI Radiology Intelligence</p>
          </div>
        </div>

        {/* Card */}
        <div className="glass-card rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-1">Sign in to your workspace</h2>
          <p className="text-xs text-text-muted mb-6">Enter your credentials to access RadSight</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              label="Email address"
              type="email"
              placeholder="you@hospital.org"
              {...register("email")}
              error={errors.email?.message}
              autoComplete="email"
            />
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              {...register("password")}
              error={errors.password?.message}
              autoComplete="current-password"
            />

            {error && (
              <p className="text-xs text-rose-400 text-center">{error}</p>
            )}

            <Button type="submit" className="w-full" loading={isSubmitting}>
              Sign in
            </Button>
          </form>

          <div className="mt-5 pt-4" style={{ borderTop: "1px solid var(--border-subtle)" }}>
            <p className="text-[11px] text-text-muted mb-2">Demo credentials</p>
            <div className="space-y-1 font-mono text-[11px] text-text-muted">
              <p>admin@radsight.health / RadSight@Admin2024</p>
              <p>radiologist@radsight.health / RadSight@Rad2024</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
