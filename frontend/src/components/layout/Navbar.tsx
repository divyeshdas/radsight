"use client";

import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { Bell, Wifi, WifiOff } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useState, useCallback } from "react";
import type { DashboardKPIs } from "@/types";

interface NavbarProps {
  title: string;
  subtitle?: string;
  onKPIUpdate?: (kpis: DashboardKPIs) => void;
}

export function Navbar({ title, subtitle, onKPIUpdate }: NavbarProps) {
  const [alerts, setAlerts] = useState(0);

  const handleMessage = useCallback((data: unknown) => {
    const msg = data as { type: string; data?: { kpis?: DashboardKPIs } };
    if (msg.type === "kpi_update" && msg.data?.kpis && onKPIUpdate) {
      onKPIUpdate(msg.data.kpis);
    }
  }, [onKPIUpdate]);

  const { status } = useWebSocket("/ws/analytics", { onMessage: handleMessage });

  return (
    <header className="h-16 flex items-center justify-between px-6"
      style={{
        backgroundColor: "var(--navbar-bg)",
        borderBottom: "1px solid var(--navbar-border)",
      }}>
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 700, lineHeight: 1.2, color: "var(--navbar-text-primary)" }}>{title}</h1>
        {subtitle && <p style={{ fontSize: 12, fontWeight: 400, color: "var(--navbar-text-muted)", marginTop: 2 }}>{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs"
          style={{ color: status === "connected" ? "var(--accent-emerald)" : "var(--navbar-text-muted)" }}>
          {status === "connected"
            ? <Wifi size={12} />
            : <WifiOff size={12} />}
          <span className="font-mono hidden sm:block">
            {status === "connected" ? "live" : status}
          </span>
        </div>

        <button className="relative p-1.5 rounded-lg transition-colors"
          style={{ color: "var(--navbar-text-primary)" }}>
          <Bell size={15} />
          {alerts > 0 && (
            <span className="absolute top-0.5 right-0.5 w-3.5 h-3.5 bg-rose-500 text-white text-[9px] rounded-full flex items-center justify-center font-bold">
              {alerts}
            </span>
          )}
        </button>

        <ThemeToggle />
      </div>
    </header>
  );
}
