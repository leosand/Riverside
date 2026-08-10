"use client";

import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

// Bbox lac Ontario (Toronto) — zone surveillée / monitored area
const ZONE_BBOX: [number, number, number, number] = [-79.5, 43.2, -78.5, 44.0];
const CENTER: [number, number] = [-79.0, 43.6];

/** Carte MapLibre de la zone surveillée avec le rectangle AOI. */
export function NdviMap() {
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
      center: CENTER,
      zoom: 9,
    });

    // Rectangle de la zone d'intérêt (AOI surveillée)
    const [w, s, e, n] = ZONE_BBOX;
    const aoiSource = {
      type: "geojson" as const,
      data: {
        type: "Feature" as const,
        properties: {},
        geometry: {
          type: "Polygon" as const,
          coordinates: [
            [
              [w, s],
              [e, s],
              [e, n],
              [w, n],
              [w, s],
            ],
          ],
        },
      },
    };
    map.on("load", () => {
      map.addSource("aoi", aoiSource);
      map.addLayer({
        id: "aoi-fill",
        type: "fill",
        source: "aoi",
        paint: { "fill-color": "#10b981", "fill-opacity": 0.08 },
      });
      map.addLayer({
        id: "aoi-border",
        type: "line",
        source: "aoi",
        paint: {
          "line-color": "#0d9488",
          "line-width": 2,
          "line-dasharray": [3, 2],
        },
      });
      map.fitBounds(
        [
          [w, s],
          [e, n],
        ],
        { padding: 24, duration: 800 },
      );
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    return () => map.remove();
  }, []);

  return (
    <div
      ref={containerRef}
      role="application"
      aria-label="Carte des berges surveillées (lac Ontario)"
      className="ndvi-map"
    />
  );
}
