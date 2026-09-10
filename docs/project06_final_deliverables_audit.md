# Project 06 — Data Pipeline & Storage Final Audit

## Status

**COMPLETED**

Project 06 requirements have been implemented and validated end-to-end.

---

## 1. Raw Events Pipeline

### Source

- MongoDB database: `glamira`
- MongoDB collection: `summary`
- Source records: **41,432,473**

### Export

- Extraction strategy: batch streaming from MongoDB
- Pagination strategy: `_id > last_id`
- Chunk size: 250,000 records
- Total chunks: **166**
- Final chunk: **182,473 records**
- Format: BSON → MongoDB Extended JSON → JSONL.GZ
- Resume state and manifest implemented
- SHA256/checkpoint metadata implemented

### GCS

Path:

`gs://glamira-raw-data-506706/staging/events/incoming/full_20260909_v1/`

Validation:

- GCS objects: **166**
- Exported records: **41,432,473**

### BigQuery

Table:

`glamira-pipeline-506706.raw.events`

Validation:

- Row count: **41,432,473**
- Distinct event_id: **41,432,473**
- Duplicate event_id: **0**
- Distinct source chunks: **166**

Required lineage fields:

- null event_id: 0
- null source_database: 0
- null source_collection: 0
- null ingestion_run_id: 0
- null source_chunk: 0
- null payload: 0
- null event_type: 0
- null event_timestamp_raw: 0

### Schema Drift Validation

`option`:

- ARRAY: **22,208,495**
- OBJECT: **12,092,054**
- Missing/null: **7,131,924**

`utm_source` observed JSON types:

- BOOLEAN: **10,856,180**
- STRING: **88,179**
- explicit JSON NULL: **68**

The Raw layer preserves source schema drift using a stable metadata envelope and a BigQuery JSON payload. Schema normalization is deferred to downstream transformation layers.

---

## 2. GeoIP Pipeline

Implementation:

- Geolocation provider: MaxMind GeoLite2 City
- Senior requirement reference: IP2Location
- GeoLite2 is used as the project implementation alternative.

Source artifact:

`ip_geolocation.csv`

BigQuery table:

`glamira-pipeline-506706.raw.geoip`

Validation:

- Source rows: **3,239,628**
- BigQuery rows: **3,239,628**
- Distinct IP addresses: **3,239,628**

Coverage:

- Valid IPs: 3,239,627
- Invalid IPs: 1
- Eligible public IPs: 3,239,321
- Lookup found: 3,238,973
- Country found: 3,238,913
- Region found: 2,879,398
- City found: 2,766,005

---

## 3. Product Pipeline

Source product universe:

- Total products: **19,558**
- Successfully enriched: **18,648**
- Not enriched: **910**

Project scope:

Only successfully enriched products are loaded into BigQuery.

Canonical source artifact:

`dim_product_crawl_success.csv`

BigQuery table:

`glamira-pipeline-506706.raw.products`

Validation:

- BigQuery rows: **18,648**
- Distinct product_id: **18,648**
- product_master_status = ENRICHED: **18,648**
- Empty product_id: **0**

The 910 NOT_ENRICHED products are excluded as an accepted project limitation.

---

## 4. Automation Architecture

Events:

MongoDB
→ Python batch exporter
→ JSONL.GZ
→ Google Cloud Storage
→ Eventarc
→ Cloud Function Gen 2
→ BigQuery `raw.events`

Reference data:

GeoIP / Product CSV
→ CSV.GZ
→ Google Cloud Storage
→ Eventarc
→ Cloud Function Gen 2
→ BigQuery `raw.geoip` / `raw.products`

Cloud Functions:

- `glamira-gcs-bq-loader`
- `glamira-gcs-ref-loader`

Region:

`asia-southeast1`

---

## 5. Senior Requirements Audit

| Requirement | Status |
|---|---|
| Connect to MongoDB / VM | PASS |
| Extract data in batches | PASS |
| Convert to appropriate format | PASS |
| Upload full data to GCS | PASS |
| Raw 41M event dataset | PASS |
| GeoIP dataset | PASS |
| Product dataset | PASS |
| Error handling | PASS |
| Logging | PASS |
| Sample testing | PASS |
| BigQuery raw dataset | PASS |
| Explicit table schemas | PASS |
| GCS → BigQuery loading | PASS |
| Automated Cloud Function trigger | PASS |
| End-to-end testing | PASS |
| NULL profiling | PASS |
| Distinct-value profiling | PASS |
| Data-type/schema-drift profiling | PASS |
| GitHub repository | PASS |

---

## Final Decision

**PROJECT 06 — DATA PIPELINE & STORAGE: PASS / COMPLETED**

All required pipeline components have been implemented and validated. Accepted limitations are documented for GeoIP provider substitution and unsuccessfully enriched products.