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

        {/* Bloc pédagogique / explainer */}
        <section className="explainer" aria-labelledby="expliquer-titre">
          <h2 id="expliquer-titre">Comprendre ce que vous voyez</h2>
          <div className="explainer-grid">
            <div className="explainer-card">
              <h3>🌿 C'est quoi le NDVI ?</h3>
              <p>
                Le <strong>NDVI</strong> (Normalized Difference Vegetation Index) mesure la santé
                de la végétation depuis l'espace. Calculé à partir des bandes rouge et
                proche-infrarouge de Sentinel-2, il va de <strong>-1 à +1</strong> :
              </p>
              <ul>
                <li><strong>&gt; 0.5</strong> : végétation dense et saine (forêts, cultures)</li>
                <li><strong>0.2 – 0.5</strong> : végétation modérée ou clairsemée</li>
                <li><strong>&lt; 0.2</strong> : sol nu, eau ou végétation dégradée</li>
              </ul>
            </div>
            <div className="explainer-card">
              <h3>⚖️ Pourquoi un seuil à 0.30 ?</h3>
              <p>
                Une berge végétalisée retient le sol : les racines freinent l'érosion et
                filtrent les eaux de ruissellement. Sous un NDVI moyen de{" "}
                <strong>0.30</strong>, la couverture végétale est jugée insuffisante pour
                protéger la berge — c'est le <strong>seuil réglementaire</strong> utilisé
                pour déclencher une alerte.
              </p>
            </div>
            <div className="explainer-card">
              <h3>🚨 Comment lire une alerte ?</h3>
              <p>
                Une alerte <strong>« Critique »</strong> signifie que le NDVI moyen d'une
                zone est tombé sous le seuil : la végétation s'est dégradée et la berge est
                exposée à l'érosion. Le pipeline compare chaque observation satellite à ce
                seuil et notifie automatiquement les équipes de restauration.
              </p>
            </div>
            <div className="explainer-card">
              <h3>🛰️ D'où viennent les données ?</h3>
              <p>
                Les images proviennent du satellite <strong>Sentinel-2</strong> (programme
                Copernicus, gratuit et ouvert), récupérées via l'API STAC Earth Search.
                Chaque scène passe par un masquage des nuages (SCL) puis un calcul du NDVI,
                avant d'être archivée dans une base géographique et comparée au seuil.
              </p>
            </div>
          </div>
        </section>

        <footer className="dashboard-footer">
          Données : Sentinel-2 L2A (Copernicus, Earth Search) · traitée par le pipeline
          Riverside (cloud removal SCL + NDVI) · API v0.3
        </footer>
      </div>
    </>
  );
}
