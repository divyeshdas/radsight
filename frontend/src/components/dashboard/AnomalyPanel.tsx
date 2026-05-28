"use client";

import { AlertTriangle, TrendingUp, TrendingDown, Zap } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { cn, formatDate } from "@/lib/utils";

interface Anomaly {
  date: string;
  anomaly_type: string;
  severity: string;
  description: string;
  deviation_score: number;
}

const ANOMALY_ICONS: Record<string, React.ElementType> = {
  critical_surge: Zap,
  volume_spike: TrendingUp,
  volume_drop: TrendingDown,
  flagged_surge: AlertTriangle,
  statistical_anomaly: AlertTriangle,
};

const SEVERITY_STYLES: Record<string, string> = {
  critical: "border-rose-500/30 bg-rose-500/5",
  high:     "border-amber-500/30 bg-amber-500/5",
  moderate: "border-blue-500/30 bg-blue-500/5",
  low:      "border-border bg-surface",
};

const SEVERITY_TEXT: Record<string, string> = {
  critical: "text-rose-400",
  high:     "text-amber-400",
  moderate: "text-blue-400",
  low:      "text-text-muted",
};

export function AnomalyPanel({ anomalies }: { anomalies: Anomaly[] }) {
  if (!anomalies.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Anomaly Alerts</CardTitle>
        </CardHeader>
        <div className="flex flex-col items-center justify-center py-8 text-text-muted">
          <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center mb-2">
            <span className="text-emerald-400 text-sm">✓</span>
          </div>
          <p className="text-xs">No anomalies detected</p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Anomaly Alerts</CardTitle>
        <span className="text-xs font-medium text-rose-400">{anomalies.length} detected</span>
      </CardHeader>
      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
        {anomalies.slice(0, 8).map((a, i) => {
          const Icon = ANOMALY_ICONS[a.anomaly_type] ?? AlertTriangle;
          return (
            <div key={i}
              className={cn("rounded-lg p-3 border text-xs", SEVERITY_STYLES[a.severity] ?? SEVERITY_STYLES.low)}>
              <div className="flex items-start gap-2">
                <Icon size={12} className={cn("mt-0.5 shrink-0", SEVERITY_TEXT[a.severity])} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 mb-0.5">
                    <span className={cn("font-medium", SEVERITY_TEXT[a.severity])}>
                      {a.anomaly_type.replace(/_/g, " ")}
                    </span>
                    <span className="text-text-muted font-mono shrink-0">{a.date}</span>
                  </div>
                  <p className="text-text-secondary leading-relaxed">{a.description}</p>
                  <span className="text-text-muted font-mono">score: {a.deviation_score.toFixed(3)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
