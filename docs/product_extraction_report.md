# Glamira Product ID and URL Extraction Report

## Scope

This checkpoint extracts the complete observed product universe from the
full Glamira event dataset and derives canonical product-page URLs.

Full dataset:

`41,432,473` documents.

The core concept of this checkpoint is set deduplication.

---

## Product Identity Sources

Product identifiers were observed in three source structures.

### Top-level product_id

Examples include:

- `view_product_detail`
- `select_product_option`
- `select_product_option_quality`
- `add_to_cart_action`
- `view_all_recommend`
- `back_to_product_action`

### cart_products[].product_id

Observed in:

- `view_shopping_cart`
- `checkout`
- `checkout_success`

### recommendation_product_id

Observed in recommendation-related events.

The full product universe is defined conceptually as:

```text
top-level product_id
UNION
cart_products[].product_id
UNION
recommendation_product_id

Product Universe

Full extraction produced:

Unique product IDs:     19,558
Products with URL:      19,417
Products without URL:      141

High-confidence product-page event sources therefore cover approximately
99.28% of the observed product universe.

Products without an observed product-page URL are retained rather than
discarded.

Their URL status is:

NOT_OBSERVED

Product Occurrences

The full dataset contained:

Top-level product occurrences:        22,242,720
Cart product occurrences:                822,438
Recommendation product occurrences:      217,700

These values represent occurrences, not unique products.

Repeated occurrences are collapsed through set deduplication.

Trusted Product URL Sources

Product-page URLs are accepted only from event types where current_url
was observed to represent an actual product page:

view_product_detail
select_product_option
select_product_option_quality
add_to_cart_action

Other events may provide useful product identity but their current_url
is not automatically treated as a product-page URL.

For example, recommendation events may contain recommendation routes rather
than canonical product pages.

URL Canonicalization

Raw URLs contain large numbers of variants caused by:

product configuration parameters;
advertising tracking parameters;
recommendation parameters;
different storefronts;
localized product paths.

Canonicalization preserves:

scheme
hostname
path

and removes:

query string
fragment

Example:

RAW:
https://www.glamira.co.uk/glamira-ring-gratia.html
?alloy=red_white-585
&diamond=diamond-Brillant
&gclid=...

CANONICAL:
https://www.glamira.co.uk/glamira-ring-gratia.html

Different storefronts are intentionally preserved.

For example:

www.glamira.de
www.glamira.co.uk
www.glamira.fr

are not collapsed into one URL.

URL Extraction Results

Full processing results:

Trusted URL observations:       22,208,495
Canonical URL observations:     22,207,472
Invalid URL observations:            1,023

Unique product/canonical URL
pairs:                              516,957

The invalid URL observation rate is approximately 0.0046%.

Output Grain

Two derived datasets are produced.

Product set

Grain:

1 row = 1 unique product_id

Fields:

product_id
url_count
url_status
Product URL set

Grain:

1 row = 1 product_id + canonical_url

Fields:

product_id
canonical_url
storefront_host
url_status

A product may have multiple canonical URLs because Glamira operates multiple
localized storefronts.

Validation

Discovery queries previously identified:

Expected unique products: 19,558
Expected products without high-confidence URL: 141

The full Python extraction produced:

Unique products:          19,558
Products without URL:        141
Product universe match:      True

The independent discovery and extraction results reconcile exactly.

Performance

The complete scan processed:

41,432,473 documents.

Elapsed time:

approximately 8.09 minutes.

The extraction uses:

MongoDB field projection;
streaming cursor processing;
normalized product identities;
Python hash sets for deduplication;
URL canonicalization.

Async processing was not required because the workload is primarily a local
MongoDB scan and in-memory normalization rather than high-latency network I/O.

Crawl Consideration

The canonical URL set contains both production and non-production hosts.

For example:

www.glamira.*
stage.glamira.de

Canonical URL does not automatically imply that a URL should be selected for
production crawling.

Crawl eligibility and storefront selection must therefore be defined before
the next checkpoint.

Data Handling

The generated product datasets are derived data artifacts and are not
committed to GitHub.

Repository artifacts should contain:

reusable extraction code;
aggregate metrics;
documentation.
Checkpoint Result
