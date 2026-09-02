# Glamira IP Geolocation Report

## Scope

This checkpoint performs IP geolocation enrichment against the full Glamira
dataset.

The original MongoDB dataset contains:

`41,432,473` events.

IP enrichment is performed against distinct source IP values rather than
against every event.

This avoids redundant geolocation lookups.

---

## Unique IP Extraction

Full dataset results:

```text
Total unique source values: 3,239,628
Valid IP values:            3,239,627
Invalid values:                     1