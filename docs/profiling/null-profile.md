# Glamira Null and Completeness Profile

## Scope

This profiling was performed against the local MongoDB sample containing
50,000 Glamira events.

The purpose of this checkpoint is to measure data completeness by event type.

This is a sample-level discovery result and must not be interpreted as a
guarantee for the full dataset.

---

## Dataset summary

- Documents: 50,000
- Event types: 21
- Missing `_id`: 0
- NULL `_id`: 0
- Missing `collection`: 0
- NULL `collection`: 0

The core document identifier and event discriminator were complete in the
sample.

---

## Missing-value definitions

The profiling distinguishes three source states:

- `missing`: field does not exist in the BSON document
- `null`: field exists with BSON NULL
- `empty`: field exists as a string with value `""`

These states must not automatically be treated as semantically equivalent.

---

## User identity fields

High empty-string rates were observed for `user_id_db` and `email_address`.

Examples:

| Event type | user_id_db empty % | email_address empty % |
|---|---:|---:|
| view_listing_page | 97.31 | 97.31 |
| view_product_detail | 95.36 | 95.36 |
| view_landing_page | 95.24 | 95.24 |
| select_product_option | 94.63 | 94.63 |
| add_to_cart_action | 84.81 | 84.81 |
| view_home_page | 82.76 | 82.76 |

The observed absence is represented primarily as empty strings rather than
missing fields or BSON NULL.

### Interpretation

This may represent anonymous/non-authenticated traffic rather than corrupted
data.

Business/source-system validation is required before treating these values as
data-quality failures.

### Hypothesis

`user_id_db` and `email_address` appear to have matching empty-value counts in
the inspected event types.

They may be populated together when user identity is known.

This relationship has not yet been validated at document level.

---

## show_recommendation

Significant NULL rates were observed.

Examples:

| Event type | NULL count | Total | NULL % |
|---|---:|---:|---:|
| view_product_detail | 7,099 | 14,011 | 50.67 |
| listing_page_recommendation_visible | 3 | 10 | 30.00 |
| product_detail_recommendation_visible | 419 | 1,987 | 21.09 |
| select_product_option_quality | 592 | 3,119 | 18.98 |
| product_detail_recommendation_clicked | 26 | 138 | 18.84 |
| select_product_option | 1,871 | 9,999 | 18.71 |
| product_detail_recommendation_noticed | 126 | 727 | 17.33 |

Previous discovery also identified string values `"true"` and `"false"`.

Therefore NULL must not automatically be classified as invalid.

The business semantics of `show_recommendation` require further validation.

---

## referrer_url

Empty `referrer_url` values were observed across several event types.

Examples:

| Event type | Empty count | Total | Empty % |
|---|---:|---:|---:|
| view_home_page | 493 | 1,566 | 31.48 |
| product_detail_recommendation_noticed | 123 | 727 | 16.92 |
| product_detail_recommendation_visible | 335 | 1,987 | 16.86 |
| select_product_option_quality | 487 | 3,119 | 15.61 |
| add_to_cart_action | 35 | 237 | 14.77 |
| view_product_detail | 1,875 | 14,011 | 13.38 |
| select_product_option | 1,293 | 9,999 | 12.93 |
| view_static_page | 258 | 2,399 | 10.75 |
| search_box_action | 36 | 364 | 9.89 |

Empty referrer values are not automatically data-quality failures.

Possible explanations include direct navigation, unavailable referrer
information, browser/privacy behavior, or other legitimate traffic patterns.

---

## Small-sample warning

Percentages for rare event types must be interpreted together with their
absolute counts.

For example:

- 1 / 2 = 50%
- 7,099 / 14,011 = 50.67%

Similar percentages do not imply equivalent statistical significance.

---

## Preliminary classification

| Field | Observation | Preliminary classification |
|---|---|---|
| `_id` | No missing/NULL observed | Healthy in sample |
| `collection` | No missing/NULL observed | Healthy in sample |
| `user_id_db` | High empty rate | Expected/unknown semantics |
| `email_address` | High empty rate | Expected/unknown semantics |
| `show_recommendation` | NULL + string boolean representations | Requires semantic validation |
| `referrer_url` | Empty values observed | Likely expected in some traffic |

---

## Conclusion

The profiling demonstrates that technical missingness must be separated from
business validity.

A high NULL or empty-string percentage does not automatically indicate bad
data.

The next data-quality assessment should determine whether observed missingness
is:

1. expected by event semantics,
2. caused by anonymous user behavior,
3. caused by source-system representation,
4. or an actual data-quality defect.

All findings must later be validated against the full dataset.