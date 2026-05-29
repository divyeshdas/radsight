"use client";

import { useState, useCallback } from "react";
import useSWR from "swr";
import {
  FileText, AlertTriangle, Activity, Clock,
  TrendingUp, Flag,
} from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { KPICard } from "@/components/dashboard/KPICard";
import { SeverityChart } from "@/components/dashboard/SeverityChart";
import { DiseaseChart } from "@/components/dashboard/DiseaseChart";
import { TrendChart } from "@/components/dashboard/TrendChart";
import { ForecastChart } from "@/components/dashboard/ForecastChart";
import { AnomalyPanel } from "@/components/dashboard/AnomalyPanel";
import { KPICardSkeleton, ChartSkeleton } from "@/components/ui/Skeleton";
import { api } from "@/lib/api";
import { formatMs } from "@/lib/utils";
import type { DashboardKPIs } from "@/types";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

export default function DashboardPage() {
  const [liveKPIs, setLiveKPIs] = useState<DashboardKPIs | null>(null);

  const { data: kpis, isLoading: kpisLoading } = useSWR<DashboardKPIs>(
    "/analytics/kpis", fetcher, { refreshInterval: 30000 }
  );
  const { data: severity } = useSWR("/analytics/severity", fetcher, { refreshInterval: 60000 });
  const { data: diseases } = useSWR("/analytics/diseases", fetcher, { refreshInterval: 60000 });
  const { data: trends } = useSWR("/analytics/trends?days=90", fetcher, { refreshInterval: 60000 });
  const { data: forecast } = useSWR("/analytics/forecast?periods=30", fetcher, { refreshInterval: 300000 });
  const { data: anomalies } = useSWR("/analytics/anomalies", fetcher, { refreshInterval: 60000 });

  const handleKPIUpdate = useCallback((data: DashboardKPIs) => {
    setLiveKPIs(data);
  }, []);

  const activeKPIs = liveKPIs ?? kpis;

  return (
    <div className="flex flex-col flex-1">
      <Navbar
        title="Dashboard"
        subtitle="Real-time radiology intelligence"
        onKPIUpdate={handleKPIUpdate}
      />

      <div className="flex-1 p-6 space-y-6">
        {/* KPI row */}
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {kpisLoading && !activeKPIs
            ? Array.from({ length: 6 }).map((_, i) => <KPICardSkeleton key={i} />)
            : <>
              <KPICard title="Total Reports" value={activeKPIs?.total_reports ?? 0}
                icon={FileText} accent="#2563EB" index={0} />
              <KPICard title="Today" value={activeKPIs?.reports_today ?? 0}
                icon={Activity} accent="#06B6D4" index={1} />
              <KPICard title="Critical Cases" value={activeKPIs?.critical_cases ?? 0}
                icon={AlertTriangle} accent="#EF4444" index={2} />
              <KPICard title="Flagged" value={activeKPIs?.flagged_for_review ?? 0}
                icon={Flag} accent="#F97316" index={3} />
              <KPICard title="Avg Risk Score"
                value={((activeKPIs?.avg_risk_score ?? 0) * 100).toFixed(1)}
                suffix="%" icon={TrendingUp} accent="#10B981" mono index={4} />
              <KPICard title="Avg Processing"
                value={formatMs(activeKPIs?.avg_processing_ms ?? 0)}
                icon={Clock} accent="#8B5CF6" mono index={5} />
            </>
          }
        </div>

        {/* Main charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {trends?.trend_data
            ? <TrendChart data={trends.trend_data} />
            : <ChartSkeleton />}
          {forecast?.forecast?.length
            ? <ForecastChart data={forecast.forecast} />
            : <ChartSkeleton />}
        </div>

        {/* Secondary charts + anomalies */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {severity?.length
            ? <SeverityChart data={severity} />
            : <ChartSkeleton height={240} />}
          {diseases?.length
            ? <DiseaseChart data={diseases} />
            : <ChartSkeleton height={240} />}
          <AnomalyPanel anomalies={anomalies?.anomalies ?? []} />
        </div>
      </div>
    </div>
  );
}
