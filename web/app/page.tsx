import type { Metadata } from "next";
import { fetchOpenAlerts, type Alert } from "@/lib/api";
import { NdviMap } from "@/components/NdviMap";
import { NdviSeriesChart } from "@/components/NdviSeriesChart";
import { AlertPanel } from "@/components/AlertPanel";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Riverside — Surveillance des berges",
  description:
    "Surveillance automatisée des berges du lac Ontario : NDVI Sentinel-2, séries temporelles et alertes réglementaires CSR.",
};

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
  areaServed: { "@type": "Place", name: "Lac Ontario, Canada" },
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
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div className="dashboard">
        <header className="dashboard-header">
          <div>
            <h1>Surveillance des berges</h1>
            <p className="subtitle">
              Lac Ontario · NDVI Sentinel-2 · Seuil réglementaire 0.30
            </p>
          </div>
          <div className="status-pill" role="status">
            <span className="dot" aria-hidden="true" />
            Données satellite en direct
          </div>
        </header>

        <main className="dashboard-grid">
          {/* Carte NDVI */}
          <section className="panel panel-map" aria-labelledby="carte-titre">
            <div className="panel-head">
              <h2 id="carte-titre">Carte NDVI — zone surveillée</h2>
              <span className="legend-note">Vert = végétation dense · Rouge = sol/érosion</span>
            </div>
            <NdviMap />
          </section>

          {/* Colonne droite : série temporelle + alertes */}
          <div className="side-column">
            <section className="panel" aria-labelledby="serie-titre">
              <div className="panel-head">
                <h2 id="serie-titre">Évolution NDVI (juin–juil. 2026)</h2>
              </div>
              <NdviSeriesChart />
            </section>

            <section className="panel" aria-labelledby="alertes-titre">
              <div className="panel-head">
                <h2 id="alertes-titre">Alertes réglementaires</h2>
                <span className="badge">{alerts.length}</span>
              </div>
              <AlertPanel alerts={alerts} error={error} />
            </section>
          </div>
        </main>

        <footer className="dashboard-footer">
          Données : Sentinel-2 L2A (Copernicus, Earth Search) · traitée par le pipeline
          Riverside (cloud removal SCL + NDVI) · API v0.3
        </footer>
      </div>
    </>
  );
}
