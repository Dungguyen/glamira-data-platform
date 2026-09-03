# Product Metadata Source Decision

## Objective

Select an appropriate source for authoritative Glamira product metadata.

The existing event dataset provides product identity and behavioral context,
but the pipeline requires a reliable product metadata source for a future
product dimension.

---

## Sources Evaluated

### 1. Existing Glamira Event BSON

Available data includes:

- `product_id`
- observed product URLs
- `option_label`
- `option_id`
- `value_id`
- event and interaction context

The event source does not provide sufficient evidence for authoritative
product master attributes such as:

- product name
- SKU
- authoritative category
- description
- image
- authoritative product price
- human-readable option value dictionary

The relationship between internal `value_id` and URL option values was also
found to be non-deterministic.

**Decision: FALLBACK / SUPPLEMENTAL SOURCE**

The BSON event data remains useful for product identity, behavior analytics,
observed URLs, and option-level event data.

---

### 2. Public Website Crawling

A deterministic crawl sample was prepared from production Glamira storefronts.

HTTP requests from the current GCP Compute Engine runtime returned:

- HTTP 403 for product pages
- HTTP 403 for the storefront homepage
- an `Access Denied` response from the edge layer

The same product URL was accessible manually from a local Chrome browser.

The available evidence therefore establishes that the current GCP automated
HTTP runtime cannot retrieve the product HTML required for crawling.

**Decision: NO-GO FOR CURRENT GCP RUNTIME**

The crawler should not be scaled or modified to bypass source access controls.

---

### 3. Internal Product Catalog

An internal product master/catalog would be the preferred source because it
would normally provide authoritative product identity and descriptive
attributes.

Expected attributes may include:

- product_id
- SKU
- product name
- category
- product attributes
- price
- images
- availability

Availability of such a catalog has not yet been confirmed.

**Decision: PREFERRED IF AVAILABLE**

---

### 4. Official API / Feed / Export

An authorized product API, catalog feed, or export would also be suitable for
building the product dimension.

Advantages include:

- authoritative source
- structured schema
- better stability than HTML scraping
- easier incremental synchronization
- lower parser maintenance

Availability has not yet been confirmed.

**Decision: PREFERRED IF AVAILABLE**

---

### 5. External or Project-Provided Product Dataset

Any project-provided product master dataset should be evaluated for:

- coverage
- freshness
- schema quality
- product_id compatibility
- source authority

**Decision: EVALUATE IF AVAILABLE**

---

## Decision Matrix

| Source | Authority | Coverage | Accessibility | Stability | Decision |
|---|---|---|---|---|---|
| Event BSON | Medium for behavior, low for product master | Partial | Available | High | FALLBACK |
| Public web crawl from current GCP runtime | Medium | Potentially high | Blocked | Low | NO-GO |
| Internal product catalog | High | Expected high | Unknown | High | PREFERRED |
| Official API/feed/export | High | Expected high | Unknown | High | PREFERRED |
| External project dataset | Depends | Depends | Unknown | Depends | EVALUATE |

---

## Architecture Decision

Preferred product metadata source:

1. Internal product catalog
2. Official API / feed / export
3. Validated external product master dataset

Fallback:

Existing event BSON for:

- product identity
- observed product URLs
- option-level event data
- behavioral analytics

Rejected for the current runtime:

Automated public website crawling from GCP.

---

## Impact on Roadmap

Checkpoint #10 demonstrated that the web crawl path is currently blocked by a
source-access dependency.

Checkpoint #11 should therefore not proceed as a full website crawl until an
authorized and technically accessible product metadata source is available.

The product identity dataset from Checkpoint #9 remains valid and reusable.

---

## Decision

**NO-GO for public web crawling from the current GCP runtime.**

**GO for product enrichment once an authoritative structured source is
identified.**