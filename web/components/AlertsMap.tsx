"use client";

import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

// Fond OSM libre / free OSM basemap — bassin des Grands Lacs
const GREAT_LAKES: [number, number] = [-82.5, 45.0];

export function AlertsMap() {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (containerRef.current === null) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      center: GREAT_LAKES,
      zoom: 5,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    // A11y clavier / keyboard navigation activée par défaut dans MapLibre
    return () => map.remove();
  }, []);

  return (
    <div
      ref={containerRef}
      role="application"
      aria-label="Carte des berges surveillées"
      style={{ width: "100%", height: "70vh", borderRadius: "0.5rem" }}
    />
  );
}
