"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface NdviPoint {
  item_id: string;
  date: string;
  cloud_cover: number;
  ndvi_mean: number;
  ndvi_p10: number;
  ndvi_p90: number;
}

export interface NdviSnapshot {
  ndvi_mean: number | null;
  valid_ratio: number;
  p10?: number;
  p50?: number;
  p90?: number;
}

export interface NdviData {
  bbox: number[];
  zone: string;
  series: NdviPoint[];
  snapshot: NdviSnapshot;
  threshold: number;
}

const THRESHOLD = 0.3;

/** Série temporelle NDVI réelle (Sentinel-2, lac Ontario). */
export function NdviSeriesChart() {
  const [data, setData] = useState<NdviData | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    fetch("/data/ndvi-real.json")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d: NdviData) => setData(d))
      .catch(() => setLoadError(true));
  }, []);

  if (loadError) {
    return (
      <p className="empty-state" role="alert">
        Données NDVI non disponibles — lancez le calcul Sentinel-2.
      </p>
    );
  }
  if (data === null || data.series.length === 0) {
    return <p className="empty-state">Chargement des données NDVI…</p>;
  }

  const chartData = data.series.map((p) => ({
    date: new Date(p.date + "T00:00:00Z").toLocaleDateString("fr-CA", {
      day: "numeric",
      month: "short",
    }),
    mean: Number(p.ndvi_mean.toFixed(3)),
    p10: Number(p.ndvi_p10.toFixed(3)),
    p90: Number(p.ndvi_p90.toFixed(3)),
  }));

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={chartData} margin={{ top: 8, right: 12, bottom: 4, left: -18 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#64748b" />
          <YAxis
            domain={[0, 1]}
            tick={{ fontSize: 11 }}
            stroke="#64748b"
            tickFormatter={(v: number) => v.toFixed(1)}
          />
          <Tooltip
            formatter={(value) => [
              typeof value === "number" ? value.toFixed(3) : String(value),
              "NDVI",
            ]}
          />
          <ReferenceLine
            y={THRESHOLD}
            stroke="#dc2626"
            strokeDasharray="4 4"
            label={{ value: "Seuil 0.30", position: "right", fontSize: 11, fill: "#dc2626" }}
          />
          <Line
            type="monotone"
            dataKey="mean"
            stroke="#0d9488"
            strokeWidth={2.5}
            dot={{ r: 4, fill: "#0d9488" }}
            name="NDVI moyen"
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="chart-caption">
        NDVI = (NIR−R)/(NIR+R) · pixels validés par le masque SCL · source{" "}
        {data.series[0]?.item_id.slice(0, 12)}…
      </p>
    </div>
  );
}
