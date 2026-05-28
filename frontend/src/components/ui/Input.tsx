import { cn } from "@/lib/utils";
import { forwardRef } from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, icon, className, ...props }, ref) => (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-xs font-medium text-text-secondary">{label}</label>}
      <div className="relative">
        {icon && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">{icon}</span>
        )}
        <input
          ref={ref}
          className={cn(
            "w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted",
            "focus:outline-none focus:border-accent-blue/60 focus:ring-1 focus:ring-accent-blue/20 transition-colors",
            icon && "pl-9",
            error && "border-rose-500/50",
            className
          )}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-rose-400">{error}</p>}
    </div>
  )
);

Input.displayName = "Input";
