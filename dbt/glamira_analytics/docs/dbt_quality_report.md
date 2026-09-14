# dbt Data Quality and Documentation Report

Last reviewed: 2026-09-14

## 1. Scope

This report summarizes the final documentation, testing, dimensional integrity,
data-quality, and PII-protection status of the Glamira dbt analytics project.

The dbt project transforms raw BigQuery datasets through:

- staging
- core
- dimensional marts

The primary analytical fact is `fact_sales_order_detail`.

---

## 2. Project inventory

| Metric | Result |
|---|---:|
| dbt models | 12 |
| dbt sources | 3 |
| automated data tests | 110 |
| relationship tests | 6 |
| models missing descriptions | 0 |
| declared columns missing descriptions | 0 |

All declared models and columns are documented.

---

## 3. Model layers

### Staging

The staging layer standardizes source datasets while retaining source-level
attributes needed for transformation, lineage, enrichment, and data-quality
analysis.

Models include:

- `stg_checkout_success`
- `stg_products`
- `stg_geoip`

Sensitive source attributes remain available in this engineering layer but are
protected using BigQuery policy tags.

### Core

The core layer applies business transformation logic.

Key models include:

- `int_checkout_deduplicated`
- `int_sales_order_lines`

`int_checkout_deduplicated` collapses duplicate checkout tracking events using
the business grain:

`order_id + store_id + cart_hash`

`int_sales_order_lines` expands deduplicated checkout carts into product-line
records.

Its business grain is:

`checkout_instance_key + line_number`

Both grains are protected by automated dbt assertions.

### Mart

The mart layer exposes the dimensional analytical model.

Dimensions:

- `dim_customer`
- `dim_product`
- `dim_store`
- `dim_device`
- `dim_date`
- `dim_geo`

Fact:

- `fact_sales_order_detail`

The fact grain is one product line within one deduplicated successful checkout.

---

## 4. Fact reconciliation

Current production analytical baseline:

| Metric | Value |
|---|---:|
| Fact rows | 34,916 |
| Distinct fact keys | 34,916 |
| Unknown customer rows | 11,681 |
| Unknown product rows | 6,805 |
| Unknown geography rows | 17 |
| Unknown date rows | 0 |
| Unknown store rows | 0 |
| Unknown device rows | 0 |

The fact technical key and business grain are both unique.

---

## 5. Referential integrity

`fact_sales_order_detail` contains six dimensional foreign keys:

- `date_key`
- `customer_key`
- `product_key`
- `geo_key`
- `store_key`
- `device_key`

All six relationships are protected by dbt relationship tests.

Dimension surrogate keys are protected with `not_null` and `unique` tests.

Unresolved dimensional references use explicit Unknown members rather than
creating orphan foreign keys.

---

## 6. PII protection

Raw and sensitive customer attributes are allowed in controlled engineering
layers where required for transformations.

Protected attributes include:

- customer identifier
- email address
- IP address
- device identifier
- user agent
- current URL
- referrer URL

BigQuery column-level security is implemented using the
`Glamira Data Classification` taxonomy.

Current protected-column coverage:

| Layer | Tagged columns |
|---|---:|
| Staging | 8 |
| Core | 14 |
| Total | 22 |

The mart layer does not expose raw:

- customer identifiers
- email addresses
- IP addresses
- device identifiers
- user agents
- current URLs
- referrer URLs

Registered customer identifiers are represented in `dim_customer` using
SHA-256 pseudonymization through `customer_id_hash`.

Pseudonymization reduces direct exposure but must not be interpreted as full
anonymization.

---

## 7. Data-quality contracts

### Hard contracts

The following conditions must remain at zero:

- non-positive quantity
- inconsistent line amount
- unknown date
- unknown store
- unknown device

Any violation causes the corresponding dbt quality test to fail.

### Tolerated source limitations

Some source limitations are retained rather than removed.

| Metric | Baseline | Maximum accepted rate |
|---|---:|---:|
| Missing currency | 3.1075% | 5.00% |
| Missing price information | ~0.0029% | 0.01% |
| Unknown product | 19.4896% | 25.00% |
| Unknown geography | 0.0487% | 0.10% |
| Quantity greater than 10 | 0.0430% | 0.10% |

Threshold-based dbt tests detect material regressions while allowing known
source-data limitations to remain visible.

Unknown Customer is treated as an accepted business state rather than a
transformation failure.

Detailed limitations are documented in `docs/data_quality.md`.

---

## 8. Business-grain protection

The following business grains are explicitly tested:

### Deduplicated checkout

`order_id + store_id + cart_hash`

### Core sales order line

`checkout_instance_key + line_number`

### Sales fact

`checkout_instance_key + line_number`

These tests complement technical-key uniqueness tests and protect the actual
business grain from future transformation regressions.

---

## 9. Documentation validation

`dbt docs generate` successfully produces:

- `manifest.json`
- `catalog.json`
- `index.html`

Final metadata reconciliation:

| Check | Result |
|---|---:|
| Models | 12 |
| Sources | 3 |
| Tests | 110 |
| Relationship tests | 6 |
| Missing model descriptions | 0 |
| Missing declared-column descriptions | 0 |

The generated dbt documentation exposes model descriptions, column metadata,
tests, and DAG lineage.

---

## 10. Final status

The dbt transformation layer now provides:

- documented staging, core, and mart models
- explicit dimensional grains
- tested surrogate and technical keys
- tested fact-to-dimension relationships
- automated business-grain assertions
- automated hard data-quality contracts
- monitored quality thresholds
- documented known source limitations
- customer identifier pseudonymization
- BigQuery column-level PII protection
- generated dbt documentation and lineage

Status:

**PASS — dbt documentation and data-quality hardening completed.**