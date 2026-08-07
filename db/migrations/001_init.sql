-- Riverside — migration 001 : schéma PostGIS initial
-- EN: initial PostGIS schema for shoreline monitoring

CREATE EXTENSION IF NOT EXISTS postgis;

-- Zones d'intérêt (berges) / Areas of interest (shorelines)
CREATE TABLE IF NOT EXISTS aoi (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    geom        GEOMETRY(Polygon, 4326) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_aoi_geom ON aoi USING GIST (geom);

-- Scènes satellite ingérées / Ingested satellite scenes
CREATE TABLE IF NOT EXISTS scenes (
    id           TEXT PRIMARY KEY,            -- STAC item id
    aoi_id       UUID NOT NULL REFERENCES aoi(id) ON DELETE CASCADE,
    acquired_at  TIMESTAMPTZ NOT NULL,
    cloud_cover  REAL NOT NULL CHECK (cloud_cover BETWEEN 0 AND 100),
    href_red     TEXT NOT NULL,
    href_nir     TEXT NOT NULL,
    href_scl     TEXT
);
CREATE INDEX IF NOT EXISTS idx_scenes_aoi_date ON scenes (aoi_id, acquired_at DESC);

-- Séries NDVI agrégées par AOI / Aggregated NDVI time series per AOI
CREATE TABLE IF NOT EXISTS ndvi_series (
    aoi_id      UUID NOT NULL REFERENCES aoi(id) ON DELETE CASCADE,
    observed_at DATE NOT NULL,
    ndvi_mean   REAL NOT NULL,
    ndvi_p10    REAL,
    ndvi_p90    REAL,
    ndwi_mean   REAL,
    PRIMARY KEY (aoi_id, observed_at)
);

-- Alertes seuils réglementaires / Regulatory threshold alerts
CREATE TABLE IF NOT EXISTS alerts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aoi_id      UUID NOT NULL REFERENCES aoi(id) ON DELETE CASCADE,
    raised_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    metric      TEXT NOT NULL,                -- ex. 'ndvi_mean'
    value       REAL NOT NULL,
    threshold   REAL NOT NULL,
    severity    TEXT NOT NULL CHECK (severity IN ('info','warning','critical')),
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_alerts_open ON alerts (aoi_id, raised_at DESC) WHERE NOT acknowledged;
