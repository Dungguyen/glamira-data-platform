# Product Dimension Contract

## Purpose

Define the analytical contract for the Glamira product dimension independently
from the currently available source systems.

---

## Grain

One row represents one unique Glamira product identified by `product_id`.

Primary business key:

`product_id`

---

## Proposed Schema

| Field | Type | Required | Current Source | Status |
|---|---|---:|---|---|
| product_id | STRING | Yes | Glamira event BSON | AVAILABLE |
| product_name | STRING | No | Product master required | BLOCKED |
| sku | STRING | No | Product master required | BLOCKED |
| category | STRING | No | Product master required | BLOCKED |
| description | STRING | No | Product master required | BLOCKED |
| image_url | STRING | No | Product master required | BLOCKED |
| canonical_url | STRING | No | Observed event URLs | DERIVED |
| storefront_host | STRING | No | Observed event URLs | DERIVED |
| first_seen_at | TIMESTAMP | No | Event BSON | DERIVED |
| last_seen_at | TIMESTAMP | No | Event BSON | DERIVED |

---

## Source Classification

### Authoritative

`product_id`

The product identifier is directly observed in Glamira event data.

### Derived

The following attributes may be derived from observed event data:

- canonical URL
- storefront host
- first seen timestamp
- last seen timestamp

These attributes are observational and must not be treated as authoritative
product-master attributes.

### Blocked

The following attributes require an authoritative product source:

- product name
- SKU
- category
- description
- image
- authoritative product attributes

Potential sources:

1. internal product catalog
2. official product API
3. product feed/export
4. validated project-provided product dataset

---

## Product Options

Nested event `option[]` data is not part of the `dim_product` grain.

Option observations belong to event-level analytical data.

Proposed child grain:

One row represents one observed option/value associated with one product event.

Potential fields:

- event_id
- product_id
- option_label
- option_id
- value_id
- value_label

The semantic meaning of `value_id` must not be inferred directly from URL
parameters because deterministic mapping was not established during source
profiling.

---

## Data Quality Rules

### product_id

- must not be null
- must not be empty
- must be unique in `dim_product`

### canonical_url

- must use HTTP or HTTPS when populated
- must represent an observed product-page URL
- tracking parameters must not be retained in the canonical representation

### timestamps

`first_seen_at <= last_seen_at`

---

## Known Source Dependency

The existing event BSON is sufficient for product identity and behavioral
analytics but is not sufficient to construct an authoritative product master.

Automated crawling from the current GCP runtime is unavailable because the
source returns HTTP 403.

Therefore missing product-master attributes remain explicitly nullable until
an authorized structured product source becomes available.

---

## Decision

Proceed with a minimal product dimension based on observed event data.

Do not fabricate missing product-master attributes.

Enrich the dimension later when an authoritative source becomes available.