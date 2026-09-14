# Data Quality Notes

Last reviewed: 2026-09-14

This document records known data-quality limitations in the Glamira
analytics dataset and distinguishes accepted source limitations from
transformation failures.

The values below represent the current development baseline for
`fact_sales_order_detail`.

## Current baseline

| Metric | Current value | Rate | Quality contract |
|---|---:|---:|---:|
| Fact rows | 34,916 | 100% | Reference baseline |
| Missing currency | 1,085 | 3.1075% | <= 5.00% |
| Missing unit price | 1 | 0.0029% | Included in missing-price threshold |
| Missing line amount | 1 | 0.0029% | Included in missing-price threshold |
| Unknown customer | 11,681 | 33.4546% | Observational only |
| Unknown product | 6,805 | 19.4896% | <= 25.00% |
| Unknown geography | 17 | 0.0487% | <= 0.10% |
| Unknown date | 0 | 0% | Must remain 0 |
| Unknown store | 0 | 0% | Must remain 0 |
| Unknown device | 0 | 0% | Must remain 0 |
| Non-positive quantity | 0 | 0% | Must remain 0 |
| Quantity greater than 10 | 15 | 0.0430% | <= 0.10% |
| Inconsistent line amount | 0 | 0% | Must remain 0 |

## Missing currency

Some successful checkout lines do not contain a usable currency value.

Current baseline:

- 1,085 rows
- 3.1075% of fact rows
- Maximum accepted rate: 5.00%

These records are retained because the absence of currency does not invalidate
the successful checkout itself.

A rate above the accepted threshold is treated as a data-quality regression.

## Missing price information

One fact row currently has an unresolved unit price and line amount.

The row is preserved rather than removed because dropping it would alter the
business grain and checkout history.

The automated quality test monitors the combined rate of missing unit price
or line amount and fails if it exceeds 0.01%.

## Unknown customer

11,681 fact rows currently map to the Unknown Customer member.

Unknown Customer is an accepted business state. It represents checkout lines
where a registered customer identifier cannot be resolved.

This condition is observational and is not treated as a transformation
failure.

Raw customer identifiers and direct PII are not exposed in the mart layer.
Registered customer identifiers are represented using the pseudonymized
`customer_id_hash` in `dim_customer`.

## Unknown product

6,805 fact rows currently map to the Unknown Product member.

This represents 19.4896% of fact rows and reflects incomplete product-master
coverage rather than a failed sales transformation.

The source `product_id` is retained in the fact table for traceability while
the dimensional foreign key maps unresolved products to the Unknown Product
member.

Maximum accepted unknown-product rate: 25.00%.

A higher rate indicates a possible product-master coverage regression or
upstream enrichment problem.

## Unknown geography

17 fact rows currently map to the Unknown Geography member.

This represents 0.0487% of fact rows.

Possible causes include addresses that cannot be resolved by the GeoIP source
or addresses without sufficient geographic attributes.

Maximum accepted unknown-geography rate: 0.10%.

## High quantities

15 fact rows currently have a quantity greater than 10.

These values are retained because high quantities are not automatically
invalid business transactions.

Current rate: 0.0430%.

Maximum accepted rate: 0.10%.

Non-positive quantities are not accepted and must remain at zero rows.

## Hard quality contracts

The following conditions are considered transformation or dimensional
integrity failures and must always remain at zero:

- Non-positive quantity.
- Inconsistent line amount relative to unit price multiplied by quantity.
- Unknown Date foreign key.
- Unknown Store foreign key.
- Unknown Device foreign key.

Violations of these rules fail the dbt quality tests.

## Automated monitoring

Known quality conditions are enforced by:

- `tests/quality/test_fact_hard_quality_contracts.sql`
- `tests/quality/test_fact_quality_thresholds.sql`

Hard contracts fail when any violating row exists.

Tolerated source limitations fail only when their configured rate exceeds the
accepted threshold.

This approach allows known source-data imperfections to remain visible without
silently accepting material regressions.