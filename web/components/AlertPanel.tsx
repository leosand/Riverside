import type { Alert } from "@/lib/api";

const SEVERITY_LABEL: Record<Alert["severity"], string> = {
  critical: "Critique",
  warning: "Avertissement",
  info: "Info",
};

const SEVERITY_EXPLAIN: Record<Alert["severity"], string> = {
  critical: "Végétation très dégradée — risque élevé d'érosion de la berge. Action recommandée sous 30 jours.",
  warning: "Végétation sous le seuil réglementaire — surveillance renforcée requise.",
  info: "Information — pas d'action immédiate.",
};

/** Panneau des alertes réglementaires ouvertes — pédagogique. */
export function AlertPanel({ alerts, error }: { alerts: Alert[]; error: string | null }) {
  if (error !== null) {
    return <p className="empty-state" role="alert">{error}</p>;
  }
  if (alerts.length === 0) {
    return (
      <div className="alert-help">
        <p className="empty-state">Aucune alerte active — la végétation est saine.</p>
      </div>
    );
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
            NDVI moyen = <strong>{a.value.toFixed(2)}</strong>
            <span className="alert-threshold">seuil réglementaire {a.threshold.toFixed(2)}</span>
          </p>
          <p className="alert-explain">{SEVERITY_EXPLAIN[a.severity]}</p>
          <p className="alert-aoi">Zone surveillée : {a.aoi_id.slice(0, 8)}…</p>
        </li>
      ))}
    </ul>
  );
}
