"use client";

import ReactECharts from "echarts-for-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";

interface DiseaseChartProps {
  data: Array<{ disease: string; count: number }>;
}

export function DiseaseChart({ data }: DiseaseChartProps) {
  const sorted = [...data].sort((a, b) => a.count - b.count).slice(-10);

  const option = {
    backgroundColor: "transparent",
    grid: { left: 120, right: 20, top: 8, bottom: 8, containLabel: false },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "none" },
      backgroundColor: "var(--bg-elevated)",
      borderColor: "var(--border-color)",
      textStyle: { color: "var(--text-primary)", fontSize: 12 },
    },
    xAxis: {
      type: "value",
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: "var(--border-subtle)", type: "dashed" } },
      axisLabel: { color: "var(--text-muted)", fontSize: 10 },
    },
    yAxis: {
      type: "category",
      data: sorted.map((d) => d.disease.replace(/_/g, " ")),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "var(--text-secondary)", fontSize: 10 },
    },
    series: [
      {
        type: "bar",
        data: sorted.map((d) => d.count),
        barMaxWidth: 18,
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: {
            type: "linear",
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: "#14B8A610" },
              { offset: 1, color: "#14B8A6" },
            ],
          },
        },
        emphasis: { itemStyle: { color: "#2DD4BF" } },
      },
    ],
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Disease Prevalence</CardTitle>
        <span className="text-xs text-text-muted">Top conditions</span>
      </CardHeader>
      <ReactECharts option={option} style={{ height: 240 }} notMerge />
    </Card>
  );
}
