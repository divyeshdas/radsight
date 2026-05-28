import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export function Button({ variant = "primary", size = "md", loading, className, children, disabled, ...props }: ButtonProps) {
  const base = "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed";

  const variants = {
    primary:   "bg-accent-blue text-white hover:opacity-90 active:scale-95",
    secondary: "bg-surface border border-border text-text-primary hover:border-accent-blue/50 active:scale-95",
    ghost:     "text-text-secondary hover:text-text-primary hover:bg-surface active:scale-95",
    danger:    "bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500/20 active:scale-95",
  };

  const sizes = {
    sm:  "px-3 py-1.5 text-xs",
    md:  "px-4 py-2 text-sm",
    lg:  "px-5 py-2.5 text-base",
  };

  return (
    <button className={cn(base, variants[variant], sizes[size], className)} disabled={disabled || loading} {...props}>
      {loading && <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />}
      {children}
    </button>
  );
}
