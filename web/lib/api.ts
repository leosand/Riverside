/**
 * Client API Riverside — typé strict, zéro `any`.
 * EN: Strictly-typed Riverside API client.
 */

export interface Alert {
  id: string;
  aoi_id: string;
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
