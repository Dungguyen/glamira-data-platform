# Glamira Scope Confirmation

## 1. Purpose

This document confirms the enrichment scope for the Glamira Data Engineering
project before cloud-scale implementation begins.

The scope decision focuses on two enrichment areas:

1. IP geolocation
2. Product metadata enrichment

The decisions are based on findings from the local 50,000-event discovery
sample.

> All sample-level measurements must later be validated against the full
> dataset.

---

## 2. IP Geolocation

### Sample evidence

The 50,000-event sample produced:

```text
Total events:             50,000
Events with IP:           50,000
IP coverage:              100%

Unique IP addresses:       7,334
Average events per IP:      6.82
Maximum events per IP:       238