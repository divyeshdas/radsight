import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { SeverityLevel } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(n: number, decimals = 0): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toFixed(decimals);
}

export function formatPercent(n: number, decimals = 1): string {
  return `${(n * 100).toFixed(decimals)}%`;
}

export function formatMs(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
  return `${Math.round(ms)}ms`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function severityColor(severity: SeverityLevel | string | undefined): string {
  const map: Record<string, string> = {
    critical: "#EF4444",
    high: "#F97316",
    severe: "#F97316",
    moderate: "#F59E0B",
    low: "#3B82F6",
    mild: "#3B82F6",
    normal: "#10B981",
  };
  return map[severity ?? ""] ?? "#94A3B8";
}

export function severityLabel(severity: string | undefined): string {
  const map: Record<string, string> = {
    critical: "Critical",
    high: "High",
    severe: "High",
    moderate: "Moderate",
    low: "Low",
    mild: "Low",
    normal: "Normal",
  };
  return map[severity ?? ""] ?? "Unknown";
}

export function riskScoreColor(score: number): string {
  if (score >= 0.8) return "#EF4444";
  if (score >= 0.6) return "#F97316";
  if (score >= 0.35) return "#F59E0B";
  if (score >= 0.15) return "#3B82F6";
  return "#10B981";
}

export function truncate(str: string, maxLen: number): string {
  return str.length > maxLen ? str.slice(0, maxLen) + "…" : str;
}
