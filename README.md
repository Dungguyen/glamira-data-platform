# Glamira Data Platform

An end-to-end Data Engineering portfolio project that transforms raw Glamira checkout/event data into a governed BigQuery dimensional model and a business-facing Looker Studio dashboard.

The project covers:

**raw data discovery → ingestion → profiling → dbt transformation → dimensional modeling → data quality → PII protection → BI serving layer → Looker Studio**

> This README is designed so another engineer can understand the system, validate it, and reproduce the analytics workflow in their own Google Cloud environment.

---

## 1. Project Goals

The project answers four engineering questions:

1. How can large semi-structured Glamira event data be ingested and profiled safely?
2. How should successful checkout events be deduplicated and transformed into an analytics-ready grain?
3. How can customer, product, store, device, geography, and date dimensions be modeled without dropping unresolved source records?
4. How can the resulting mart be exposed to BI while protecting PII and preserving trustworthy KPI definitions?

Primary analytical fact:

`fact_sales_order_detail`

Grain:

> **One product line within one deduplicated successful checkout.**

Final BI-facing object:

`bi_sales_order_detail`

---

## 2. Architecture

```text
Raw BSON / source datasets
        |
        v
Google Cloud Storage
        |
        v
BigQuery raw datasets
        |
        v
dbt Staging Layer
dbt_dev_staging
        |
        v
dbt Core Layer
dbt_dev_core
        |
        v
Dimensional Mart
dbt_dev_mart
        |
        +--> dim_customer
        +--> dim_product
        +--> dim_store
        +--> dim_device
        +--> dim_date
        +--> dim_geo
        +--> fact_sales_order_detail
        |
        v
bi_sales_order_detail
        |
        v
Looker Studio
```

The BI layer reads only the controlled mart/BI-serving layer. It does not query raw, staging, or core datasets directly.

---

## 3. Technology Stack

| Area | Technology |
|---|---|
| Development OS | Windows |
| Shell | PowerShell |
| Editor | Visual Studio Code |
| Python environment | `uv` |
| Python | 3.12.13 |
| Local BSON exploration | MongoDB 8 |
| MongoDB tools | Database Tools 100.18.0 |
| Cloud | Google Cloud Platform |
| Storage | Google Cloud Storage |
| Warehouse | BigQuery |
| Transformation | dbt Core 1.12.4 |
| BigQuery adapter | dbt-bigquery 1.12.0 |
| BI | Looker Studio |
| Version control | Git / GitHub |

---

## 4. Repository Layout

Simplified structure:

```text
glamira-data-platform/
|
|-- data/
|   `-- raw/
|       `-- summary.bson              # local only, ignored by Git
|
|-- dbt/
|   `-- glamira_analytics/
|       |-- models/
|       |   |-- staging/
|       |   |-- core/
|       |   `-- marts/
|       |       |-- dimensions/
|       |       |-- facts/
|       |       `-- bi/
|       |-- tests/
|       |   |-- mart/
|       |   `-- quality/
|       |-- docs/
|       |   |-- data_quality.md
|       |   |-- dbt_quality_report.md
|       |   |-- bi_dashboard_spec.md
|       |   |-- bi_dashboard_handoff.md
|       |   `-- images/
|       |       `-- bi/
|       |-- scripts/
|       |   `-- Invoke-BqRest.ps1
|       |-- dbt_project.yml
|       `-- ...
|
|-- docs/                            # platform / ingestion / discovery docs
|-- pyproject.toml
|-- uv.lock
|-- .python-version
|-- .gitignore
`-- README.md
```

---

## 5. Data Sources

### Event BSON

Original object:

```text
gs://glamira-raw-data-506706/summary.bson
```

Original reported size:

```text
~33.5 GB
```

Local development path:

```text
D:\glamira-data-platform\data\raw\summary.bson
```

The BSON file is intentionally ignored by Git.

### Product master

```text
18,648 product rows
```

### GeoIP

```text
3,239,628 GeoIP rows
```

The project used MaxMind GeoLite2 for IP geolocation enrichment.

### Reproducibility note

The raw Glamira data is not bundled in this repository.

To reproduce the project exactly, you need access to the same source datasets. If you use equivalent data instead, adapt the source definitions while preserving the documented grains and contracts.

---

## 6. Important Validation Baselines

These numbers are useful when reproducing the original dataset.

### Raw / checkout processing

```text
Raw event rows                         41,432,473
Raw checkout_success events               26,079
Deduplicated checkout instances            26,045
Production checkout instances              25,962
```

### Final fact

```text
fact_sales_order_detail rows                34,916
Distinct fact keys                          34,916
Successful production checkouts             25,962
Raw units                                   45,573
Distinct source products                     5,826
```

### Known dimensional gaps

```text
Unknown customer lines                      11,681
Unknown product lines                        6,805
Unknown product IDs                            198
Unknown geography lines                         17
Unknown date lines                                0
Unknown store lines                               0
Unknown device lines                              0
```

---

## 7. Prerequisites

Install:

- Git
- Visual Studio Code
- Python 3.12
- `uv`
- Google Cloud CLI
- dbt Core + dbt-bigquery
- access to a Google Cloud project with BigQuery enabled
- optional: MongoDB + MongoDB Database Tools for local BSON inspection
- optional: Looker Studio access

Authenticate:

```powershell
gcloud auth login
gcloud auth application-default login
gcloud auth list
```

---

## 8. Clone and Prepare

```powershell
git clone <YOUR_REPOSITORY_URL>
cd glamira-data-platform
```

Prepare Python:

```powershell
uv sync
```

Install dbt if needed:

```powershell
uv tool install --python 3.12 "dbt-core==1.12.4" --with "dbt-bigquery==1.12.0"
```

Validate:

```powershell
dbt --version
```

---

## 9. Optional Local BSON Exploration

Useful tools:

```powershell
bsondump.exe --version
mongorestore.exe --version
```

Example:

```powershell
bsondump.exe --pretty D:\glamira-data-platform\data\raw\summary.bson
```

Observed source fields include:

```text
_id
time_stamp
ip
user_agent
resolution
user_id_db
device_id
api_version
store_id
local_time
current_url
referrer_url
email_address
collection
product_id
collect_id
cat_id
option
```

The `option` field can appear as an object or an array of objects, so the project favors schema-on-read instead of forcing a rigid schema at ingestion time.

---

## 10. Google Cloud Setup

The original deployment used:

```text
Project ID: glamira-pipeline-506706
Region:     asia-southeast1
```

For reproduction, use your own values:

```text
<YOUR_GCP_PROJECT_ID>
<YOUR_BUCKET_NAME>
<YOUR_REGION>
```

Do not copy project-specific policy-tag resource IDs into another GCP project.

---

## 11. dbt Setup

Run dbt from:

```powershell
cd D:\glamira-data-platform\dbt\glamira_analytics
```

Example `$HOME\.dbt\profiles.yml`:

```yaml
glamira_analytics:
  target: dev

  outputs:
    dev:
      type: bigquery
      method: oauth
      project: <YOUR_GCP_PROJECT_ID>
      dataset: dbt_dev
      location: asia-southeast1
      threads: 4
```

Validate:

```powershell
dbt debug
dbt parse --no-partial-parse
```

---

## 12. dbt Layers

### Staging — `dbt_dev_staging`

```text
stg_checkout_success
stg_products
stg_geoip
```

Responsibilities:

- standardize names and types;
- normalize environment labels;
- preserve source fields required downstream;
- prepare product and geography enrichment;
- retain controlled source PII where transformation requires it.

### Core — `dbt_dev_core`

```text
int_checkout_deduplicated
int_sales_order_lines
```

Checkout business grain:

```text
order_id + store_id + cart_hash
```

Sales-line grain:

```text
checkout_instance_key + line_number
```

### Mart — `dbt_dev_mart`

Dimensions:

```text
dim_customer
dim_product
dim_store
dim_device
dim_date
dim_geo
```

Fact:

```text
fact_sales_order_detail
```

BI serving view:

```text
bi_sales_order_detail
```

---

## 13. Build the Project

From the dbt project directory:

```powershell
dbt run
dbt test
```

Or:

```powershell
dbt build
```

Generate docs:

```powershell
dbt docs generate
dbt docs serve --port 8080
```

`target/` contains generated artifacts and should normally remain ignored by Git.

---

## 14. Validate the Final Fact

```sql
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT sales_order_detail_key) AS distinct_fact_keys,
    COUNT(DISTINCT checkout_instance_key) AS successful_checkouts,
    SUM(quantity) AS raw_units,
    COUNT(DISTINCT product_id) AS distinct_products,
    COUNTIF(customer_key = 0) AS unknown_customer_lines,
    COUNTIF(product_key = 0) AS unknown_product_lines,
    COUNTIF(geo_key = 0) AS unknown_geo_lines
FROM `<YOUR_GCP_PROJECT_ID>.dbt_dev_mart.fact_sales_order_detail`;
```

Original expected result:

```text
row_count               34,916
distinct_fact_keys      34,916
successful_checkouts    25,962
raw_units               45,573
distinct_products        5,826
unknown_customer_lines  11,681
unknown_product_lines    6,805
unknown_geo_lines           17
```

---

## 15. Data Quality Strategy

The project distinguishes:

```text
Transformation failure
!=
Known source limitation
```

### Hard contracts

Must remain zero:

- non-positive quantity;
- inconsistent line amount;
- unknown date;
- unknown store;
- unknown device.

### Tolerated / monitored limitations

| Metric | Baseline | Maximum accepted rate |
|---|---:|---:|
| Missing currency | 3.1075% | 5.00% |
| Missing price information | ~0.0029% | 0.01% |
| Unknown product | 19.4896% | 25.00% |
| Unknown geography | 0.0487% | 0.10% |
| Quantity greater than 10 | 0.0430% | 0.10% |

Quality tests are under:

```text
tests/quality/
```

Known limitations are documented in:

```text
docs/data_quality.md
```

---

## 16. Quantity Anomaly

A known source row contains:

```text
quantity = 9,999
```

On `2020-04-09`, that one row raises daily units from about `504` to `10,503`.

The row is retained because no authoritative business rule proves it is invalid.

Therefore:

- Raw Units remain source-faithful;
- high quantities are explicitly flagged;
- BI must not silently remove these rows;
- adjusted metrics require a documented business rule.

---

## 17. Multi-Currency Policy

The fact stores:

```text
line_amount_local
currency_symbol
```

The dataset contains multiple currencies.

This is invalid:

```text
SUM(line_amount_local) across all currencies
```

The project supports `Sales Amount Local` only within a consistent:

```text
Store + Currency
```

context.

A global normalized revenue KPI requires:

- ISO currency codes;
- exchange-rate data;
- conversion dates;
- target reporting currency;
- reproducible FX logic.

---

## 18. PII Protection

Protected source attributes include:

```text
customer_id
email_address
ip_address
device_id
user_agent
current_url
referrer_url
```

Original taxonomy:

```text
Glamira Data Classification
```

Policy classes:

```text
Direct Identifier
Customer Identifier
Device Identifier
Network Identifier
Quasi Identifier
Sensitive URL
```

Original policy-tag coverage:

```text
Staging:  8 tagged columns
Core:    14 tagged columns
Total:   22 tagged columns
```

When reproducing:

1. create your own taxonomy in the same region as the BigQuery datasets;
2. create equivalent policy tags;
3. replace policy-tag resource IDs in dbt YAML;
4. grant Fine-Grained Reader only to principals that need raw PII;
5. rebuild dbt models so column metadata/tags are persisted.

### Mart protection

`dim_customer` uses:

```text
customer_id_hash
```

for pseudonymization.

The BI view intentionally excludes even that pseudonym.

The BI surface does not expose:

```text
customer_id
customer_id_hash
email_address
ip_address
device_id
user_agent
current_url
referrer_url
```

---

## 19. BI Serving Layer

Looker Studio should use:

```text
dbt_dev_mart.bi_sales_order_detail
```

instead of blending the fact and six dimensions inside Looker Studio.

Benefits:

- semantic joins stay version-controlled in dbt;
- easier testing;
- no inconsistent dashboard blends;
- lower fan-out risk;
- centralized security;
- simpler dashboard development.

Validate:

```sql
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT sales_order_detail_key) AS distinct_keys,
    COUNT(DISTINCT checkout_instance_key) AS successful_checkouts,
    SUM(quantity) AS raw_units,
    COUNT(DISTINCT product_id) AS distinct_products,
    COUNTIF(is_unknown_customer) AS unknown_customer_lines,
    COUNTIF(is_unknown_product) AS unknown_product_lines,
    COUNTIF(is_unknown_geo) AS unknown_geo_lines,
    COUNTIF(is_high_quantity) AS high_quantity_lines,
    COUNTIF(is_missing_currency) AS missing_currency_lines
FROM `<YOUR_GCP_PROJECT_ID>.dbt_dev_mart.bi_sales_order_detail`;
```

Original expected result:

```text
row_count               34,916
distinct_keys           34,916
successful_checkouts    25,962
raw_units               45,573
distinct_products        5,826
unknown_customer_lines  11,681
unknown_product_lines    6,805
unknown_geo_lines           17
high_quantity_lines         15
missing_currency_lines   1,085
```

---

## 20. Looker Studio Dashboard

Connect Looker Studio to:

```text
Project: <YOUR_GCP_PROJECT_ID>
Dataset: dbt_dev_mart
Object:  bi_sales_order_detail
```

The final dashboard has four pages.

### Page 1 — Executive / Sales Overview

KPIs:

```text
Product Lines
Successful Checkouts
Raw Units
Distinct Products
High Quantity Lines
Missing Currency Lines
```

Visuals:

```text
Top Stores by Successful Checkouts
Successful Checkouts Over Time
Sales Amount by Store & Currency
```

### Page 2 — Product Performance

KPIs:

```text
Distinct Products
High Quantity Lines
Unknown Product Lines
Product Coverage
```

Visuals:

```text
Top Products by Successful Checkouts
Product Master Coverage
Product Detail
```

Use:

```text
product_id = product identity
product_name/category_name = enrichment only
```

### Page 3 — Customer Analytics

Baseline:

```text
Registered Customers        15,087
Registered Checkouts        16,799
Unknown Customer Checkouts   9,163
Unknown Customer Lines      11,681
```

Customer reporting is aggregate-only.

### Page 4 — Geography & Device Analysis

Geography baseline:

```text
Countries                    98
Successful Checkouts      25,962
Product Lines             34,916
Unknown Geography Lines       17
```

Device baseline:

```text
Mobile Checkouts      13,765
Desktop Checkouts     11,785
Tablet Checkouts         411
Bot Checkouts               1
```

---

## 21. BI Metric Contracts

| Field | Correct aggregation |
|---|---|
| `checkout_instance_key` | `COUNT DISTINCT` |
| `product_id` | `COUNT DISTINCT` for distinct-product KPIs |
| `quantity` | `SUM` |
| `line_amount_local` | `SUM` only in consistent currency context |
| `sales_order_detail_key` | identifier; never `SUM` |
| surrogate keys | identifiers; never `SUM` |

Date controls must use:

```text
checkout_date
```

not:

```text
date_key
```

---

## 22. Product Coverage

```text
Distinct source products    5,826
Matched product IDs         5,628
Unknown product IDs           198

Matched product lines      28,111
Unknown product lines       6,805

Product coverage           ~80.51%
Unknown line rate           19.4896%
```

Unknown products are mapped to an explicit Unknown member instead of being dropped.

---

## 23. Customer Modeling

Original customer dimension:

```text
15,100 rows total
15,099 registered customer hashes
1 Unknown Customer
```

Anonymous/unresolved customers are accepted business states, not automatically transformation failures.

---

## 24. Geography Modeling

Dimension grain:

```text
country + region + city
```

Original dimension:

```text
5,944 rows total
5,943 known
1 Unknown Geography
```

Production GeoIP outcomes included:

```text
FOUND                 25,951
NON_GLOBAL                10
ADDRESS_NOT_FOUND          1
```

---

## 25. Device Modeling

Grain:

```text
device_type + resolution
```

Device types:

```text
MOBILE
DESKTOP
TABLET
BOT
```

`is_bot` is an attribute rather than part of the surrogate-key identity.

---

## 26. Date Modeling

Production date range:

```text
2020-04-01 through 2020-06-04
```

Active dates:

```text
65
```

`date_key` uses `YYYYMMDD`, with `0` reserved for Unknown Date.

---

## 27. Store Modeling

`store_id` is the authoritative natural key.

`store_domain` is descriptive only and is not guaranteed unique.

Dashboard controls therefore use:

```text
<store_id> | <store_domain>
```

---

## 28. Tests

The project contains:

- uniqueness tests;
- not-null tests;
- accepted-value tests;
- fact-to-dimension relationship tests;
- business-grain singular tests;
- PII exposure tests;
- customer-hash protection tests;
- hard data-quality tests;
- tolerated quality-threshold tests.

Explicit business grains tested:

```text
int_checkout_deduplicated
= order_id + store_id + cart_hash

int_sales_order_lines
= checkout_instance_key + line_number

fact_sales_order_detail
= checkout_instance_key + line_number
```

Run:

```powershell
dbt test
```

Acceptance is based on all current tests passing, not on a fixed historical test count.

---

## 29. Documentation

dbt/BI docs:

```text
dbt/glamira_analytics/docs/data_quality.md
dbt/glamira_analytics/docs/dbt_quality_report.md
dbt/glamira_analytics/docs/bi_dashboard_spec.md
dbt/glamira_analytics/docs/bi_dashboard_handoff.md
```

Platform-level docs remain under:

```text
docs/
```

---

## 30. BigQuery REST Helper

During development, the local `bq` CLI had a Windows networking issue.

Helper:

```text
dbt/glamira_analytics/scripts/Invoke-BqRest.ps1
```

Load it:

```powershell
. .\scripts\Invoke-BqRest.ps1
```

Example:

```powershell
$sql = @'
SELECT COUNT(*) AS row_count
FROM `<YOUR_GCP_PROJECT_ID>.dbt_dev_mart.fact_sales_order_detail`
'@

Invoke-BqRest -Query $sql | Format-List
```

This helper is optional if `bq` works normally on your machine.

---

## 31. Troubleshooting

### No `dbt_project.yml` found

Run dbt from:

```powershell
cd D:\glamira-data-platform\dbt\glamira_analytics
```

Or pass:

```powershell
dbt parse --project-dir .\dbt\glamira_analytics --no-partial-parse
```

### Policy-tag access denied

Grant the intended user/service account Fine-Grained Reader access on the relevant policy tags. Do not remove policy tags merely to make dbt run.

### Looker Studio integer overflow

Never use:

```text
SUM(checkout_instance_key)
```

Use:

```text
COUNT DISTINCT(checkout_instance_key)
```

### Google Maps does not accept `country_name`

Set the Looker Studio data-source field type to:

```text
Geo -> Country
```

### KPIs are unexpectedly small

Check:

- Store filter;
- Currency filter;
- Date filter;
- chart selection;
- cross-filtering.

Reset controls before comparing with project baselines.

---

## 32. Reproduction Checklist

```text
[ ] Raw/source data available
[ ] BigQuery raw tables loaded
[ ] dbt connection succeeds
[ ] staging builds
[ ] core builds
[ ] dimensional mart builds
[ ] BI serving view builds
[ ] all dbt tests pass
[ ] fact rows = 34,916 for the original dataset
[ ] distinct fact keys = fact rows
[ ] successful checkouts = 25,962
[ ] raw units = 45,573
[ ] distinct products = 5,826
[ ] policy tags protect sensitive staging/core columns
[ ] BI view contains no prohibited PII
[ ] Looker Studio reads only bi_sales_order_detail
[ ] four dashboard pages exist
[ ] dashboard KPIs reconcile to BigQuery
[ ] currencies are not globally summed
[ ] known data-quality limitations remain visible
```

---

## 33. Recommended Execution Order

```text
1. Read discovery / ingestion documentation
2. Obtain or prepare source datasets
3. Configure GCP and authentication
4. Load raw data into BigQuery
5. Configure dbt profiles.yml
6. Build staging
7. Build core
8. Build marts
9. Run dbt tests
10. Configure policy tags and permissions
11. Build BI-serving view
12. Reconcile BI view against fact
13. Connect Looker Studio
14. Build the four dashboard pages
15. Reconcile dashboard KPIs
16. Generate dbt docs
```

Transformation workflow:

```powershell
cd D:\glamira-data-platform\dbt\glamira_analytics

dbt parse --no-partial-parse
dbt run
dbt test
dbt docs generate
```

---

## 34. Engineering Decisions

Key decisions:

- preserve raw anomalies instead of silently deleting them;
- use explicit Unknown members instead of orphan foreign keys;
- test technical keys and business grains separately;
- treat anonymous customers as a valid state;
- retain unmatched product IDs for traceability;
- retain PII in controlled engineering layers only when necessary;
- pseudonymize registered customer IDs in the mart;
- expose an even safer BI-serving view;
- keep semantic joins in dbt instead of Looker Studio blends;
- prohibit global revenue aggregation across currencies;
- expose data-quality limitations to dashboard users.

---

## 35. Future Improvements

Potential next steps:

- ISO currency codes;
- historical FX rates and normalized reporting currency;
- business investigation of the `quantity = 9999` anomaly;
- improved product-master coverage for the 198 unresolved IDs;
- CI for dbt parse/test on pull requests;
- scheduled/orchestrated dbt runs;
- stricter dev/prod dataset separation;
- dedicated production service accounts;
- freshness tests and source SLAs;
- dashboard deployment/access documentation.

---

## 36. Project Status

```text
Raw data exploration             COMPLETE
BigQuery analytical source       COMPLETE
dbt staging                      COMPLETE
dbt core                         COMPLETE
Dimensional mart                 COMPLETE
PII protection                   COMPLETE
Data quality hardening           COMPLETE
dbt documentation                COMPLETE
BI serving layer                 COMPLETE
Looker Studio dashboard          COMPLETE
Dashboard reconciliation         COMPLETE
```

This project demonstrates not only transformation code, but also:

- data discovery;
- dimensional design;
- data contracts;
- test design;
- PII governance;
- analytical semantics;
- multi-currency reasoning;
- BI reconciliation;
- engineering documentation.

---

## Data Notice

This repository is an educational and portfolio Data Engineering project.

Raw source data should not be committed to Git. Any use or redistribution of source datasets must respect the source owner's terms, privacy requirements, and applicable law.
