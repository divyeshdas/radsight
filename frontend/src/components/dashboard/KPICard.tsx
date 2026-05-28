"use client";

import { motion } from "framer-motion";
import { cn, formatNumber } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: LucideIcon;
  accent?: string;
  suffix?: string;
  mono?: boolean;
  index?: number;
}

export function KPICard({ title, value, change, icon: Icon, accent = "#0EA5E9", suffix, mono, index = 0 }: KPICardProps) {
  const isPositiveGood = change !== undefined && change > 0;
  const changeColor = change === undefined ? "" : change > 0 ? "#10B981" : change < 0 ? "#EF4444" : "#94A3B8";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="panel rounded-xl p-5 relative overflow-hidden group hover:border-opacity-80 transition-all"
    >
      <div className="absolute top-0 right-0 w-24 h-24 rounded-full opacity-5 -translate-y-6 translate-x-6"
        style={{ backgroundColor: accent }} />

      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">{title}</p>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `${accent}18`, border: `1px solid ${accent}25` }}>
          <Icon size={14} style={{ color: accent }} />
        </div>
      </div>

      <div className="flex items-end gap-2">
        <span className={cn("text-2xl font-bold text-text-primary", mono && "font-mono")}>
          {typeof value === "number" ? formatNumber(value) : value}
          {suffix && <span className="text-sm font-normal text-text-muted ml-1">{suffix}</span>}
        </span>
        {change !== undefined && (
          <span className="text-xs font-medium mb-0.5" style={{ color: changeColor }}>
            {change > 0 ? "↑" : change < 0 ? "↓" : "—"} {Math.abs(change).toFixed(1)}%
          </span>
        )}
      </div>
    </motion.div>
  );
}
