import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./dashboard.css";

// SEO/AEO : métadonnées dynamiques FR-CA / dynamic FR-CA metadata
export const metadata: Metadata = {
  title: {
    default: "Riverside — Surveillance des berges",
    template: "%s | Riverside",
  },
  description:
    "Surveillance automatisée des berges par imagerie satellite Sentinel-2 : NDVI, alertes réglementaires CSR et prédiction de végétation. Automated shoreline monitoring.",
  openGraph: {
    title: "Riverside — Surveillance des berges",
    description: "NDVI satellite, alertes CSR, prédiction végétation.",
    locale: "fr_CA",
    type: "website",
  },
  robots: { index: false, follow: false }, // outil interne / internal tool
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fr-CA">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif" }}>
        {/* A11y : lien d'évitement / skip link */}
        <a
          href="#contenu"
          style={{
            position: "absolute",
            left: "-9999px",
            top: 0,
            background: "#0b7285",
            color: "#fff",
            padding: "0.5rem 1rem",
            zIndex: 100,
          }}
        >
          Aller au contenu
        </a>
        <main id="contenu">{children}</main>
      </body>
    </html>
  );
}
