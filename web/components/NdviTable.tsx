"use client";

import { useEffect, useState } from "react";
import { fetchNdviSeries, type NdviSeriesPoint } from "@/lib/api";

const THRESHOLD = 0.3;

/** Statut d'un point vs seuil réglementaire / compliance status vs threshold. */
function statusOf(mean: number): { label: string; className: string } {
  if (mean >= THRESHOLD) return { label: "Conforme", className: "ok" };
  if (mean >= 0.8 * THRESHOLD) return { label: "Sous seuil", className: "warn" };
  return { label: "Critique", className: "crit" };
}

/** Tableau d'évolution NDVI documenté / documented NDVI evolution table. */
export function NdviTable({ aoiId }: { aoiId: string }) {
  const [points, setPoints] = useState<NdviSeriesPoint[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNdviSeries(aoiId)
      .then((d) => setPoints(d.series))
      .catch((e: Error) => setError(e.message));
  }, [aoiId]);

  if (error !== null) {
    return (
      <p className="empty-state" role="alert">
        {error}
      </p>
    );
  }
  if (points === null) {
    return <p className="empty-state">Chargement de l'évolution NDVI…</p>;
  }
  if (points.length === 0) {
    return (
      <p className="empty-state" role="alert">
        Aucune observation enregistrée — l'ingestion réelle n'a pas encore
        persisté de série pour cette AOI.
      </p>
    );
  }

  return (
    <div className="table-wrap">
      <table className="ndvi-table">
        <caption className="sr-only">Évolution du NDVI au fil du temps</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">NDVI moyen</th>
            <th scope="col">Min / Max (p10–p90)</th>
            <th scope="col">NDWI</th>
            <th scope="col">Statut vs seuil 0.30</th>
          </tr>
        </thead>
        <tbody>
          {points.map((p) => {
            const st = statusOf(p.ndvi_mean);
            return (
              <tr key={p.date}>
                <td>
                  {new Date(p.date + "T00:00:00Z").toLocaleDateString("fr-CA", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })}
                </td>
                <td className="num">{p.ndvi_mean.toFixed(3)}</td>
                <td className="num">
                  {p.ndvi_p10 !== null && p.ndvi_p90 !== null
                    ? `${p.ndvi_p10.toFixed(2)} – ${p.ndvi_p90.toFixed(2)}`
                    : "—"}
                </td>
                <td className="num">
                  {p.ndwi_mean !== null ? p.ndwi_mean.toFixed(3) : "—"}
                </td>
                <td>
                  <span className={`badge-status ${st.className}`}>{st.label}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="chart-caption">
        NDWI &lt; 0 = surface humide (eau/berge saturée) · p10–p90 = variabilité
        spatiale des pixels · seuil réglementaire 0.30
      </p>
    </div>
  );
}
