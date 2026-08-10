import type { Alert } from "@/lib/api";

const SEVERITY_LABEL: Record<Alert["severity"], string> = {
  critical: "Critique",
  warning: "Avertissement",
  info: "Info",
};

/** Panneau des alertes réglementaires ouvertes. */
export function AlertPanel({ alerts, error }: { alerts: Alert[]; error: string | null }) {
  if (error !== null) {
    return <p className="empty-state" role="alert">{error}</p>;
  }
  if (alerts.length === 0) {
    return <p className="empty-state">Aucune alerte active — la végétation est saine.</p>;
  }
  return (
    <ul className="alert-list">
      {alerts.map((a) => (
        <li key={a.id} className={`alert-item alert-${a.severity}`}>
          <div className="alert-top">
            <span className="alert-severity">{SEVERITY_LABEL[a.severity]}</span>
            <time dateTime={a.raised_at}>
              {new Date(a.raised_at).toLocaleDateString("fr-CA")}
            </time>
          </div>
          <p className="alert-metric">
            {a.metric} = <strong>{a.value.toFixed(3)}</strong>
            <span className="alert-threshold">seuil {a.threshold.toFixed(2)}</span>
          </p>
          <p className="alert-aoi">AOI {a.aoi_id.slice(0, 8)}…</p>
        </li>
      ))}
    </ul>
  );
}
