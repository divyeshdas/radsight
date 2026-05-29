import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  glass?: boolean;
  onClick?: () => void;
}

export function Card({ children, className, glass, onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "rounded-xl p-4",
        glass ? "glass-card" : "panel",
        onClick && "cursor-pointer hover:border-accent-blue/40 transition-colors",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-center justify-between mb-4", className)}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <h3 className={cn("font-semibold text-text-secondary uppercase tracking-wider", className)}
      style={{ fontSize: 13, fontWeight: 600, letterSpacing: "0.06em" }}>
      {children}
    </h3>
  );
}
