import { cn, severityColor } from "@/lib/utils";

interface BadgeProps {
  label: string;
  variant?: "severity" | "status" | "default";
  severity?: string;
  className?: string;
}

export function Badge({ label, variant = "default", severity, className }: BadgeProps) {
  if (variant === "severity" && severity) {
    const color = severityColor(severity);
    return (
      <span
        className={cn("inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium", className)}
        style={{ color, backgroundColor: `${color}18`, border: `1px solid ${color}30` }}
      >
        <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
        {label}
      </span>
    );
  }

  const statusStyles: Record<string, string> = {
    completed: "text-emerald-400 bg-emerald-400/10 border border-emerald-400/20",
    pending:   "text-amber-400 bg-amber-400/10 border border-amber-400/20",
    processing:"text-blue-400 bg-blue-400/10 border border-blue-400/20",
    failed:    "text-rose-400 bg-rose-400/10 border border-rose-400/20",
    default:   "text-text-secondary bg-surface border border-border",
  };

  return (
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
      statusStyles[label.toLowerCase()] ?? statusStyles.default, className)}>
      {label}
    </span>
  );
}
