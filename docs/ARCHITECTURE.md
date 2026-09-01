# Riverside — Architecture Overview

**Repository:** [leosand/Riverside](https://github.com/leosand/Riverside)  
**Purpose:** MVP for automated riverbank monitoring using Sentinel-2 imagery, AI cloud removal, NDVI, vegetation prediction, and regulatory-threshold alerts.

---

## High-level components

1. **Data ingestion**
   - Pulls Sentinel-2 imagery for defined areas of interest (AOIs) and time ranges.
   - Stores raw scenes and metadata in a structured directory or object storage.

2. **Preprocessing & cloud removal**
   - Applies cloud masking and cloud-removal models (e.g., DSen2-CR or similar).
   - Produces cloud-reduced reflectance composites ready for index computation.

3. **Index computation & feature extraction**
   - Computes NDVI and potentially other vegetation/water indices.
   - Extracts time-series features per AOI (e.g., mean NDVI, trends, anomalies).

4. **Predictive modeling**
   - Uses a vegetation or erosion-risk model to predict bank condition over time.
   - Outputs risk scores or change indicators per AOI.

5. **Alert engine**
   - Compares predicted/observed indicators against regulatory thresholds (e.g., CSR).
   - Generates alerts when thresholds are exceeded, with timestamps and AOI references.

6. **Persistence**
   - Stores processed data, model outputs, and alerts in a database (`db/`).
   - Maintains run metadata and processing logs for traceability.

7. **Web UI / API**
   - Provides a simple interface (`web/`) to visualize AOIs, time series, and alerts.
   - Optionally exposes an API for programmatic access.

8. **Orchestration**
   - Scheduled or on-demand pipelines orchestrated via scripts or a workflow engine.
   - Containerized execution via Docker Compose for reproducibility.

---

## Data flow (text diagram)

```text
[Sentinel-2 Source]
       ↓
[Ingestion Module] → raw scenes + metadata
       ↓
[Preprocessing & Cloud Removal] → cloud-reduced composites
       ↓
[Index Computation (NDVI, etc.)] → feature tables
       ↓
[Predictive Model] → risk scores / change indicators
       ↓
[Alert Engine] → alerts (threshold breaches)
       ↓
[Database] ←→ [Web UI / API]
```

---

## Deployment topology

- **Local or single-node deployment** using Docker Compose:
  - `app` service: Python processing pipeline.
  - `db` service: PostgreSQL or similar.
  - `web` service: lightweight UI or API.
- **Scheduled runs** via cron or a simple scheduler inside the container or host.

---

## Failure modes & mitigations

- **Data source outage** (Sentinel delayed/unavailable):
  - Skip run, log warning, retry on next schedule.
- **Cloud removal failure** (model error, bad input):
  - Mark scene as invalid, do not propagate to downstream steps.
- **Model drift** (predictions degrade over time):
  - Periodic re-validation against ground truth; retrain or recalibrate as needed.
- **Alert fatigue** (too many false positives):
  - Tune thresholds, add hysteresis, require multi-scene confirmation.

---

## Extension points

- Add more indices (EVI, SAVI, water indices) and multi-sensor fusion (e.g., Landsat).
- Introduce a proper workflow orchestrator (e.g., Prefect, Airflow) for complex pipelines.
- Add role-based access control and multi-tenant support if exposing as a service.
- Integrate with notification channels (email, SMS, webhooks) for alert delivery.
