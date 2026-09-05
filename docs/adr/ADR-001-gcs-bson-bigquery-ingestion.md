# ADR-001: GCS BSON to BigQuery Ingestion Architecture

## Status

Proposed

## Context

The Glamira source dataset is stored in Google Cloud Storage as:

summary.bson

Current source size:

33,530,129,089 bytes (~33.5 GB)

The source contains polymorphic event-oriented BSON documents.

Local discovery identified:

- 21 event types in the 50K sample
- event-specific payload schemas
- polymorphic `option`
- nested `cart_products`
- inconsistent BSON types
- locale-dependent price representation
- string boolean values
- identifier type inconsistencies

The target architecture provided for the project is:

GCS
→ Cloud Function
→ BigQuery RAW
→ dbt
→ BigQuery Analytical
→ Looker

BigQuery does not directly ingest BSON.

Therefore an intermediate conversion step is required.

---

## Decision

Use the following ingestion architecture:

GCS RAW BSON
→ Event trigger
→ Cloud Function
→ Cloud Run Job
→ GCS staging NDJSON
→ BigQuery RAW
→ dbt
→ BigQuery Analytical
→ Looker

Cloud Function will be responsible for:

- receiving the GCS finalized-object event
- validating source metadata    
- starting the batch processing job

Cloud Function will NOT parse the full 33.5 GB BSON file.

Cloud Run Job will be responsible for:

- reading BSON from GCS
- decoding documents
- creating a minimal event envelope
- preserving the raw payload
- writing chunked NDJSON output
- writing processing metrics
- failing explicitly on unrecoverable parsing errors

BigQuery RAW will contain one row per source event.

---

## BigQuery RAW strategycan

Initial candidate schema:

- event_id STRING
- event_type STRING
- api_version STRING
- event_timestamp_raw INT64
- source_object STRING
- source_generation STRING
- ingested_at TIMESTAMP
- payload JSON

The purpose of RAW is source fidelity and queryability.

Business normalization belongs in dbt staging/intermediate models.

---

## Why not direct Cloud Function processing?

The source object is approximately 33.5 GB.

The workload requires:

- full BSON scanning
- nested BSON decoding
- schema variability handling
- chunked output generation
- retries
- potentially long execution time

A lightweight event function is better used as orchestration than as the primary batch-processing engine.

---

## Why Cloud Run Job?

Reasons:

- containerized runtime
- suitable for long-running batch workloads
- easier Python dependency management
- straightforward BSON parsing
- configurable CPU and memory
- retries
- task timeout suitable for batch processing
- easier local reproduction than distributed frameworks

---

## Why not Dataflow initially?

Dataflow remains a valid alternative.

It may be preferable if the system later requires:

- very high throughput
- many source files
- distributed processing
- streaming ingestion
- complex event-time processing

For the current single-file POC, Dataflow adds unnecessary operational complexity.

---

## Why not Dataproc / Spark initially?

Spark is suitable for large-scale distributed transformations.

However, for the current 33.5 GB single-file POC:

- cluster setup adds complexity
- startup and infrastructure overhead are higher
- the transformation is primarily BSON decode + envelope creation

Spark should be reconsidered if volume, file count, or transformation complexity increases significantly.

---

## Why NDJSON staging?

BigQuery supports loading newline-delimited JSON from Cloud Storage.

NDJSON provides:

- direct BigQuery compatibility
- easy inspection
- easy chunking
- retryable intermediate artifacts
- compatibility with BigQuery JSON fields

Staging output should be chunked rather than written as one very large file.

---

## Why not Parquet for RAW?

Parquet requires a more explicit schema.

The source contains polymorphic and event-specific structures.

Premature normalization into Parquet may:

- lose source fidelity
- introduce coercion errors
- make schema evolution harder to observe

Parquet may be more appropriate for cleaned/staging or analytical layers after schema normalization.

---

## Idempotency

Each source object version is identified by:

source_object
+
source_generation

Before processing, the ingestion system must check whether the same source object generation has already completed successfully.

Recommended control table:

control.ingestion_runs

Fields:

- source_object
- source_generation
- status
- started_at
- completed_at
- row_count
- error_count
- job_id

If an object generation is already marked SUCCESS, the pipeline should not process it again unless an explicit reprocessing mode is requested.

---

## Failure handling

The pipeline should distinguish:

- source download/read failure
- BSON decode failure
- malformed document
- staging-write failure
- BigQuery load failure

Failed records should not silently disappear.

The POC should evaluate a quarantine/dead-letter strategy.

---

## Consequences

Benefits:

- raw source remains immutable
- BSON-specific processing is isolated from BigQuery
- event payload is preserved
- retries are safer
- debugging is easier
- ingestion can be reprocessed
- BigQuery receives a stable envelope

Costs:

- introduces GCS staging
- introduces Cloud Run Job
- requires container build/deployment
- requires ingestion metadata tracking

---

## Alternatives

1. Cloud Function → BigQuery directly
2. Cloud Function → Dataflow → BigQuery
3. GCS → Dataproc/Spark → BigQuery
4. GCS → Cloud Run Job → BigQuery

The recommended POC uses Cloud Function + Cloud Run Job.

---

## Validation required

This ADR remains Proposed until DE-06 POC validates:

- correctness
- runtime
- memory usage
- output size
- BigQuery compatibility
- retry behavior
- idempotency
- cost