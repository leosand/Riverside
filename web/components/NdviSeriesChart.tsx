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

/** Format du fichier ndvi-real.json (généré par scripts/export_ndvi_json.py). */
export interface NdviSeriesPoint {
  date: string;
  ndvi_mean: number;
  ndvi_p10?: number;
  ndvi_p90?: number;
  ndwi_mean?: number;
}

export interface NdviData {
  meta?: { source?: string; generated_at?: string; aoi_id?: string };
  aoi?: { id?: string; bbox?: number[] };
  threshold?: number;
  series: NdviSeriesPoint[];
}

const DEFAULT_THRESHOLD = 0.3;

/** Série temporelle NDVI (Sentinel-2, export pipeline / mise en page). */
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
  if (data === null) {
    return <p className="empty-state">Chargement des données NDVI…</p>;
  }
  if (data.series.length === 0) {
    return (
      <p className="empty-state" role="alert">
        Aucune série NDVI enregistrée pour cette zone — exécutez le pipeline
        d'ingestion (STAC → NDVI → ndvi_series), puis{" "}
        <code>python scripts/export_ndvi_json.py --aoi-id &lt;uuid&gt;</code>.
      </p>
    );
  }

  const threshold = data.threshold ?? DEFAULT_THRESHOLD;
  const chartData = data.series.map((p) => ({
    date: new Date(p.date + "T00:00:00Z").toLocaleDateString("fr-CA", {
      day: "numeric",
      month: "short",
    }),
    mean: Number(p.ndvi_mean.toFixed(3)),
  }));
  const sourceLabel =
    data.meta?.source && data.meta.source !== "synthetic_placeholder"
      ? `source ${data.meta.source}`
      : "données de mise en page (régénérer via scripts/export_ndvi_json.py)";

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
            y={threshold}
            stroke="#dc2626"
            strokeDasharray="4 4"
            label={{ value: `Seuil ${threshold.toFixed(2)}`, position: "right", fontSize: 11, fill: "#dc2626" }}
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
        NDVI = (NIR−R)/(NIR+R) · {sourceLabel}
      </p>
    </div>
  );
}
