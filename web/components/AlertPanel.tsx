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

/** Pourcentage de la valeur par rapport au seuil (borné 0-100 pour la jauge). */
function gaugePercent(value: number, threshold: number): number {
  const pct = (value / threshold) * 100;
  return Math.max(0, Math.min(100, pct));
}

/** Panneau des alertes réglementaires — format professionnel. */
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
      {alerts.map((a) => {
        const pct = gaugePercent(a.value, a.threshold);
        return (
          <li key={a.id} className={`alert-item alert-${a.severity}`}>
            <div className="alert-top">
              <span className="alert-severity">{SEVERITY_LABEL[a.severity]}</span>
              <time dateTime={a.raised_at}>
                {new Date(a.raised_at).toLocaleDateString("fr-CA", {
                  year: "numeric",
                  month: "short",
                  day: "numeric",
                })}
              </time>
            </div>

            {/* Métrique principale : valeur vs seuil */}
            <div className="alert-metric">
              <div className="alert-metric-row">
                <span className="alert-label">NDVI moyen</span>
                <span className="alert-value">{a.value.toFixed(2)}</span>
                <span className="alert-sep">/ seuil</span>
                <span className="alert-threshold">{a.threshold.toFixed(2)}</span>
              </div>
              <div className="alert-gauge" role="img" aria-label={`${Math.round(pct)} % du seuil`}>
                <div
                  className={`alert-gauge-fill alert-gauge-${a.severity}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <div className="alert-gauge-labels">
                <span>0</span>
                <span>seuil {a.threshold.toFixed(2)}</span>
                <span>1.0</span>
              </div>
            </div>

            <p className="alert-explain">{SEVERITY_EXPLAIN[a.severity]}</p>
            <p className="alert-aoi">
              Zone surveillée : {a.aoi_name ?? a.aoi_id.slice(0, 8) + "…"}
            </p>
          </li>
        );
      })}
    </ul>
  );
}
