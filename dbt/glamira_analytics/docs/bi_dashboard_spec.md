# Glamira BI Dashboard Specification

Last reviewed: 2026-09-14

## 1. Purpose

The Glamira BI dashboard provides analytical visibility into successful
checkout activity produced by the dbt dimensional mart.

The dashboard is designed for business analysis rather than operational
transaction processing.

## 2. Analytical source

Primary fact:

`fact_sales_order_detail`

Fact grain:

One product line within one deduplicated successful checkout.

Dimensions:

- `dim_date`
- `dim_customer`
- `dim_product`
- `dim_store`
- `dim_device`
- `dim_geo`

## 3. Business interpretation

A successful checkout event represents a checkout observed by the tracking
dataset.

It should not automatically be interpreted as a confirmed payment, fulfilled
order, or recognized accounting revenue unless additional source data proves
those states.

## 4. KPI definitions

### Successful Checkouts

Number of distinct deduplicated checkout instances.

Formula:

`COUNT(DISTINCT checkout_instance_key)`

### Product Lines

Number of product-line records in the sales fact.

Formula:

`COUNT(*)`

### Units

Total product quantity represented by checkout lines.

Formula:

`SUM(quantity)`

### Distinct Products

Number of distinct source products appearing in successful checkout activity.

Formula:

`COUNT(DISTINCT product_id)`

### Sales Amount

Sum of `line_amount_local`.

Sales amount must be analyzed within a consistent currency.

Amounts from different currencies must not be aggregated into a single global
sales value without an explicit FX normalization model.

## 5. Initial dashboard views

### Executive Overview

- Successful checkouts
- Product lines
- Units
- Sales amount by currency
- Checkout trend by date
- Sales trend by date

### Product Performance

- Products by checkout activity
- Products by units
- Products by sales amount within currency
- Product category performance
- Unknown Product coverage

### Customer Analysis

- Registered versus Unknown Customer activity
- Distinct registered customers
- Checkout activity by customer type

Raw customer identifiers and direct PII must not be exposed.

### Geographic Analysis

- Checkout activity by country
- Checkout activity by region
- Checkout activity by city
- Unknown Geography coverage

### Store Analysis

- Checkout activity by store
- Sales amount by store and currency
- Product activity by store

### Device Analysis

- Checkout activity by device type
- Desktop / Mobile / Tablet distribution
- Screen-resolution analysis

## 6. Security requirements

The dashboard must query the mart layer only.

Staging and core datasets must not be used as BI data sources.

The dashboard must not expose:

- email address
- IP address
- device identifier
- user agent
- raw customer identifier
- current URL
- referrer URL

## 7. Data-quality considerations

Known data-quality limitations are documented in:

`docs/data_quality.md`

Dashboard metrics must preserve Unknown dimension members rather than silently
dropping them.

## Revenue and Currency Policy

`line_amount_local` represents monetary value in the local currency associated
with a storefront.

The analytical dataset is multi-currency. Monetary amounts from different
currencies must not be aggregated into a single global revenue metric.

### Store-level currency behavior

Profiling confirms that every store with an available currency uses exactly
one currency symbol in the current dataset.

Therefore, Sales Amount may be aggregated when the analytical context retains:

- `store_id`
- `store_domain`
- `currency_symbol`

`store_id` is the authoritative store identifier. `store_domain` is a display
attribute and must not be treated as a unique store key because multiple
store IDs can share the same domain.

### Missing currency

Three storefronts currently have no currency value:

- store 51 — `www.glamira.ro`
- store 63 — `www.glamira.ae`
- store 79 — `www.glamira.co.za`

Together they account for all 1,085 fact rows with missing currency.

These rows must remain visible as an Unknown / Missing Currency category and
must not be silently excluded from checkout, product-line, or unit metrics.

Monetary values for these stores must not be presented as a currency-specific
revenue KPI because the source currency is unresolved.

### Global revenue

A global revenue metric is intentionally not supported.

Cross-currency monetary comparison requires an explicit FX-rate dataset,
conversion date policy, target reporting currency, and reproducible conversion
logic.

Until such a model exists, the dashboard reports local sales amount only
within a Store + Currency context.

### Sales Amount Local

Sum of `line_amount_local` within a consistent Store + Currency context.

Formula:

`SUM(line_amount_local)`

Required grouping or filter context:

- Store
- Currency

This metric must not be aggregated across different currencies.

## Quantity Anomaly Policy

The source dataset contains legitimate-looking checkout records with unusually
high product quantities.

A notable example occurs on 2020-04-09, where one sales line contains a
quantity of 9,999. This single row increases daily units from 504 to 10,503
and also materially affects the associated local sales amount.

These records are retained because there is currently no authoritative
business rule proving that quantities above 10 are invalid.

The dashboard must therefore:

- preserve Raw Units as the source-faithful metric;
- expose High Quantity Lines as a data-quality indicator;
- avoid silently excluding high-quantity records;
- avoid presenting an adjusted Units or Sales metric as authoritative unless
  a documented business rule is introduced.

High Quantity is currently defined for monitoring as `quantity > 10`.