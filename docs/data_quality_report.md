# Glamira Data Quality Assessment

## 1. Scope

This report documents the initial data quality assessment performed on a
50,000-document sample extracted from the Glamira raw BSON dataset.

The purpose of this assessment is to understand the source data before
implementing full-scale processing and transformation pipelines.

The assessment focuses on:

- completeness
- uniqueness
- type consistency
- value validity
- cross-field consistency
- encoding quality

> **Important:** All findings in this report are based on the 50,000-document
> local sample and must be revalidated against the full dataset during
> full-scale processing.

No source records were modified or removed during this assessment.

---

## 2. Dataset Overview

### Source

The original source is a BSON dataset containing Glamira web/e-commerce
behavioral events.

The local MongoDB collection used for exploration is:

```text
Database: glamira
Collection: summary_sample
Sample size: 50,000 documents
API version observed: 1.0
```

MongoDB is used only as a local exploration environment for understanding
the sample.

Full-scale data processing will be performed on GCP rather than using the
local MongoDB instance as the production processing platform.

### Event model

The field `collection` represents the event type.

The sample contains 21 observed event types.

Major event types include:

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

Several low-frequency recommendation and sorting events are also present.

The dataset therefore follows a heterogeneous event model rather than a
single uniform document schema.

---

## 3. Methodology

Data quality checks were performed against the 50,000-document sample using
MongoDB aggregation queries and targeted manual inspection.

The following dimensions were evaluated:

1. Completeness
2. Uniqueness
3. Type consistency
4. Validity
5. Cross-field consistency
6. Encoding screening

The analysis follows a schema-on-read approach.

Fields are interpreted in the context of their event type instead of assuming
that every event must contain the same fields.

---

## 4. Completeness

Missing, null, and empty values were analyzed separately.

These states have different meanings:

```text
missing -> field does not exist
null    -> field exists with null value
empty   -> field exists but contains an empty string
```

### Core fields

The following results were observed across the 50,000-document sample:

```text
Missing _id:          0
Null _id:             0

Missing collection:   0
Null collection:      0
```

Therefore, both document identity and event type were present across the
entire sample.

### User identity fields

`user_id_db` and `email_address` contain a high percentage of empty values
for many event types.

Examples include:

| Event type | Empty/problem % |
|---|---:|
| view_listing_page | 97.31% |
| product_detail_recommendation_noticed | 95.60% |
| view_product_detail | 95.36% |
| view_landing_page | 95.24% |
| product_detail_recommendation_visible | 94.97% |
| product_detail_recommendation_clicked | 94.93% |
| select_product_option | 94.63% |
| select_product_option_quality | 93.94% |
| search_box_action | 88.19% |
| add_to_cart_action | 84.81% |
| view_home_page | 82.76% |

These values should not automatically be classified as data loss.

They may reflect anonymous browsing behavior because the same pattern is
observed consistently across both identity-related fields.

### Recommendation fields

`show_recommendation` also contains null values depending on event type.

For example:

```text
view_product_detail:
null = 7,099 / 14,011
     = 50.67%
```

This suggests that completeness requirements must be defined per event type
and field semantics rather than globally.

### Conclusion

**Status: EVENT-DEPENDENT**

High null or empty percentages are not sufficient evidence of bad data.

Completeness rules for the production pipeline should be event-aware.

---

## 5. Uniqueness

An initial duplicate-candidate analysis was performed using the following
fingerprint:

```text
time_stamp
collection
user_id_db
device_id
product_id
current_url
```

Results:

```text
Candidate duplicate groups:          140
Documents in candidate groups:       282
Candidate extra documents:           142
Candidate duplicate rate:          0.28%
```

The 0.28% value must **not** be interpreted as the confirmed duplicate rate.

### Manual inspection

Several candidate groups contained records with identical values for the
fingerprint fields and identical observed payloads.

Examples included:

- `view_landing_page`
- `view_product_detail`
- `view_listing_page`
- `view_static_page`

These are strong duplicate candidates.

However, a false-positive case was identified for:

```text
select_product_option_quality
```

Two events shared the same initial fingerprint but contained different
business payload:

```text
Event 1:
quality       = AAA
quality_label = VS

Event 2:
quality       = AA
quality_label = SI
```

These represent different product-option selections and must not be removed
as duplicates.

### Conclusion

**Status: INVESTIGATION REQUIRED**

The initial fingerprint is insufficient for safe deduplication.

Deduplication should be event-aware and should incorporate event-specific
payload when required.

No records should be removed during the discovery phase.

---

## 6. Type Consistency

The sample contains several fields with multiple observed BSON types.

### option

Observed distribution:

```text
array   = 27,366
object  = 12,816
missing =  9,818
```

Further analysis showed that the type is strongly associated with event type.

Examples:

```text
view_product_detail            -> array
select_product_option          -> array
select_product_option_quality  -> array
add_to_cart_action             -> array

view_listing_page              -> object
```

Therefore, `option` should be considered an **event-dependent polymorphic
field**, not automatically classified as schema corruption.

### order_id

Observed BSON types:

```text
missing = 49,803
string  =    147
int     =     33
double  =     17
```

Previous event-level inspection showed:

```text
checkout
    -> order_id = ""

checkout_success
    -> order_id populated with numeric values
```

This indicates a lifecycle-dependent representation.

The mixed `int` and `double` representation of populated identifiers should
be normalized before analytical use.

### utm_source

Observed types:

```text
missing = 35,989
bool    = 13,731
string  =    280
```

### utm_medium

Observed types:

```text
missing = 35,989
bool    = 13,726
string  =    285
```

The boolean/string representation requires further semantic validation.

A possible explanation is that boolean `false` represents absence of UTM
attribution while strings contain actual attribution values.

This remains a hypothesis and should not be treated as a confirmed business
rule without further evidence.

### Other polymorphic/nullable fields

Additional fields with multiple observed representations include:

```text
show_recommendation
cat_id
recommendation_product_id
recommendation_clicked_position
price
currency
is_paypal
key_search
```

Many of these differences involve `null` versus populated values and may be
valid event-specific behavior.

### Conclusion

**Status: NORMALIZATION REQUIRED**

The source schema is heterogeneous and should not be forced into a single
uniform raw schema.

Normalization should be performed according to event semantics.

---

## 7. Validity

### Timestamp

Observed range:

```text
Minimum Unix timestamp:
1591259987
2020-06-04T08:39:47Z

Maximum Unix timestamp:
1591266092
2020-06-04T10:21:32Z
```

The observed values are consistent with Unix timestamps expressed in seconds.

The 50,000-document sample covers approximately 1 hour and 42 minutes.

This also means the sample should not be assumed to represent the temporal
distribution of the complete dataset.

**Status: PASS — sample level**

### Resolution

Results:

```text
Total:           50,000
Missing:              0
Empty:                0
Invalid format:       0
```

All observed values matched the basic pattern:

```text
<number>x<number>
```

Example:

```text
1366x768
```

This validates syntax only. It does not guarantee that every width and height
represents a realistic screen resolution.

**Status: PASS — format level**

### Price

There were 232 string-valued prices.

Observed simple format classification:

```text
Dot decimal:       46
Comma decimal:    113
Other format:      73
Total:            232
```

The source therefore contains locale-dependent price representations.

Examples observed during exploration include:

```text
880.00
343,00
55,00
```

The 73 values classified as `other_format` must not automatically be treated
as invalid. They only failed the two simple decimal regex patterns used by
the profiling query.

They may contain valid locale-specific formatting such as thousands
separators.

**Status: NORMALIZATION REQUIRED**

### Currency

Multiple currency representations were observed.

Examples include:

```text
€
£
kr
Ft
$
AU $
zł
SGD $
RON
₺
лв
₱
Kč
CAD $
CHF
HKD $
CHF '
ZAR
CLP
kn
```

The source mixes:

- currency symbols
- local abbreviations
- ISO-like codes
- code + symbol representations

Some symbols are ambiguous without market context.

For example:

```text
$
kr
```

should not be mapped to a canonical currency using the symbol alone.

Currency normalization should use additional context such as:

```text
store_id
current_url/domain
market/locale
```

where available.

A future normalized representation should preferably use an ISO 4217
currency code while preserving the original source value.

Example:

```text
currency_raw  = "€"
currency_code = "EUR"
```

**Status: NORMALIZATION REQUIRED**

---

## 8. Cross-field Consistency

The relationship between:

```text
user_id_db
email_address
```

was tested.

Results:

```text
both_empty       = 46,470
both_populated   =  3,530
user_only        =      0
email_only       =      0
```

Percentages:

```text
both_empty       = 92.94%
both_populated   =  7.06%
inconsistent     =  0.00%
```

Within the sample, the two fields exhibit perfect observed presence
consistency.

This supports the hypothesis that the fields are related to the same user
identity state.

However, the data alone does not prove that user authentication is the
business cause of this relationship.

**Status: PASS — sample level**

---

## 9. Encoding Screening

A targeted screening was performed for common mojibake/corrupted text
patterns.

Results:

```text
Suspicious encoding matches: 0 / 50,000
```

Unicode values such as:

```text
Weißgold
€
zł
₺
лв
Kč
```

are valid multilingual text and should not be classified as encoding errors.

The screening covered selected string fields and common corruption markers.
It does not prove that every string field in the complete dataset is free
from encoding problems.

**Status: PASS — targeted sample screening**

---

## 10. Key Data Quality Findings

The main findings from the sample are:

### 1. The dataset is event-oriented

Different values of `collection` represent different event types with
different payload structures.

A single rigid schema should not be assumed for all events.

### 2. Missing values are frequently semantic

Many fields are absent, null, or empty because they are not applicable to a
particular event or user state.

Global completeness rules would therefore produce misleading DQ results.

### 3. Nested structures are polymorphic

`option` is represented as both an object and an array depending on event
type.

This behavior appears systematic rather than random.

### 4. Naive deduplication is unsafe

The initial fingerprint produced a 0.28% candidate duplicate rate, but manual
inspection identified at least one false-positive group containing distinct
business actions.

Deduplication must therefore be event-aware.

### 5. Monetary fields require normalization

`price` contains locale-dependent number formats.

`currency` contains heterogeneous symbols and codes.

These fields require contextual normalization before analytical use.

### 6. Some source fields use heterogeneous representations

Examples include:

```text
utm_source
utm_medium
order_id
show_recommendation
option
```

Canonical representations should be defined in downstream normalized layers.

---

## 11. Risks for Full-scale Processing

The following risks should be considered before processing the complete
dataset.

### Schema assumptions

A pipeline that assumes a single schema may fail when encountering
event-specific structures.

### Unsafe deduplication

A global duplicate fingerprint may remove valid user interactions.

### Monetary parsing

Naive numeric conversion may incorrectly parse locale-specific prices.

### Currency ambiguity

Currency symbols cannot always be converted to ISO codes without additional
market context.

### Type coercion

Automatic coercion may destroy source semantics for polymorphic fields.

### Sample bias

The 50,000-document sample covers only a small temporal range and may not
contain all schemas, event types, values, or historical schema changes
present in the full dataset.

---

## 12. Recommended Normalization Strategy

The raw source should be preserved before normalization.

A recommended conceptual flow is:

```text
Raw BSON
   |
   v
Bronze
- preserve source records
- preserve raw field values
- retain event metadata
   |
   v
Silver
- event-aware schema handling
- canonical data types
- null/empty normalization
- option normalization
- price normalization
- currency normalization
- event-aware deduplication
   |
   v
Gold
- analytics-ready business models
- behavioral funnels
- product analytics
- sales analytics
- marketing attribution
```

Raw values should be retained where normalization could lose source
information.

For example:

```text
price_raw
price_amount

currency_raw
currency_code
```

---

## 13. Limitations

This assessment has several important limitations.

### Sample size

Only 50,000 documents were analyzed locally.

Findings must be validated against the full dataset.

### Temporal coverage

The sample covers approximately 1 hour and 42 minutes of observed event
timestamps.

Historical schema changes may therefore not appear in this sample.

### API version coverage

Only API version `1.0` was observed in the sample.

No conclusion can currently be made about schema evolution across API
versions.

### Duplicate detection

Duplicate analysis used an initial heuristic fingerprint.

The resulting candidate duplicate rate is not a confirmed duplicate rate.

### Encoding validation

Encoding screening covered selected fields and common mojibake patterns
rather than performing exhaustive validation of every nested string.

### Business semantics

Some interpretations remain hypotheses until validated against source-system
documentation or additional data.

Examples include:

- meaning of boolean UTM values
- user identity semantics
- exact recommendation semantics
- canonical currency mapping

---

## 14. Conclusion

The 50,000-document Glamira sample does not indicate widespread structural
corruption.

Instead, the primary challenge is **heterogeneous event semantics and
representation**.

The most important engineering implications are:

1. use schema-on-read during discovery;
2. preserve raw source data;
3. apply event-aware normalization;
4. avoid global deduplication rules;
5. normalize monetary values using locale/market context;
6. distinguish missing, null, and empty values;
7. validate sample-derived assumptions against the full dataset.

The dataset is suitable for continued pipeline development, provided that
these characteristics are explicitly handled in downstream processing.

**Overall assessment: PROCEED WITH EVENT-AWARE NORMALIZATION AND FULL-DATA
VALIDATION.**