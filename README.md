# Glamira Data Platform

A Data Engineering project for exploring, validating, enriching, and
preparing Glamira behavioral event data for downstream analytics.

The project follows an evidence-first workflow:

> Understand the data → validate assumptions → enrich required
> dimensions → document decisions → build analytical pipelines.

---

## 1. Business Context

The raw Glamira dataset contains behavioral/e-commerce events but does
not directly provide all business-friendly analytical attributes.

Example requirements include:

- geographic performance;
- revenue by country/city;
- product performance;
- product category analysis;
- time-based behavioral analysis.

Two important enrichment gaps were identified:

raw IP
   ↓
GeoIP enrichment
   ↓
country / region / city

and:

product_id
   ↓
product metadata enrichment
   ↓
product_name / sku / category / description

## 2. Source Dataset

The source dataset is a BSON file containing Glamira event data.

Validated source statistics:

Metric	Value
BSON documents	41,432,473
MongoDB documents	41,432,473
Source/MongoDB difference	0
Source size	~31.2 GiB
MongoDB database	glamira
MongoDB collection	summary

The source and MongoDB counts reconcile exactly.

## 3. Data Characteristics

The source follows a flexible event-oriented schema.

Different values of collection represent different event types and
therefore contain different attributes.

Examples include:

view_product_detail
view_listing_page
select_product_option
select_product_option_quality
add_to_cart_action
view_shopping_cart
checkout
checkout_success
recommendation-related events

Important characteristics discovered during profiling:

fields are event-dependent;
missing values are often semantic rather than data loss;
option can appear as object or array;
some fields have mixed BSON types;
products can appear at top level or inside nested cart/recommendation
structures;
price and currency values can use localized representations.

See:

docs/data_quality_report.md
docs/data_dictionary.md

for detailed findings.

## 4. Architecture — Current Scope
                         GCS
                  summary.bson
                       │
                       ▼
                  MongoDB VM
             glamira.summary
             41,432,473 docs
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
     IP Extraction            Product Discovery
          │                         │
          ▼                         ▼
   GeoLite2 City              Product Enrichment
          │                         │
          ▼                         ▼
  ip_geolocation              dim_product
     ~3.24M IPs              19,558 products
          │                         │
          └────────────┬────────────┘
                       ▼
                Analytics-ready
                 enrichment data
## 5. Data Exploration

A bounded MongoDB exploration script is available at:

src/glamira_data/discovery/data_exploration.py

Example:

python data_exploration.py --sample-size 100000

Latest 100K exploration run:

Metric	Result
Documents inspected	100,000
Event types observed	22
Unique IPs in sample	13,761

The bounded sample is used for exploration only and should not be
interpreted as the statistical distribution of the complete dataset.

## 6. IP Geolocation Enrichment

IP enrichment uses the GeoLite2 City database.

Implementation:

src/glamira_data/enrichment/ip_geo/
├── enrich_ips.py
├── validate_ips.py
└── benchmark_geoip.py

Validated results:

Metric	Value
Unique source IP values	3,239,628
Valid IPs	3,239,627
Invalid source values	1
Eligible public IPs	3,239,321
Successful lookups	3,238,973
Country coverage	99.99%
Region coverage	88.89%
City coverage	85.39%

GeoIP locations are approximate and should not be treated as exact
physical user locations.

Detailed report:

docs/ip_geolocation_report.md
## 7. Product Discovery and Enrichment

The complete discovered product universe contains:

19,558 unique product IDs

Product IDs were discovered across:

top-level product fields;
cart structures;
checkout structures;
recommendation structures.

Product extraction code:

src/glamira_data/product_extraction/

Product dimension code:

src/product/
├── build_dim_product_enriched.py
└── profile_dim_product_semantics.py

Current product enrichment result:

Metric	Value
Product universe	19,558
Enriched products	18,648
Not enriched	910
Enrichment coverage	95.35%
Dimension rows	19,558
Duplicate product IDs	0
Product accounting coverage	100%

The enrichment process was stopped after diminishing returns were
observed.

Unresolved products are retained in the dimension with
NOT_ENRICHED status instead of being silently removed.

## 8. Known Product Limitation

Product categories are collected from localized storefront metadata.

Observed values include localized equivalents of categories such as:

Wedding Rings
Anillos de boda
结婚戒指
Alyans

Some extracted category values also correspond to product-name
breadcrumb values.

Therefore, the current category field should not yet be treated as a
canonical cross-country taxonomy.

Category normalization is intentionally deferred to a later analytical
modeling step.

## 9. Repository Structure
glamira-data-platform/
│
├── docs/
│   ├── data_dictionary.md
│   ├── data_quality_report.md
│   ├── ip_geolocation_report.md
│   ├── mongodb_vm_setup.md
│   ├── product_crawl_feasibility.md
│   ├── product_dimension_contract.md
│   ├── product_dimension_enrichment.md
│   ├── product_extraction_report.md
│   ├── product_source_decision.md
│   └── scope_confirmation.md
│
├── src/
│   ├── glamira_data/
│   │   ├── discovery/
│   │   ├── enrichment/
│   │   │   └── ip_geo/
│   │   └── product_extraction/
│   │
│   └── product/
│
├── data/
│   ├── raw/          # ignored
│   ├── crawl/        # ignored
│   └── processed/    # ignored
│
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md

Generated datasets and large raw files are intentionally excluded from
Git.

## 10. Local Development Setup
Requirements
Python 3.12
uv
Git
Visual Studio Code
MongoDB when local MongoDB access is required
Google Cloud CLI for GCP operations
Clone repository
git clone <YOUR_REPOSITORY_URL>
cd glamira-data-platform
Install dependencies

The project uses uv for Python environment and dependency management.

uv sync --locked

Activate the environment if required.

Windows PowerShell:

.venv\Scripts\Activate.ps1

Linux:

source .venv/bin/activate
## 11. Environment Variables

Credentials and secrets must not be committed to Git.

Example configuration:

MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=glamira
MONGODB_COLLECTION=summary

Store local values in:

.env

The .env file is excluded through .gitignore.

## 12. Documentation

Important project documents:

Document	Purpose
docs/scope_confirmation.md	Scope and GO/NO-GO decisions
docs/data_quality_report.md	Source data-quality assessment
docs/mongodb_vm_setup.md	MongoDB/GCP VM setup and validation
docs/ip_geolocation_report.md	GeoIP enrichment findings
docs/product_source_decision.md	Product metadata source decision
docs/product_extraction_report.md	Product discovery findings
docs/product_crawl_feasibility.md	Crawl feasibility and limitations
docs/product_dimension_contract.md	Product dimension grain/schema contract
docs/product_dimension_enrichment.md	Product enrichment results
docs/data_dictionary.md	Dataset and field definitions
## 13. Current Project Status
Phase 0 — Data Investigation
PASS

Phase 1 — Infrastructure & Full Data Loading
PASS

Phase 2 — Data Enrichment
PASS_WITH_ACCEPTED_LIMITATION

Accepted limitation:

910 / 19,558 products are not enriched.

The complete product universe is preserved.

## 14. Engineering Principles

This project follows several core Data Engineering practices:

understand data before coding;
validate row counts between pipeline stages;
preserve raw source data;
avoid silent data loss;
document schema drift;
distinguish expected NULLs from data-quality failures;
use explicit grain for analytical datasets;
document accepted limitations;
keep generated/large datasets outside Git;
commit work in small logical checkpoints.