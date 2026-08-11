/**
 * Client API Riverside — typé strict, zéro `any`.
 * EN: Strictly-typed Riverside API client.
 */

export interface Alert {
  id: string;
  aoi_id: string;
  aoi_name?: string;
  raised_at: string;
  metric: string;
  value: number;
  threshold: number;
  severity: "info" | "warning" | "critical";
  acknowledged: boolean;
}

interface OpenAlertsResponse {
  count: number;
  alerts: Alert[];
}

const API_URL: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Alertes non acquittées / fetch unacknowledged alerts (throws on HTTP error). */
export async function fetchOpenAlerts(aoiId?: string): Promise<Alert[]> {
  const params = aoiId !== undefined ? `?aoi_id=${encodeURIComponent(aoiId)}` : "";
  const res = await fetch(`${API_URL}/api/v1/alerts/open${params}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  const data = (await res.json()) as OpenAlertsResponse;
  return data.alerts;
}

/** Acquitte une alerte / acknowledge an alert. */
export async function acknowledgeAlert(alertId: string): Promise<void> {
  const res = await fetch(
    `${API_URL}/api/v1/alerts/${encodeURIComponent(alertId)}/acknowledge`,
    { method: "POST" },
  );
  if (!res.ok) {
    throw new Error(`Acknowledge failed: HTTP ${res.status}`);
  }
}

export interface NdviSeriesPoint {
  date: string;
  ndvi_mean: number;
  ndvi_p10: number | null;
  ndvi_p90: number | null;
  ndwi_mean: number | null;
}

export interface NdviSeriesResponse {
  aoi_id: string;
  threshold: number;
  months?: number;
  from_date?: string;
  count: number;
  series: NdviSeriesPoint[];
}

/** Série temporelle NDVI d'une AOI sur les N derniers mois (défaut 12). */
export async function fetchNdviSeries(
  aoiId: string,
  months = 12,
): Promise<NdviSeriesResponse> {
  const res = await fetch(
    `${API_URL}/api/v1/ndvi/series?aoi_id=${encodeURIComponent(aoiId)}&months=${months}`,
    { cache: "no-store" },
  );
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return (await res.json()) as NdviSeriesResponse;
}

/** Formate une date ISO (YYYY-MM-DD) sans décalage de fuseau horaire.
 * EN: Format an ISO date without timezone shift (avoids off-by-one day). */
export function formatIsoDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const months = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
  return `${d} ${months[(m ?? 1) - 1]} ${y}`;
}
