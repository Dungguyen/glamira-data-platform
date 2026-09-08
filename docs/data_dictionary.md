# Data Dictionary — Glamira Analytics

## 1. Collection: `summary`

### 1.1 Overview

`summary` is the raw event collection containing user interaction events
generated from Glamira storefronts.

The collection is stored in MongoDB and follows a flexible,
schema-on-read structure. Different event types may contain different
sets of attributes.

### Grain



> One MongoDB document represents one tracked user event.

### Source statistics

| Metric | Value |
|---|---:|
| Total documents | 41,432,473 |
| Source format | BSON |
| MongoDB database | `glamira` |
| MongoDB collection | `summary` |
| Primary identifier | `_id` |

---

### 1.2 Common fields

| Field Name | Observed Type | Nullable / Conditional | Description | Example |
|---|---|---|---|---|
| `_id` | ObjectId | No | MongoDB unique identifier for the event document | `ObjectId(...)` |
| `collection` | STRING | Expected No | Event type / tracking action | `view_product_detail` |
| `time_stamp` | INT64 | Conditional | Raw event timestamp | `...` |
| `ip` | STRING | Conditional | Source IP address of the event | `85.115.53.202` |
| `user_agent` | STRING | Conditional | Browser/device user-agent string | `Mozilla/5.0 ...` |
| `resolution` | STRING | Conditional | Client screen resolution | `1920x1080` |
| `user_id_db` | STRING | Conditional | User identifier from application database | `...` |
| `device_id` | STRING | Conditional | Tracking/device identifier | `...` |
| `api_version` | STRING | Conditional | Version of tracking API | `...` |
| `store_id` | STRING | Conditional | Glamira storefront/store identifier | `...` |
| `local_time` | STRING | Conditional | Event-local time stored by source system | `...` |
| `current_url` | STRING | Conditional | URL where the event occurred | `https://www.glamira...` |
| `referrer_url` | STRING | Conditional | Referring page URL | `https://www.glamira...` |
| `email_address` | STRING | Conditional | Email value captured by applicable events | `...` |
| `product_id` | STRING | Conditional | Product associated with the event | `96047` |
| `collect_id` | STRING | Conditional | Source collection/tracking identifier | `...` |
| `cat_id` | NULL / STRING-like | Conditional | Category identifier where available | `...` |
| `recommendation` | BOOL | Conditional | Indicates recommendation-related behavior | `true` |
| `show_recommendation` | STRING / BOOL / NULL | Conditional | Recommendation display state; schema varies | `true` |
| `utm_source` | STRING / BOOL | Conditional | Campaign/source tracking value | `google` |
| `utm_medium` | STRING / BOOL | Conditional | Campaign-medium tracking value | `cpc` |
| `option` | OBJECT / ARRAY / Missing | Conditional | Product configuration/options payload | `[...]` |

---

### 1.3 Event-specific schema behavior

The `summary` collection does not have a fixed relational-style schema.

Different values of `collection` represent different event types and
therefore carry different attributes.

Examples:

#### `view_product_detail`

Commonly contains:

- `product_id`
- `current_url`
- product-related `option`
- user/device/session attributes

This event represents a product-detail page interaction.

#### Product-option events

Examples:

- `select_product_option`
- `select_product_option_quality`

These events contain a `product_id` and may contain detailed product
configuration information.

#### Cart and checkout events

Examples:

- `view_shopping_cart`
- `checkout`
- `checkout_success`

These event types may contain nested arrays representing multiple
products in the same cart/order event.

Therefore:

> One event can reference more than one product through nested
> cart structures.

#### Recommendation events

Recommendation-related events may contain product identifiers in
nested recommendation structures rather than only in the top-level
`product_id` field.

This distinction must be considered when extracting the complete
product universe.

---
###
### 1.4 `option` schema drift

The `option` field has multiple observed representations.

#### Representation 1 — Object

Example conceptual structure:
###

Observed array items may contain fields such as:

option_label
option_id
value_label
value_id

Additional keys may also appear depending on event/product
configuration.

Interpretation

This is treated as schema drift within the source tracking data.

It is not automatically classified as corrupted data.

Downstream transformations must inspect the actual BSON type instead
of assuming option always has one representation.

### 1.5 Mixed-type fields

Several fields have been observed with more than one BSON type.

Field	Observed behavior
show_recommendation	May be string, boolean or null
utm_source	May be string or boolean
utm_medium	May be boolean or string
option	May be object, array or missing

These fields require schema-on-read handling.

Consumers should not assume a single static data type without an
explicit normalization step.

### 1.6 Product relationships

Product identifiers can appear in multiple structures.

Top-level product relationship
summary.product_id
        ↓
dim_product.product_id

Common examples include:

view_product_detail
select_product_option
select_product_option_quality
add_to_cart_action
view_all_recommend
back_to_product_action
Nested cart relationship

Cart/checkout events may contain multiple product IDs inside nested
cart structures.

summary
   │
   └── cart[]
          └── product_id
Recommendation relationship

Recommendation events may contain product IDs in nested recommendation
objects/arrays.

Therefore, building the complete product universe requires inspecting
top-level, cart and recommendation structures.

### 1.7 IP relationship

The raw source contains IP addresses but does not contain analytical
geography such as country or city.

Relationship:

summary.ip
    ↓
ip_geolocation.ip_address

The enriched IP dataset is used to provide geographic attributes such
as country, region and city.

### 1.8 Known data-quality and schema issues
Issue	Interpretation	Treatment
Fields missing for certain event types	Expected event-specific schema	Treat as schema-on-read
option object/array variation	Source schema drift	Handle by BSON type
utm_source mixed types	Schema inconsistency	Normalize downstream if required
utm_medium mixed types	Schema inconsistency	Normalize downstream if required
show_recommendation mixed types	Schema inconsistency	Normalize downstream if required
Nested product identifiers	Product IDs are not always top-level	Inspect nested structures
Raw IP lacks geography	Business attribute missing from source	Enrich using GeoIP dataset
Raw product IDs lack complete business metadata	Product analytics cannot rely on raw events alone	Enrich using product dimension
Localized URLs	Same product may have many storefront URLs	Preserve representative/canonical URL logic
Flexible MongoDB schema	Columns are not globally applicable	Document semantics by event type
### 1.9 Usage notes

The summary collection should be treated as a raw event source.

Analytical consumers should avoid assuming:

every field exists on every event;
every product ID is stored at the top level;
option always has the same structure;
campaign fields always have one data type;
IP addresses directly represent a country or city;
raw product_id alone provides product name/category.

Enrichment datasets and downstream analytical models should be used
where business-friendly attributes are required.

## 2. Dataset: `ip_geolocation`

### 2.1 Overview

`ip_geolocation` is an enrichment dataset derived from unique IP
addresses observed in the raw `summary` event collection.

The raw event data contains IP addresses but does not directly contain
analytical geographic attributes such as country, region, or city.

The enrichment process uses the GeoLite2 City database to map public IP
addresses to approximate geographic information.

### Grain

> One row represents one unique source IP value.

### Source relationship
###
text
summary.ip
    ↓
ip_geolocation.ip_address
This dataset can be joined back to the raw event dataset to support
geographic analytics such as:

events by country;
events by region;
events by city;
geographic customer activity;
geographic revenue analysis after joining with transaction events.
### 2.2 Fields
Field Name	Type	Nullable	Description	Example
ip_address	STRING	No	IP address observed in raw event data	85.115.53.202
country_code	STRING	Yes	ISO-style country code returned by GeoIP lookup	GB
country_name	STRING	Yes	Country name associated with the IP	United Kingdom
region_name	STRING	Yes	Administrative region/state where available	England
city_name	STRING	Yes	City associated with the IP where available	London
latitude	FLOAT	Yes	Approximate geographic latitude	51.5074
longitude	FLOAT	Yes	Approximate geographic longitude	-0.1278

Exact column names should follow the exported
ip_geolocation.csv implementation if they differ from the names
above.

### 2.3 Enrichment statistics
Metric	Value
Total unique source IP values	3,239,628
Valid IP addresses	3,239,627
Invalid source values	1
IPv4 addresses	3,238,153
IPv6 addresses	1,474
Non-global IP addresses	306
Eligible public IP addresses	3,239,321
Successful GeoIP lookups	3,238,973
Address not found	348
### 2.4 Geographic coverage
Geographic Attribute	Coverage
GeoIP lookup success	99.99%
Country	99.99%
Region	88.89%
City	85.39%

Country-level analytics therefore have significantly better coverage
than city-level analytics.

A missing city does not necessarily mean the IP lookup failed.

For example:

IP lookup
   │
   ├── country available
   ├── region available
   └── city unavailable

This should be treated as partial geolocation rather than a failed
record.

###2.5 Invalid and non-global addresses

The source contained:

one invalid value;
private/non-global IP addresses;
valid public IPv4 addresses;
valid public IPv6 addresses.

Invalid and non-global addresses are not expected to produce normal
public GeoIP results.

These records must not be interpreted as enrichment pipeline failures.

### 2.6 Data-quality rules
Check	Result	Interpretation
Duplicate IP grain	One row per unique source value	Expected
Invalid IP values	1	Source DQ issue
GeoIP address not found	348	Expected lookup limitation
Country missing	Very low	High country coverage
Region missing	~11.11%	GeoIP coverage limitation
City missing	~14.61%	GeoIP coverage limitation
Private/non-global IP	306	Not suitable for public GeoIP mapping
### 2.7 Known limitations
Approximate location

GeoIP location represents an approximate network-based location.

It must not be interpreted as:

the user's exact physical location;
a residential address;
GPS-level location.
City coverage is incomplete

City information is not available for every successfully resolved IP.

Therefore:

country-level analysis
        ↓
more reliable coverage

city-level analysis
        ↓
lower coverage

Dashboards using city-level dimensions should support NULL or
UNKNOWN city values.

Location changes over time

IP geolocation databases are snapshots.

An IP address may be assigned to a different location or network in the
future.

The current enrichment therefore represents:

Location according to the GeoLite2 database version used during
enrichment.

For strict historical reproducibility, the GeoIP database version/date
should be preserved in pipeline metadata.

### 2.8 Business usage

This dataset exists primarily to support the geographic dashboard
requirement.

Example analytical relationship:

checkout_success event
        │
        ├── ip
        │
        ▼
ip_geolocation
        │
        ├── country
        ├── region
        └── city
        │
        ▼
Revenue by Geography

The raw summary dataset should remain the source of event facts,
while ip_geolocation supplies the geographic dimension attributes.

### 2.9 Example analytical join

Conceptually:

SELECT
    geo.country_name,
    COUNT(*) AS event_count
FROM summary AS events
LEFT JOIN ip_geolocation AS geo
    ON events.ip = geo.ip_address
GROUP BY geo.country_name;

A LEFT JOIN is preferred so that events without successful
geolocation are not silently removed from analytics.

## 3. Dataset: `dim_product`

### 3.1 Overview

`dim_product` is the product enrichment dataset used to attach
business-friendly product attributes to product IDs observed in the
raw `summary` event collection.

The raw event data primarily provides `product_id` values but does not
consistently provide analytical attributes such as:

- product name;
- SKU;
- product category;
- product description;
- product image.

Product metadata was therefore collected from Glamira storefront
product pages and joined back to the validated product universe.

### Grain

> One row represents one unique `product_id`.

This grain must remain unique.

A product is retained in the dimension even when external enrichment
was not successful.

---

### 3.2 Product universe and enrichment result

| Metric | Value |
|---|---:|
| Validated product universe | 19,558 |
| Dimension rows | 19,558 |
| Unique product IDs | 19,558 |
| Duplicate product IDs | 0 |
| Successfully enriched products | 18,648 |
| Not enriched products | 910 |
| Enrichment coverage | 95.35% |
| Product accounting coverage | 100% |

The final dimension preserves the complete validated product universe.


Products that could not be enriched are not dropped.

### 3.3 Fields
Field Name	Type	Nullable	Description
product_id	STRING	No	Unique product identifier and grain of the dimension
sku	STRING	Yes	Product SKU obtained from storefront enrichment
product_name	STRING	Yes	Localized product name obtained from storefront enrichment
category	STRING	Yes	Localized category/breadcrumb value obtained from storefront enrichment
description	STRING	Yes	Product description obtained from storefront enrichment
image_url	STRING	Yes	Product image URL
representative_url	STRING	Yes	Deterministically selected product URL observed in raw event data
representative_host	STRING	Yes	Host associated with representative_url
crawl_url	STRING	Yes	Product URL that successfully supplied enrichment metadata
crawl_host	STRING	Yes	Glamira storefront host used for successful enrichment
source_url_count	INTEGER	Yes	Number of distinct source URLs observed for the product
source_url_status	STRING	No	Indicates whether source URLs were observed
product_master_status	STRING	No	Product enrichment status: ENRICHED or NOT_ENRICHED
### 3.4 Status semantics
ENRICHED

The product has successfully collected storefront metadata.

For the current retained enriched dataset:

product_name is populated;
sku is populated;
category is populated;
description is populated;
image_url is populated.

Total:

18,648 products
NOT_ENRICHED

The product belongs to the validated product universe but no accepted
product metadata was retained from the crawl.

These products remain in the dimension.

Total:

910 products

Their product metadata fields may therefore be NULL/empty.

### 3.5 Source relationships

The primary relationship from raw events is:

summary.product_id
        ↓
dim_product.product_id

However, product identifiers can also occur inside nested cart or
recommendation structures.

Therefore dim_product represents the complete discovered product
universe, not only products found in the top-level product_id field.

### 3.6 URL semantics

representative_url and crawl_url have different meanings.

representative_url

Derived from product URLs observed in the raw event dataset.

The representative URL is selected deterministically from eligible
production storefront URLs.

It represents:

A source-observed URL associated with the product.

crawl_url

The storefront URL from which product metadata was successfully
collected.

It represents:

The actual enrichment source for the product metadata.

These fields should not be assumed to be identical.

The same product can appear across multiple localized Glamira
storefronts.

### 3.7 Product metadata quality

Semantic profiling of the enriched product dataset produced the
following results:

Check	Result
Enriched products	18,648
Unique SKUs	18,648
Duplicate SKU values	0
Products using duplicate SKUs	0
Unique product names	18,638
Crawl URL/host mismatch	0
Representative URL/host mismatch	0
Invalid image URLs	0
Short metadata anomaly rows	0

Duplicate product names are allowed because product_name is not used
as the dimension key.

product_id remains the primary grain of this dataset.

### 3.8 Category limitation

The category value is collected from localized Glamira storefront
HTML.

The field is useful for exploratory product analytics, but it is not
yet a canonical cross-country product taxonomy.

Category profiling identified localized values such as:

Wedding Rings
Anillos de boda
结婚戒指
Alyans

These values may represent the same business concept in different
languages.

Semantic profiling also identified cases where the extracted category
value equals the product name.

Examples include values such as:

Gracious Angel
Gracious Beauty
GLAMIRA Earring Lynn

This indicates that some storefront breadcrumb structures expose the
product name as the final breadcrumb value.

Current decision

The current iteration accepts this limitation.

The raw extracted category is preserved rather than guessed or
manually remapped.

Therefore:

category must not yet be treated as a canonical normalized taxonomy.

A later analytical modeling step may introduce a normalized category
mapping.

### 3.9 Crawl stopping decision

Full enrichment was stopped after diminishing returns became
significant.

Additional crawl attempts over approximately one thousand unresolved
product IDs produced only a very small number of newly enriched
products and required disproportionate runtime.

Final accepted state:

Product universe   : 19,558
Enriched           : 18,648
Not enriched       :    910
Coverage           : 95.35%

The 910 unresolved products are preserved rather than removed.

This is recorded as an accepted limitation of the current project
iteration.

### 3.10 Price fields

The crawl output may contain attributes such as:

price;
old_price;
currency.

These fields are not currently included as core attributes of
dim_product.

Price can depend on storefront, currency, product configuration and
time.

Treating one crawled price as a globally static product attribute could
therefore produce misleading analytics.

If price analysis is required later, it should be modeled with
storefront/time context rather than assumed to be a permanent
dimension attribute.

### 3.11 Business usage

The product dimension supports enrichment of event data for product
analytics.

Conceptually:

checkout / product event
        │
        ├── product_id
        │
        ▼
dim_product
        │
        ├── product_name
        ├── category
        └── sku
        │
        ▼
Product Analysis Dashboard

Example analytical join:

SELECT
    product.category,
    COUNT(*) AS event_count
FROM summary AS events
LEFT JOIN dim_product AS product
    ON events.product_id = product.product_id
GROUP BY product.category;

A LEFT JOIN is preferred so that events referencing products without
successful enrichment are not silently removed.

## 4. Dataset Relationships

The Glamira analytical datasets are connected primarily through
IP addresses and product identifiers.

### 4.1 High-level relationship

                     ┌─────────────────────┐
                     │       summary       │
                     │   raw event data    │
                     │  41,432,473 events  │
                     └─────────┬───────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 │ ip                        │ product_id
                 ▼                           ▼
       ┌───────────────────┐       ┌────────────────────┐
       │  ip_geolocation   │       │    dim_product     │
       │ 1 row / unique IP │       │ 1 row / product_id │
       └───────────────────┘       └────────────────────┘
                 │                           │
                 ▼                           ▼
         Geographic Analysis          Product Analysis
### 4.2 Raw events → IP geolocation

Join key:

summary.ip
    =
ip_geolocation.ip_address

Relationship:

many events
    ↓
one IP geolocation row

Cardinality:

Many raw event documents can reference the same IP address.

Recommended analytical join:

SELECT
    events.*,
    geo.country_name,
    geo.region_name,
    geo.city_name
FROM summary AS events
LEFT JOIN ip_geolocation AS geo
    ON events.ip = geo.ip_address;

A LEFT JOIN should be used so that events with invalid, private,
non-global, or unresolved IP addresses remain in the analytical
dataset.

### 4.3 Raw events → Product dimension

Primary join key:

summary.product_id
    =
dim_product.product_id

Relationship:

many product-related events
        ↓
one product dimension row

Recommended conceptual join:

SELECT
    events.*,
    product.sku,
    product.product_name,
    product.category
FROM summary AS events
LEFT JOIN dim_product AS product
    ON events.product_id = product.product_id;

A LEFT JOIN should be preferred because products with
NOT_ENRICHED status must not cause source events to disappear.

### 4.4 Nested product relationships

Not every product reference exists in the top-level product_id
field.

Some event types contain product identifiers in nested structures.

Examples include:

shopping cart products;
checkout products;
recommendation products;
viewing/recommended product relationships.

Conceptually:

summary event
   │
   ├── product_id
   │
   ├── cart[]
   │      └── product_id
   │
   └── recommendation[]
          └── product_id

Therefore, downstream models that require complete product-event
relationships must inspect both top-level and nested product
structures.

The top-level summary.product_id → dim_product.product_id join alone
does not represent every possible product relationship in the raw
dataset.

## 5. Consolidated Known Data Quality Issues

The following issues were identified during investigation and
enrichment.

Issue	Dataset	Severity	Interpretation	Current Treatment
Event-specific NULL fields	summary	Low	Different event types intentionally contain different attributes	Treat as expected schema-on-read behavior
Flexible document schema	summary	Medium	MongoDB documents do not share one fixed schema	Document fields by semantics/event type
option object/array variation	summary	Medium	Same field appears with different BSON structures	Preserve and normalize later if required
Mixed utm_source types	summary	Medium	String/boolean values observed	Normalize downstream before typed analytics
Mixed utm_medium types	summary	Medium	String/boolean values observed	Normalize downstream before typed analytics
Mixed show_recommendation types	summary	Medium	String/boolean/null values observed	Normalize downstream before typed analytics
Nested product IDs	summary	Medium	Product references are not always top-level	Inspect cart/recommendation structures where required
One invalid IP value	ip_geolocation	Low	Invalid source IP value exists	Exclude from public GeoIP lookup
Non-global IP addresses	ip_geolocation	Low	Private/non-global addresses cannot be normally geolocated	Preserve as known lookup limitation
GeoIP lookup not found	ip_geolocation	Low	Some valid public IPs have no matching GeoIP record	Preserve with NULL geographic fields
Region coverage < 100%	ip_geolocation	Medium	GeoIP database does not resolve region for every IP	Allow NULL/UNKNOWN
City coverage < 100%	ip_geolocation	Medium	City-level enrichment is incomplete	Allow NULL/UNKNOWN; disclose dashboard limitation
910 products not enriched	dim_product	Medium	Product metadata collection stopped due to diminishing returns	Preserve product IDs with NOT_ENRICHED status
Localized category names	dim_product	Medium	Same business category may appear in different languages	Retain raw category; normalize later if needed
Category/product-name leakage	dim_product	Medium	Some extracted breadcrumb categories equal product names	Accepted limitation for current iteration
Multiple URLs per product	Product discovery	Low	Same product appears across storefronts/configurations	Keep deterministic representative URL
Product price varies by context	Crawl output	Medium	Price may depend on storefront, currency and configuration	Do not treat crawl price as a globally static product attribute
## 6. Data Quality Decisions
### 6.1 Schema-on-read is intentional

Missing fields are not automatically data-quality failures.

For example:

view_product_detail
    → product-specific attributes

checkout_success
    → transaction/cart-specific attributes

A field that is absent because it is irrelevant to an event type
should not be treated the same as an unexpectedly missing required
field.

### 6.2 No silent record deletion

Enrichment failures should not remove valid source entities.

Examples:

Unresolved IP
    → keep event
    → geography = NULL

NOT_ENRICHED product
    → keep product_id
    → product metadata = NULL

This principle prevents analytical counts from changing simply because
an enrichment dataset is incomplete.

### 6.3 Raw and enriched attributes have different authority

The raw summary dataset is the source of truth for tracked events.

Enrichment datasets provide additional analytical attributes:

summary
    = event facts

ip_geolocation
    = geographic enrichment

dim_product
    = product enrichment

Enrichment data must not overwrite or redefine the existence of raw
events.

## 7. Current Dataset Summary
Dataset	Grain	Approximate Rows	Primary Join Key	Purpose
summary	One row/document per tracked event	41,432,473	_id	Raw event source
ip_geolocation	One row per unique source IP	3,239,628 source values	ip_address	Geographic enrichment
dim_product	One row per unique product	19,558	product_id	Product enrichment
## 8. Business Requirement Mapping
Business Requirement	Raw Data Available	Enrichment Required	Dataset Used
Revenue by country	IP only	Yes	summary + ip_geolocation
Revenue by city	IP only	Yes	summary + ip_geolocation
Product performance	product_id	Yes	summary + dim_product
Product category analysis	product_id	Yes	summary + dim_product
Event/time trends	Event timestamp	No external enrichment required	summary

This mapping explains why both IP and product enrichment were included
in the project scope.