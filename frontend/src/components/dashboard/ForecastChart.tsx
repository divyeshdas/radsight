"use client";

import ReactECharts from "echarts-for-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";

interface ForecastRow {
  date: string;
  forecast: number;
  lower: number;
  upper: number;
}

export function ForecastChart({ data }: { data: ForecastRow[] }) {
  const dates = data.map((d) => d.date);
  const forecasts = data.map((d) => d.forecast);
  const bands = data.map((d) => [d.lower, d.upper]);

  const option = {
    backgroundColor: "transparent",
    grid: { left: 12, right: 12, top: 12, bottom: 40, containLabel: true },
    tooltip: {
      trigger: "axis",
      backgroundColor: "var(--bg-elevated)",
      borderColor: "var(--border-color)",
      textStyle: { color: "var(--text-primary)", fontSize: 12 },
    },
    legend: {
      bottom: 0,
      textStyle: { color: "var(--text-secondary)", fontSize: 11 },
      itemWidth: 12, itemHeight: 2,
    },
    xAxis: {
      type: "category",
      data: dates,
      axisLine: { lineStyle: { color: "var(--border-color)" } },
      axisTick: { show: false },
      axisLabel: {
        color: "var(--text-muted)", fontSize: 10,
        formatter: (v: string) => v.slice(5),
        interval: Math.floor(dates.length / 6),
      },
    },
    yAxis: {
      type: "value",
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: "var(--border-subtle)", type: "dashed" } },
      axisLabel: { color: "var(--text-muted)", fontSize: 10 },
    },
    series: [
      {
        name: "Confidence Band",
        type: "custom",
        data: bands,
        renderItem: (_: unknown, api: { value: (i: number) => number; coord: (p: number[]) => number[]; style: () => unknown }) => {
          const xValue = api.coord([0, 0])[0];
          return { type: "group", children: [] };
        },
        silent: true,
        z: 0,
      },
      {
        name: "CI Lower",
        type: "line",
        data: data.map((d) => d.lower),
        lineStyle: { opacity: 0 },
        stack: "ci",
        symbol: "none",
        areaStyle: { color: "transparent" },
      },
      {
        name: "CI Band",
        type: "line",
        data: data.map((d) => d.upper - d.lower),
        lineStyle: { opacity: 0 },
        stack: "ci",
        symbol: "none",
        areaStyle: { color: "#14B8A618", origin: "auto" },
        tooltip: { show: false },
      },
      {
        name: "Forecast",
        type: "line",
        data: forecasts,
        smooth: true,
        lineStyle: { color: "#14B8A6", width: 2 },
        symbol: "none",
        itemStyle: { color: "#14B8A6" },
        areaStyle: {
          color: {
            type: "linear", x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "#14B8A620" },
              { offset: 1, color: "#14B8A600" },
            ],
          },
        },
      },
    ],
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>30-Day Forecast</CardTitle>
        <span className="text-xs text-text-muted font-mono">Prophet model</span>
      </CardHeader>
      <ReactECharts option={option} style={{ height: 240 }} notMerge />
    </Card>
  );
}
