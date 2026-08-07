import { AlertsMap } from "@/components/AlertsMap";
import { fetchOpenAlerts, type Alert } from "@/lib/api";

// SSR : données fraîches à chaque requête / fresh data per request
export const dynamic = "force-dynamic";

// GEO : schema.org pour citabilité IA / structured data for AI citability
const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "Riverside",
  applicationCategory: "EnvironmentalMonitoring",
  operatingSystem: "Web",
  inLanguage: "fr-CA",
  description:
    "Surveillance automatisée des berges : NDVI Sentinel-2, alertes CSR.",
};

export default async function DashboardPage() {
  let alerts: Alert[] = [];
  let error: string | null = null;
  try {
    alerts = await fetchOpenAlerts();
  } catch {
    error = "API indisponible — vérifiez que le service Riverside est démarré.";
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "1rem", padding: "1rem" }}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <section aria-labelledby="alertes-titre">
        <h1 id="alertes-titre">Alertes ouvertes</h1>
        {error !== null && <p role="alert">{error}</p>}
        {alerts.length === 0 && error === null && <p>Aucune alerte active.</p>}
        <ul>
          {alerts.map((a) => (
            <li key={a.id}>
              <strong>{a.severity.toUpperCase()}</strong> — {a.metric} ={" "}
              {a.value.toFixed(3)} (seuil {a.threshold.toFixed(2)}) — AOI{" "}
              {a.aoi_id}
            </li>
          ))}
        </ul>
      </section>
      <section aria-label="Carte des zones surveillées">
        <AlertsMap />
      </section>
    </div>
  );
}
