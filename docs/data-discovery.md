# Glamira Data Discovery

## 1. Document purpose

This document records the initial data discovery performed on the Glamira raw event dataset.

The purpose of this phase is to understand:

- the overall BSON structure;
- event types;
- common and event-specific fields;
- nested and polymorphic structures;
- observed BSON data types;
- potential data quality issues;
- business semantics that can reasonably be inferred from the data;
- questions that require further validation;
- requirements for full-dataset profiling on GCP.

This document is based primarily on a local sample of **50,000 BSON documents**.

> IMPORTANT:
>
> Findings from the 50,000-document sample must not be treated as guarantees about the complete dataset.
>
> All schema assumptions and data-quality rules must be validated against the full dataset on GCP before being promoted into production data contracts.

---

# 2. Dataset overview

## 2.1 Source

Raw dataset:

```text
summary.bson
```

Cloud storage location:

```text
gs://glamira-raw-data-506706/summary.bson
```

Observed object size:

```text
33,530,129,089 bytes
≈ 33.5 GB
```

The source file is BSON and contains event-oriented data generated from the Glamira website/application.

---

## 2.2 Local discovery sample

For local exploration, 50,000 BSON documents were extracted from the raw file and restored into a local MongoDB instance.

Local collection:

```text
Database: glamira
Collection: summary_sample
Documents: 50,000
```

MongoDB is used only as a local exploration tool.

It is **not part of the target production data pipeline**.

Target architecture:

```text
Data Sources
     |
     v
Google Cloud Storage
     |
     v
Cloud Function / ingestion orchestration
     |
     v
BigQuery RAW
     |
     v
dbt
     |
     v
BigQuery Analytical
     |
     v
Looker
```

---

# 3. Discovery limitations

The current sample contains the first 50,000 extracted BSON documents.

Therefore:

- it is not guaranteed to be a random sample;
- rare event types may be underrepresented;
- additional event types may exist in the full dataset;
- additional API versions may exist;
- additional BSON types may exist;
- schema drift may exist outside the sample;
- value distributions may differ from the full dataset.

The local discovery phase is intended to generate hypotheses and ingestion requirements rather than production-level guarantees.

---

# 4. Event model

The field:

```text
collection
```

appears to act as the event-type discriminator.

Example:

```text
collection = view_product_detail
collection = view_listing_page
collection = checkout
collection = checkout_success
```

Therefore, the source can be conceptually interpreted as:

```text
Event
|
+-- common event metadata
|
+-- collection
|      |
|      +-- determines event type
|
+-- event-specific payload
```

This is an important characteristic of the source schema.

Different event types contain different fields and may use different structures for fields with the same name.

---

# 5. Event taxonomy

The following 21 event types were observed in the 50,000-document sample.

| Event type | Count |
|---|---:|
| view_product_detail | 14,011 |
| view_listing_page | 12,799 |
| select_product_option | 9,999 |
| select_product_option_quality | 3,119 |
| view_static_page | 2,399 |
| product_detail_recommendation_visible | 1,987 |
| view_landing_page | 1,721 |
| view_home_page | 1,566 |
| product_detail_recommendation_noticed | 727 |
| view_shopping_cart | 439 |
| search_box_action | 364 |
| view_my_account | 278 |
| add_to_cart_action | 237 |
| checkout | 147 |
| product_detail_recommendation_clicked | 138 |
| checkout_success | 50 |
| listing_page_recommendation_visible | 10 |
| view_sorting_relevance | 4 |
| landing_page_recommendation_visible | 2 |
| listing_page_recommendation_noticed | 2 |
| listing_page_recommendation_clicked | 1 |

Total:

```text
50,000 events
```

---

# 6. Common event fields

Frequently observed top-level fields include:

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
show_recommendation
current_url
referrer_url
email_address
collection
```

Some events additionally contain fields such as:

```text
product_id
cat_id
collect_id
option
cart_products
order_id
price
currency
is_paypal
recommendation
utm_source
utm_medium
```

These additional fields are event-dependent.

---

# 7. Preliminary field interpretation

The following interpretations are based on field names and observed values.

They should not be treated as confirmed business definitions unless validated against source-system documentation.

## `_id`

Observed BSON type:

```text
ObjectId
```

Interpretation:

```text
MongoDB/BSON document or event identifier
```

It should not be treated as the order identifier.

A separate `order_id` field exists in checkout-related events.

---

## `time_stamp`

Example:

```text
1591266090
```

Observed as a Unix-style timestamp.

Expected interpretation:

```text
seconds since Unix epoch
1970-01-01 00:00:00 UTC
```

Full-data validation is required before assuming every value follows the same unit and valid range.

---

## `ip`

Represents the client IP address recorded for the event.

Potential uses include:

- traffic analysis;
- approximate network/geographical enrichment;
- fraud/security analysis.

IP addresses should be treated carefully because they may contain sensitive or privacy-relevant information.

---

## `user_agent`

Example:

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64)
AppleWebKit/537.36 ...
```

This is the HTTP User-Agent string, not a website URL.

It may be parsed to derive:

```text
browser
browser version
operating system
device class
```

---

## `resolution`

Example:

```text
1366x768
```

Likely represents client screen resolution.

Potential analytical uses:

- desktop/mobile behavior;
- UX analysis;
- device segmentation.

---

## `user_id_db`

Likely represents an application/database user identifier.

Potentially useful for identifying authenticated users.

The exact semantics require business/source-system confirmation.

---

## `device_id`

Likely identifies a browser/device or tracking device.

Potential use:

```text
anonymous user activity
repeat visits
session/user behavior
funnel analysis
```

The exact generation mechanism is unknown.

---

## `api_version`

Observed value in the 50K sample:

```text
1.0
```

All observed documents use API version `1.0`.

This field may become important for schema evolution.

However, because only one version was observed locally, no conclusion can yet be made about schema differences between API versions.

Full-dataset profiling must verify whether additional API versions exist.

---

## `store_id`

Likely identifies a Glamira store, storefront, market, or site context.

The exact business definition is currently unknown.

It should not yet be interpreted as the physical store responsible for fulfillment without additional evidence.

---

## `local_time`

Example:

```text
2020-06-04 5:54:48
```

Likely represents local event time.

It should not automatically be interpreted as a reliable geographical location.

Further validation is required regarding:

- timezone;
- formatting;
- relationship to `time_stamp`;
- source of local timezone information.

---

## `current_url`

Represents the page URL where the event occurred.

Potential uses:

```text
page classification
product/category extraction
funnel reconstruction
traffic analysis
```

---

## `referrer_url`

Likely represents the previous/referring URL.

Potential uses:

```text
traffic-source analysis
navigation analysis
marketing attribution
referral analysis
```

Referrer alone should not automatically be treated as authoritative marketing attribution.

---

## `email_address`

Email information associated with an event when available.

Presence of the field does not guarantee a meaningful value.

Possible states must be distinguished:

```text
missing
null
empty string
valid value
invalid value
```

---

# 8. Event-specific schema observations

Six major event types were selected for deeper profiling:

```text
view_product_detail
view_listing_page
select_product_option
add_to_cart_action
checkout
checkout_success
```

These events represent important parts of the customer journey:

```text
Product discovery
      |
      v
Product view
      |
      v
Option selection
      |
      v
Add to cart
      |
      v
Checkout
      |
      v
Checkout success
```

---

# 9. `option` polymorphism

The top-level `option` field is polymorphic.

Observed distribution across the 50K sample:

| BSON type | Count | Percentage |
|---|---:|---:|
| array | 27,366 | 54.73% |
| object | 12,816 | 25.63% |
| missing | 9,818 | 19.64% |

The variation is strongly associated with `collection`.

---

## 9.1 Option type by event

Examples:

```text
add_to_cart_action
    option = array

select_product_option
    option = array

select_product_option_quality
    option = array

view_product_detail
    option = array

view_listing_page
    option = object

view_sorting_relevance
    option = object

checkout
    option = missing

checkout_success
    option = missing
```

This suggests that top-level `option` variation in the sample is primarily related to event type rather than random schema corruption.

---

# 10. Example `option` structures

## Array representation

Example conceptual structure:

```json
[
  {
    "option_label": "diamond",
    "option_id": 261151,
    "value_label": "Swarovsky Cristall",
    "value_id": 2166253
  },
  {
    "option_label": "alloy",
    "option_id": 261154,
    "value_label": "Weißgold 585",
    "value_id": 2166328
  }
]
```

Typical fields:

```text
option_label
option_id
value_label
value_id
```

---

## Object representation

For some listing-related events, `option` is represented as an object.

Observed keys include examples such as:

```text
alloy
diamond
shapediamond
```

Therefore, ingestion must not assume that all top-level `option` values share a single BSON type.

---

# 11. Checkout payload

Checkout-related events contain:

```text
cart_products
order_id
```

The `cart_products` field is an array containing one or more products.

Conceptual structure:

```text
checkout event
|
+-- cart_products[]
       |
       +-- product_id
       +-- amount
       +-- price
       +-- currency
       |
       +-- option[]
              |
              +-- option_label
              +-- option_id
              +-- value_label
              +-- value_id
```

---

# 12. Event grain and nested grain

The discovery revealed multiple levels of grain.

## Event grain

```text
1 document = 1 event
```

Example:

```text
checkout event
```

## Cart-product grain

After expanding `cart_products`:

```text
1 row = 1 product within an event
```

Relationship:

```text
EVENT
  1
  |
  N
CART PRODUCT
```

## Product-option grain

A product may contain multiple options:

```text
EVENT
  1
  |
  N
CART PRODUCT
  1
  |
  N
PRODUCT OPTION
```

This grain must be considered when designing analytical models.

Blindly flattening all nested structures into one table may duplicate event- or product-level measures.

---

# 13. Checkout vs checkout_success

The sample shows important structural differences between these two event types.

## `checkout`

Observed:

```text
events = 147
cart product rows after unwind = 170
```

For all 147 checkout events:

```text
order_id = ""
BSON type = string
```

At cart-product grain:

```text
product_id = int
amount = int
price = missing
currency = missing
```

Observed `cart_products[].option`:

| Type | Count |
|---|---:|
| array | 164 |
| string | 6 |

---

## `checkout_success`

Observed:

```text
events = 50
cart product rows after unwind = 57
```

For all 50 events, `order_id` is populated.

Observed `order_id` types:

| Type | Count | Percentage |
|---|---:|---:|
| int | 33 | 66% |
| double | 17 | 34% |

At cart-product grain:

```text
product_id = int
amount = int
price = string
currency = string
```

Observed `cart_products[].option`:

| Type | Count |
|---|---:|
| array | 52 |
| string | 5 |

---

# 14. `cart_products[].option` inconsistency

A nested schema inconsistency was observed.

Normally:

```text
cart_products[].option
    =
ARRAY<OBJECT>
```

However, some products contain:

```text
option = ""
```

Profiling identified:

```text
checkout:
6 string values
6/6 = ""

checkout_success:
5 string values
5/5 = ""
```

Therefore:

```text
11 / 11 observed string representations
were empty strings.
```

### Observed fact

All string-valued `cart_products[].option` fields in the 50K sample are empty strings.

### Inference

The source producer may be using:

```text
""
```

to represent absence of product options.

### Proposed Silver normalization

If full-data profiling confirms this behavior:

```text
"" -> []
```

may be considered.

This transformation must not be applied to the immutable raw representation.

---

# 15. Price representation

`price` was observed in `checkout_success` cart products.

Examples:

```text
880.00
343,00
55,00
```

The BSON type is:

```text
string
```

This indicates locale-dependent numeric formatting.

Possible formats that must be profiled against the full dataset include:

```text
1299.00
1299,00
1,299.00
1.299,00
```

Therefore, price must not be blindly cast to a numeric type.

Normalization should consider:

```text
currency
store
locale
number formatting
```

---

# 16. Currency representation

Observed examples:

```text
£
€
```

The source appears to use currency symbols rather than guaranteed ISO-4217 currency codes.

Potential analytical normalization:

```text
currency_raw
currency_code
```

Example:

```text
€ -> EUR
£ -> GBP
```

However, mapping must be validated because symbols such as `$` may be ambiguous without additional context.

---

# 17. Recommendation fields

For `view_product_detail`, the following combinations were observed:

| recommendation | show_recommendation | Count |
|---|---|---:|
| false | null | 7,099 |
| false | `"false"` | 6,735 |
| false | `"true"` | 177 |

Total:

```text
14,011
```

Therefore:

```text
recommendation = false
```

for every observed `view_product_detail` event in the sample.

`show_recommendation` uses:

```text
null
"false"
"true"
```

The values `"true"` and `"false"` are strings rather than BSON booleans.

### Important conclusion

`recommendation` and `show_recommendation` should not be assumed to represent the same concept.

Their exact business semantics require confirmation.

---

# 18. Data-type inconsistencies

Several important type inconsistencies or polymorphic representations were observed.

## Top-level option

```text
array
object
missing
```

Mostly explained by event type.

## cart_products[].option

```text
array
string
```

String values observed locally are exclusively:

```text
""
```

## checkout_success.order_id

```text
int
double
```

This represents a type inconsistency within the same event type.

Because `order_id` is an identifier rather than a measure, a normalized STRING representation should be considered for the analytical layer.

Before conversion, full-data profiling must verify whether double-valued IDs are integer-valued numbers such as:

```text
720251727.0
```

rather than values containing meaningful fractional components.

## show_recommendation

Observed representations include:

```text
null
"true"
"false"
```

Normalization to nullable BOOLEAN may be appropriate downstream after full-data validation.

---

# 19. Missing vs null vs empty

The discovery phase identified the need to distinguish:

```text
MISSING
NULL
EMPTY
INVALID
VALID
```

These states must not be treated as equivalent.

Example:

```text
order_id missing
```

is different from:

```text
order_id = null
```

which is different from:

```text
order_id = ""
```

This distinction is particularly important when creating data-quality tests.

---

# 20. Preliminary transaction lifecycle

The sample suggests the following lifecycle:

```text
Product viewed
      |
      v
Options selected
      |
      v
Product added to cart
      |
      v
checkout
      |
      | order_id = ""
      | price/currency absent from cart product
      |
      v
checkout_success
      |
      | order_id populated
      | price populated
      | currency populated
      |
      v
Successful transaction
```

This is an inference from observed data.

It should be validated against business/event-tracking documentation before becoming an official semantic model.

---

# 21. Data-quality hypotheses

The following checks should be validated against the full dataset.

## DQ-01 — Event type

`collection` should exist and use an expected event type.

Check:

```text
missing collection
null collection
non-string collection
unknown event types
```

---

## DQ-02 — API version

Profile:

```text
api_version
```

across the full dataset.

The local sample contains only:

```text
1.0
```

Additional versions may imply schema evolution.

---

## DQ-03 — Event-specific schema

Validate field presence and BSON types by:

```text
collection
api_version
```

rather than assuming one global schema.

---

## DQ-04 — Event identifiers

Check:

```text
_id uniqueness
missing _id
duplicate _id
```

---

## DQ-05 — Product identifiers

For product-related events, validate:

```text
product_id
```

for:

```text
missing
null
unexpected type
invalid value
```

---

## DQ-06 — Checkout cart

For checkout-related events:

```text
cart_products
```

should be validated for:

```text
array type
empty arrays
missing values
product count
unexpected nested schema
```

---

## DQ-07 — Product amount

Validate:

```text
cart_products[].amount
```

Expected hypothesis:

```text
integer
> 0
```

Check for:

```text
0
negative values
null
missing
non-integer
```

---

## DQ-08 — Cart product option

Validate full-data distribution of:

```text
cart_products[].option
```

Observed locally:

```text
array
""
```

Check whether any other string or BSON representation exists.

---

## DQ-09 — Checkout order ID

Current local hypothesis:

```text
checkout
→ order_id = ""
```

This may be expected source behavior rather than a quality defect.

Validate against the full dataset.

---

## DQ-10 — Successful checkout order ID

For:

```text
collection = checkout_success
```

`order_id` should be populated.

Check:

```text
missing
null
empty
duplicate
unexpected datatype
```

---

## DQ-11 — Order ID datatype

Observed:

```text
int
double
```

for `checkout_success`.

Investigate whether double values have zero fractional components before normalization.

---

## DQ-12 — Price

Validate:

```text
price
```

for:

```text
missing
null
empty
invalid numeric format
locale-dependent decimal separators
unexpected characters
negative values
zero values
```

---

## DQ-13 — Currency

Profile all currency values.

Check:

```text
symbols
ISO codes
unknown values
missing values
currency/store relationships
```

---

## DQ-14 — Recommendation boolean normalization

Profile:

```text
show_recommendation
```

for all BSON types and values.

Observed locally:

```text
null
"true"
"false"
```

Potential Silver normalization:

```text
"true"  -> TRUE
"false" -> FALSE
null    -> NULL
```

only after full-data validation.

---

## DQ-15 — Recommendation semantics

The exact meaning of:

```text
recommendation
show_recommendation
```

requires business clarification.

Do not merge these fields solely based on their names.

---

## DQ-16 — Timestamp

Validate:

```text
time_stamp
```

for:

```text
datatype
Unix timestamp unit
valid range
future timestamps
extremely old timestamps
```

---

## DQ-17 — Local time

Validate:

```text
local_time
```

for:

```text
format consistency
parseability
timezone semantics
relationship with time_stamp
```

---

## DQ-18 — Email

Profile:

```text
email_address
```

while distinguishing:

```text
missing
null
empty
invalid
valid
```

Sensitive data should not be unnecessarily propagated into analytical models.

---

## DQ-19 — Encoding

Profile textual fields for:

```text
UTF-8 issues
replacement characters
invalid encoding
unexpected control characters
whitespace anomalies
```

Important candidate fields include:

```text
option_label
value_label
current_url
referrer_url
user_agent
```

The sample already contains multilingual product values such as:

```text
Weißgold
Gelbgold
Swarovsky Cristall
```

These are not errors merely because they contain non-ASCII characters.

---

## DQ-20 — Duplicate detection

Duplicate analysis should be performed at multiple levels.

### Physical/document duplicate

```text
duplicate _id
```

### Exact event duplicate

Potentially identical event payloads.

### Semantic duplicate

Two different documents may represent the same logical event.

Semantic duplicate detection may require a combination such as:

```text
device_id
user_id_db
collection
time_stamp
product_id
```

The correct business key has not yet been established.

---

# 22. Schema-on-read implications

The source demonstrates why schema-on-read is useful for the raw ingestion layer.

Example:

```text
option

view_listing_page
    -> object

view_product_detail
    -> array

checkout
    -> missing
```

Nested payloads also vary:

```text
cart_products[].option
    -> array<object>
    -> ""
```

Attempting to impose one rigid schema before understanding these variations may cause:

```text
load failures
data loss
incorrect coercion
unexpected nulls
```

Therefore, the raw ingestion design should prioritize:

```text
source fidelity
recoverability
schema observability
reprocessing capability
```

before analytical normalization.

---

# 23. Raw vs analytical responsibility

The intended separation is:

```text
GCS RAW
--------------------------------
Preserve original source artifact

summary.bson


BigQuery RAW
--------------------------------
Queryable ingestion representation

Preserve source semantics
Avoid premature business transformation


dbt / staging
--------------------------------
Type normalization
Field standardization
Event-specific parsing
Basic data-quality handling


Intermediate models
--------------------------------
Business entities
Sessions
Products
Checkout structures
Recommendation interactions


Analytical marts
--------------------------------
Stable business-ready models
for Looker / analysts
```

---

# 24. Proposed normalization candidates

The following transformations are candidates for downstream processing.

They are **not yet production rules**.

| Raw field/value | Possible normalized representation |
|---|---|
| `show_recommendation = "true"` | BOOLEAN `TRUE` |
| `show_recommendation = "false"` | BOOLEAN `FALSE` |
| `show_recommendation = null` | BOOLEAN `NULL` |
| `cart_products[].option = ""` | empty option collection |
| `order_id int/double` | STRING identifier |
| localized price string | NUMERIC + preserved raw value |
| currency symbol | ISO currency code + preserved raw value |
| Unix `time_stamp` | TIMESTAMP |
| `local_time` string | parsed local DATETIME/TIMESTAMP where semantics permit |

Every transformation must preserve or allow recovery of the raw representation.

---

# 25. Open business questions

The following questions remain unresolved.

## User identity

What exactly does:

```text
user_id_db
```

represent?

Does it only exist for authenticated users?

---

## Device identity

How is:

```text
device_id
```

generated?

Is it:

```text
browser cookie
device fingerprint
session identifier
application-generated UUID
```

?

---

## Store

What exactly does:

```text
store_id
```

represent?

Possible interpretations include:

```text
country storefront
website instance
physical store
fulfillment store
market
```

No assumption should be made yet.

---

## Recommendation

What is the semantic difference between:

```text
recommendation
show_recommendation
```

?

---

## Checkout

Does:

```text
checkout
```

represent:

```text
checkout page viewed
checkout initiated
payment initiated
```

or another business action?

---

## Order ID

At what point in the transaction lifecycle is:

```text
order_id
```

generated?

---

## Price

Is `cart_products[].price`:

```text
unit price
final product price
discounted price
tax-inclusive price
```

?

---

## Currency

Can the same currency symbol represent multiple currency codes depending on:

```text
store_id
country
locale
```

?

---

# 26. Requirements for full-data profiling on GCP

The complete 33.5 GB dataset must be profiled before production transformation rules are finalized.

Required profiling dimensions include:

```text
record count
event-type distribution
api-version distribution
top-level field inventory
field presence by event
field BSON type by event
nested schema distribution
null/missing/empty distribution
timestamp validity
price formats
currency values
order ID types
duplicate IDs
potential semantic duplicates
encoding anomalies
unknown/new fields
unknown/new event types
```

Important profiling should be grouped by:

```text
collection
api_version
```

and, where relevant:

```text
store_id
currency
time period
```

This will help distinguish:

```text
event-specific schema
API-version schema evolution
temporal schema drift
source-system data-quality defects
```

---

# 27. Implications for DE-06

The local discovery phase establishes several requirements for the GCS → BigQuery ingestion POC.

The ingestion design must answer:

1. How should a 33.5 GB BSON file be processed safely?
2. Should Cloud Function process BSON directly or act only as an orchestration trigger?
3. How should polymorphic fields be represented in BigQuery RAW?
4. How can source fidelity be preserved?
5. How should malformed records be isolated?
6. How should ingestion be made idempotent?
7. How should retries avoid duplicate loading?
8. How should processing progress be tracked?
9. How should schema drift be detected?
10. How should the pipeline support reprocessing?
11. What is the appropriate processing unit/chunk size?
12. What are the cost and operational implications of alternative GCP compute services?

These questions will be evaluated during DE-06 rather than assumed during local exploration.

---

# 28. Discovery conclusions

The Glamira source is an event-oriented BSON dataset with a common event envelope and event-specific payloads.

The most important findings from the local sample are:

1. `collection` behaves as the primary event-type discriminator.
2. 21 event types were observed.
3. All 50,000 sampled documents use `api_version = 1.0`.
4. Top-level `option` is polymorphic.
5. Much of the top-level `option` polymorphism is explained by event type.
6. `cart_products` introduces one-to-many nested product structures.
7. Products may themselves contain one-to-many options.
8. `cart_products[].option` may be either an array or an empty string.
9. All 11 observed string representations of nested product options are `""`.
10. `checkout` and `checkout_success` have different payload semantics.
11. `checkout.order_id` is empty in all 147 sampled checkout events.
12. `checkout_success.order_id` is populated but represented as both INT and DOUBLE.
13. `checkout_success` price is stored as a STRING.
14. Price formatting appears locale-dependent.
15. Currency is represented using symbols in observed records.
16. `show_recommendation` contains string booleans and NULL.
17. `recommendation` and `show_recommendation` should not be assumed equivalent.
18. Missing, NULL, empty, and invalid values must be treated separately.
19. Local MongoDB exploration is insufficient for production guarantees.
20. All important assumptions must be validated against the full dataset on GCP.

---

# 29. Status

```text
DE-05 — Local Data Discovery

05.1 BSON type discovery             DONE
05.2 Event taxonomy                  DONE
05.3 Event × schema analysis         DONE
05.4 Field presence by event         DONE
05.5 Nested payload inspection       DONE
05.6 Data quality hypotheses         DONE
05.7 Discovery documentation         DONE
```

Next task:

```text
DE-06 — GCS → BigQuery Ingestion POC
```