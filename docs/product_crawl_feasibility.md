# Product Crawl Feasibility Assessment

## Objective

Validate whether Glamira product pages can be fetched from the
current GCP pipeline runtime before implementing a full crawler.

## Candidate Discovery

Product extraction produced:

- 19,558 unique product IDs
- 19,417 products with observed URLs
- 516,957 canonical product/URL pairs

Production URL profiling identified:

- 504,243 production URL pairs
- 12,714 non-production URL pairs
- 224 unique hosts

## URL Quality

Among production URL pairs:

- 462,433 HTML product candidates (91.71%)
- 41,337 checkout routes (8.20%)
- 473 other routes (0.09%)

Checkout and known non-product routes were excluded before sampling.

## Test Sample

A deterministic stratified sample was generated using:

- 10 production storefronts
- 10 unique products per storefront
- 100 total candidates
- random seed 42

## HTTP Probe

Five sequential product requests were executed from the GCP VM.

Results:

- 5/5 returned HTTP 403
- no redirects
- Content-Type: text/html
- response size approximately 398–422 bytes
- latency approximately 0.02–0.04 seconds

The response body contained:

`Access Denied`

and referenced an `errors.edgesuite.net` endpoint.

## Control Test

The storefront homepage was also requested from the same GCP VM.

Result:

- `https://www.glamira.de/` → HTTP 403

The same product URL was manually accessible through Chrome from
the local Windows environment.

## Interpretation

The current GCP automated HTTP execution environment cannot retrieve
the storefront HTML required by the crawler.

The available evidence does not establish which individual client or
network characteristic triggers the denial.

## Decision

**NO-GO for automated Glamira crawling from the current GCP runtime.**

Do not scale the crawler to 100 or full-product execution while the
source-access dependency remains unresolved.

## Next Step

Evaluate an approved product metadata source, such as:

- product catalog/export
- authorized API
- product feed
- internal product master
- explicitly authorized web access

The product identity dataset from Checkpoint #9 remains valid and can
be joined to a replacement product metadata source.