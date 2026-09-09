# GCS to BigQuery Raw Ingestion Design

## Objective

Prepare Glamira MongoDB events for ingestion from GCS into BigQuery
without losing source-event grain or heterogeneous event payloads.

## Source

- MongoDB database: `glamira`
- Collection: `summary`
- Validated documents: 41,432,473

## Transport Format

`JSONL.GZ`

One source MongoDB document becomes one JSONL record.

## Raw Record Contract

| Field | Type | Description |
|---|---|---|
| event_id | STRING | MongoDB `_id` converted to string |
| event_type | STRING | Source `collection` |
| event_timestamp_raw | INTEGER | Original `time_stamp` |
| source_database | STRING | Source database |
| source_collection | STRING | Source collection |
| payload | JSON | Original event payload in JSON-compatible representation |

## Why JSONL.GZ

JSONL preserves nested event structures and is suitable for streaming.

Gzip reduces GCS storage and network transfer.

CSV is not selected because the source contains nested arrays and
objects.

## Why a JSON payload

The source contains heterogeneous and mixed-type fields.

Examples:

- `option`: object / array / missing
- `utm_source`: string / boolean
- `utm_medium`: string / boolean
- event-specific nested cart/recommendation structures

Keeping the heterogeneous attributes inside `payload` prevents the Raw
BigQuery schema from requiring a globally uniform event schema.

## Grain

One Raw BigQuery row represents one source event.

Nested arrays are not exploded during ingestion.

## Reconciliation

For the full run:

source_documents
=
exported_documents
+
rejected_documents

Expected source count:

41,432,473