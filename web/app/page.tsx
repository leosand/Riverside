import type { Metadata } from "next";
import { fetchOpenAlerts, type Alert } from "@/lib/api";
import { NdviMap } from "@/components/NdviMap";
import { NdviSeriesChart } from "@/components/NdviSeriesChart";
import { AlertPanel } from "@/components/AlertPanel";
import { NdviTable } from "@/components/NdviTable";

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

            <section className="panel" aria-labelledby="table-titre">
              <div className="panel-head">
                <h2 id="table-titre">Tableau d'évolution NDVI</h2>
                <span className="legend-note">Données réelles · API /api/v1/ndvi/series</span>
              </div>
              <NdviTable aoiId="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa" />
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

        {/* Bloc projet / À propos */}
        <section className="explainer" aria-labelledby="projet-titre">
          <h2 id="projet-titre">Le projet en bref</h2>
          <div className="explainer-grid">
            <div className="explainer-card">
              <h3>🌊 Le problème</h3>
              <p>
                Les berges des Grands Lacs subissent une érosion continue : la montée des
                eaux, les tempêtes et la perte de végétation menacent les propriétés,
                la qualité de l'eau et les habitats riverains. Les inspections manuelles
                sont coûteuses, ponctuelles et ne couvrent qu'une fraction du littoral.
              </p>
            </div>
            <div className="explainer-card">
              <h3>🛰️ La solution Riverside</h3>
              <p>
                <strong>Riverside</strong> automatise la surveillance des berges grâce à
                l'imagerie satellite gratuite : il détecte les zones sous-végétalisées,
                suit leur évolution dans le temps, prédit la croissance de la végétation
                et déclenche des alertes réglementaires avant que l'érosion ne devienne
                critique — le tout sans déplacement sur le terrain.
              </p>
            </div>
            <div className="explainer-card">
              <h3>⚙️ Le pipeline de bout en bout</h3>
              <p>De l'acquisition à l'action, chaque observation traverse 6 étapes :</p>
              <ol className="explainer-steps">
                <li><strong>Acquisition</strong> — recherche de scènes Sentinel-2 récentes (STAC Earth Search)</li>
                <li><strong>Dénuagement</strong> — masque SCL + composite médian temporel</li>
                <li><strong>Indices</strong> — calcul NDVI (santé végétale) et NDWI (humidité)</li>
                <li><strong>Historisation</strong> — séries temporelles archivées en base PostGIS</li>
                <li><strong>Décision</strong> — comparaison au seuil réglementaire + alertes + webhook n8n</li>
                <li><strong>Prédiction</strong> — modèle LSTM de trajectoire NDVI pour anticiper les brèches de seuil</li>
              </ol>
            </div>
            <div className="explainer-card">
              <h3>📋 Vers des rapports de conformité</h3>
              <p>
                Les observations alimentent des <strong>rapports CSR bilingues</strong> (français/anglais) :
                synthèse de conformité au seuil, tendance de la végétation, nombre de
                franchissements — et une rédaction narrative optionnelle générée par un
                LLM local (Ollama), souveraine et hors-ligne.
              </p>
            </div>
          </div>
        </section>

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
