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
import { fetchNdviSeries, formatIsoDate, type NdviSeriesResponse } from "@/lib/api";

const DEFAULT_THRESHOLD = 0.3;
const REFRESH_MS = 15_000; // rafraîchissement temps réel / live refresh

/** Série temporelle NDVI — alimentée par l'API, rafraîchie en temps réel. */
export function NdviSeriesChart({ aoiId, months = 6 }: { aoiId: string; months?: number }) {
  const [data, setData] = useState<NdviSeriesResponse | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      fetchNdviSeries(aoiId, months)
        .then((d) => {
          if (!cancelled) {
            setData(d);
            setLoadError(false);
          }
        })
        .catch(() => {
          if (!cancelled) setLoadError(true);
        });
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [aoiId, months]);

  if (loadError) {
    return (
      <p className="empty-state" role="alert">
        Données NDVI non disponibles — vérifiez que l'API est joignable.
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
        d'ingestion (STAC → NDVI → ndvi_series).
      </p>
    );
  }

  const threshold = data.threshold ?? DEFAULT_THRESHOLD;
  const chartData = data.series.map((p) => ({
    date: formatIsoDate(p.date).replace(/ \d{4}$/, ""), // "10 août" sans année
    mean: Number(p.ndvi_mean.toFixed(3)),
  }));
  const last = data.series[data.series.length - 1];

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={240}>
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
        Dernière observation : {last.date} · NDVI {last.ndvi_mean.toFixed(3)} ·
        fenêtre {months} derniers mois · mise à jour toutes les 15 s · API /api/v1/ndvi/series
      </p>
    </div>
  );
}
