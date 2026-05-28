"use client";

import ReactECharts from "echarts-for-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { severityColor } from "@/lib/utils";

interface SeverityChartProps {
  data: Array<{ severity: string; count: number }>;
}

export function SeverityChart({ data }: SeverityChartProps) {
  const pieData = data.map((d) => ({
    name: d.severity.charAt(0).toUpperCase() + d.severity.slice(1),
    value: d.count,
    itemStyle: { color: severityColor(d.severity) },
  }));

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "var(--bg-elevated)",
      borderColor: "var(--border-color)",
      textStyle: { color: "var(--text-primary)", fontSize: 12 },
      formatter: "{b}: {c} ({d}%)",
    },
    legend: {
      orient: "vertical",
      right: 10,
      top: "center",
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: "var(--text-secondary)", fontSize: 11 },
    },
    series: [
      {
        type: "pie",
        radius: ["45%", "72%"],
        center: ["40%", "50%"],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 4, borderWidth: 2, borderColor: "var(--bg-panel)" },
        label: { show: false },
        emphasis: {
          scale: true,
          scaleSize: 6,
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: "rgba(0,0,0,0.3)" },
        },
        data: pieData,
      },
    ],
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Severity Distribution</CardTitle>
        <span className="text-xs text-text-muted">Last 30 days</span>
      </CardHeader>
      <ReactECharts option={option} style={{ height: 240 }} notMerge />
    </Card>
  );
}
