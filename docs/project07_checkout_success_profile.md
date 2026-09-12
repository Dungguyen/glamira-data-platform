# Project 07 — Checkout Success Profiling

## 1. Objective

Profile the `checkout_success` event from `raw.events` before designing the dimensional model and `fact_sales_order_detail`.

The goals are to determine:

- checkout event structure;
- order identifier;
- product nesting;
- quantity, price, and currency location;
- customer, GeoIP, and product join candidates;
- duplicate behavior;
- exact fact grain.

---

## 2. Checkout Success Volume

The raw dataset contains:

- Raw `checkout_success` events: **26,079**
- Distinct `order_id`: **26,031**

The difference initially indicated **48 extra event rows**, but further profiling showed that not all repeated `order_id` values are true duplicates.

---

## 3. Top-Level Fields

The `checkout_success` payload contains the following top-level fields:

- `_id`
- `api_version`
- `cart_products`
- `collection`
- `current_url`
- `device_id`
- `email_address`
- `ip`
- `local_time`
- `order_id`
- `referrer_url`
- `resolution`
- `show_recommendation`
- `store_id`
- `time_stamp`
- `user_agent`
- `user_id_db`

`_id.$oid` is a nested value inside `_id`, not a separate top-level field.

---

## 4. Order Identifier

The source order identifier is:

`order_id`

However, profiling proved that `order_id` is **not globally unique enough to be used alone as the business transaction key**.

There are:

- **30 duplicated `order_id` values**
- **78 events** within those duplicate groups
- **48 extra event rows**
- Maximum observed repetition: **17 events for one `order_id`**

---

## 5. Product Structure

Products are not stored at the payload top level.

They are nested inside:

`cart_products[]`

Each cart product contains fields such as:

- `product_id`
- `amount`
- `price`
- `currency`
- `option`

Therefore, `cart_products` must be unnested before building the sales-order-detail fact.

---

## 6. Products per Checkout

A successful checkout may contain one or multiple products.

Observed cart sizes range from **1 to 10 products**.

Distribution includes:

- 1 product: 18,703 checkout events
- 2 products: 6,032
- 3 products: 1,160
- 4 products: 136
- 5 products: 30
- 6 products: 12
- 7 products: 2
- 8 products: 1
- 10 products: 3

Before deduplication, unnesting `cart_products` produces:

**35,065 raw product-line rows**

---

## 7. Quantity, Price, and Currency

Line-item measures are located inside each `cart_products[]` element:

- Quantity: `amount`
- Price: `price`
- Currency: `currency`

Across the 35,065 raw cart-product lines:

- NULL `product_id`: 0
- NULL `amount`: 0
- NULL `price`: 0
- NULL `currency`: 0

Price requires normalization because multiple locale formats exist, for example:

- `331.00`
- `754,00`
- `1,725.00`
- `4.990,00`

Therefore, `price` cannot be directly cast to a numeric type without locale-aware transformation.

Revenue must also not be aggregated across currencies without an explicit currency-conversion strategy.

---

## 8. Customer Identifier

The source customer identifier candidate is:

`user_id_db`

Some events contain an empty string instead of a customer ID.

The staging layer should normalize:

`'' -> NULL`

`email_address` should not be used as the warehouse business key because it is personally identifiable information.

---

## 9. GeoIP Join

Checkout events contain the top-level field:

`ip`

This allows a candidate join:

`checkout_success.ip -> geoip.ip`

The actual join coverage should be measured during staging/model validation.

---

## 10. Product Join

After unnesting `cart_products`, the source product identifier is:

`cart_products[].product_id`

Candidate join:

`cart_products[].product_id -> products.product_id`

A LEFT JOIN should be preferred because the product reference dataset contains only successfully enriched products, so unmatched product IDs may exist.

---

## 11. Option Schema Drift

`cart_products[].option` does not have one stable JSON type.

Observed line counts:

- ARRAY: **27,354**
- STRING: **7,711**

The staging layer must therefore explicitly normalize this schema drift.

---

## 12. Duplicate Order Profiling

The 30 repeated `order_id` values were profiled using:

- cart content;
- customer ID;
- store ID;
- IP address;
- timestamps.

Results:

- `SAME_BUSINESS_ORDER`: **16 order IDs**
- Extra events belonging to this class: **34**
- `BUSINESS_DIFFERENCE_FOUND`: **14 order IDs**
- Additional events belonging to this class: **14**

The second group must not be removed merely because its `order_id` repeats.

Several repeated order IDs have:

- different cart contents;
- different customers;
- different IP addresses;
- timestamps separated by days or weeks.

This demonstrates that `order_id` alone is not a sufficiently reliable deduplication key.

---

## 13. Deduplication Rule

Confirmed tracking duplicates are identified using the business-event identity:

`order_id + store_id + cart_hash`

Where `cart_hash` is derived from the complete `cart_products` structure.

For repeated events with the same business identity, retain the earliest event using:

`event_timestamp_raw ASC, event_id ASC`

Conceptually:

ROW_NUMBER() OVER (
    PARTITION BY
        order_id,
        store_id,
        cart_hash
    ORDER BY
        event_timestamp_raw,
        event_id
)

Keep only:

`event_rank = 1`

Customer ID is not included in the deduplication key because it may be missing.

IP address is not used as a transaction identifier because network information may change independently of the business transaction.

---

## 14. Final Reconciliation

Final profiling produced:

| Metric | Count |
|---|---:|
| Raw checkout events | 26,079 |
| Deduplicated business checkout instances | 26,045 |
| Confirmed tracking events removed | 34 |
| Raw product-line rows | 35,065 |
| Final fact candidate rows | 35,019 |

Therefore:

- **34 duplicate checkout events** are removed.
- These duplicate events represent **46 duplicated product-line rows**.
- **14 legitimate checkout instances with reused `order_id` values are preserved.**

Reconciliation:

`26,079 - 34 = 26,045 business checkout instances`

and:

`35,065 - 46 = 35,019 fact candidate rows`

---

## 15. Final Fact Grain

The final grain of `fact_sales_order_detail` is:

> **One row per product line within one deduplicated successful checkout instance.**

A successful checkout instance is identified using the deduplicated business-event identity rather than `order_id` alone.

Therefore, the fact grain is NOT:

> One row per checkout event.

It is also NOT:

> One row per `order_id`.

Instead:

`checkout_success`
→ deduplicate business checkout instance
→ unnest `cart_products[]`
→ one fact row per product line

Expected candidate fact volume:

**35,019 rows**

---

## 16. Checkpoint Result

**Checkpoint 7.2 — PASS**

The source event structure, duplicate behavior, dimensional join candidates, and exact fact grain have been established using profiling evidence.

The project can now proceed to dimensional-model design and dbt staging implementation.