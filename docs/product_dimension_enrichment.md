# Product Dimension Enrichment

## Objective

Build an analytical product dimension while preserving the complete
validated product universe.

## Grain

One row represents one unique `product_id`.

## Source datasets

- Product universe: 19,558 products
- Successful product enrichment: 18,648 products

## Results

- Total dimension rows: 19,558
- Unique product IDs: 19,558
- Duplicate product IDs: 0
- Enriched products: 18,648
- Not enriched products: 910
- Enrichment coverage: 95.35%
- Product accounting coverage: 100%

Products that could not be enriched are retained in the dimension with
`NOT_ENRICHED` status rather than being dropped.

## Data quality

- No duplicate product IDs
- No duplicate SKUs among enriched products
- No crawl host mismatches
- No representative host mismatches
- No invalid image URLs
- Enriched records contain product name, SKU, category, image and
  description.

## Known limitations

The category attribute is extracted from localized storefront HTML.

Semantic profiling identified cases where the final breadcrumb value
corresponds to the product name instead of a true product category.

The raw category value is retained for lineage. Category should not yet
be treated as a canonical analytical taxonomy.

Category normalization is intentionally deferred to a later modeling
step.

Product enrichment was stopped after diminishing returns were observed.
Approximately 1,000 additional crawl attempts produced only a very small
number of newly enriched products.

The remaining 910 products are preserved as `NOT_ENRICHED`.

## Decision

PASS_WITH_ACCEPTED_LIMITATION