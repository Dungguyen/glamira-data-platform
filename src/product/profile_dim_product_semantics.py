import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path.home() / "glamira-product-extraction"

INPUT_FILE = (
    BASE_DIR
    / "output"
    / "dimensions"
    / "dim_product_enriched.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "output"
    / "dimensions"
)

REPORT_FILE = (
    OUTPUT_DIR
    / "dim_product_semantic_profile.txt"
)

DUPLICATE_SKU_FILE = (
    OUTPUT_DIR
    / "dim_product_duplicate_skus.csv"
)

ANOMALY_FILE = (
    OUTPUT_DIR
    / "dim_product_semantic_anomalies.csv"
)


ENRICHMENT_FIELDS = [
    "sku",
    "product_name",
    "category",
    "description",
    "image_url",
    "crawl_url",
    "crawl_host",
]


NULL_LIKE_VALUES = {
    "",
    "null",
    "none",
    "nan",
    "undefined",
    "n/a",
    "na",
}


def clean(value):
    if value is None:
        return ""

    return str(value).strip()


def is_null_like(value):
    return clean(value).lower() in NULL_LIKE_VALUES


def hostname(url):
    if not url:
        return ""

    try:
        return (
            urlparse(url).hostname
            or ""
        ).lower()

    except ValueError:
        return ""


def percentile(values, pct):
    if not values:
        return 0

    values = sorted(values)

    index = int(
        round(
            (len(values) - 1)
            * pct
        )
    )

    return values[index]


def main():

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        rows = list(
            csv.DictReader(file)
        )

    enriched = [
        row
        for row in rows
        if clean(
            row.get(
                "product_master_status"
            )
        ) == "ENRICHED"
    ]

    not_enriched = [
        row
        for row in rows
        if clean(
            row.get(
                "product_master_status"
            )
        ) == "NOT_ENRICHED"
    ]

    # =====================================================
    # 1. Status invariants
    # =====================================================

    enriched_missing_metadata = []

    for row in enriched:

        missing_fields = [
            field
            for field in ENRICHMENT_FIELDS
            if is_null_like(
                row.get(field)
            )
        ]

        if missing_fields:
            enriched_missing_metadata.append(
                (
                    row["product_id"],
                    missing_fields,
                )
            )

    not_enriched_with_metadata = []

    for row in not_enriched:

        populated = [
            field
            for field in ENRICHMENT_FIELDS
            if not is_null_like(
                row.get(field)
            )
        ]

        if populated:
            not_enriched_with_metadata.append(
                (
                    row["product_id"],
                    populated,
                )
            )

    # =====================================================
    # 2. SKU profiling
    # =====================================================

    sku_to_products = defaultdict(
        list
    )

    for row in enriched:

        sku = clean(
            row.get("sku")
        )

        if not is_null_like(sku):
            sku_to_products[sku].append(
                row["product_id"]
            )

    duplicate_skus = {
        sku: product_ids
        for sku, product_ids
        in sku_to_products.items()
        if len(product_ids) > 1
    }

    duplicate_sku_products = sum(
        len(product_ids)
        for product_ids
        in duplicate_skus.values()
    )

    # =====================================================
    # 3. Product name profiling
    # =====================================================

    name_counter = Counter(
        clean(
            row.get("product_name")
        )
        for row in enriched
        if not is_null_like(
            row.get("product_name")
        )
    )

    duplicate_names = {
        name: count
        for name, count
        in name_counter.items()
        if count > 1
    }

    # =====================================================
    # 4. Category profiling
    # =====================================================

    category_counter = Counter(
        clean(
            row.get("category")
        )
        for row in enriched
        if not is_null_like(
            row.get("category")
        )
    )

    # =====================================================
    # 5. Description profiling
    # =====================================================

    description_lengths = [
        len(
            clean(
                row.get(
                    "description"
                )
            )
        )
        for row in enriched
        if not is_null_like(
            row.get(
                "description"
            )
        )
    ]

    # =====================================================
    # 6. URL / host integrity
    # =====================================================

    crawl_host_mismatch = []
    representative_host_mismatch = []
    invalid_image_urls = []

    for row in rows:

        product_id = row[
            "product_id"
        ]

        crawl_url = clean(
            row.get("crawl_url")
        )

        crawl_host = clean(
            row.get("crawl_host")
        ).lower()

        if crawl_url:

            actual_host = hostname(
                crawl_url
            )

            if (
                not actual_host
                or actual_host
                != crawl_host
            ):
                crawl_host_mismatch.append(
                    product_id
                )

        representative_url = clean(
            row.get(
                "representative_url"
            )
        )

        representative_host = clean(
            row.get(
                "representative_host"
            )
        ).lower()

        if representative_url:

            actual_host = hostname(
                representative_url
            )

            if (
                not actual_host
                or actual_host
                != representative_host
            ):
                representative_host_mismatch.append(
                    product_id
                )

        image_url = clean(
            row.get("image_url")
        )

        if image_url:

            parsed = urlparse(
                image_url
            )

            if (
                parsed.scheme
                not in {
                    "http",
                    "https",
                }
                or not parsed.netloc
            ):
                invalid_image_urls.append(
                    product_id
                )

    # =====================================================
    # 7. General semantic anomalies
    # =====================================================

    anomaly_rows = []

    for row in enriched:

        product_id = row[
            "product_id"
        ]

        name = clean(
            row.get(
                "product_name"
            )
        )

        sku = clean(
            row.get("sku")
        )

        category = clean(
            row.get("category")
        )

        description = clean(
            row.get(
                "description"
            )
        )

        issues = []

        if len(name) < 3:
            issues.append(
                "SHORT_PRODUCT_NAME"
            )

        if len(sku) < 2:
            issues.append(
                "SHORT_SKU"
            )

        if len(category) < 2:
            issues.append(
                "SHORT_CATEGORY"
            )

        if len(description) < 20:
            issues.append(
                "SHORT_DESCRIPTION"
            )

        if issues:
            anomaly_rows.append({
                "product_id":
                    product_id,
                "issues":
                    "|".join(
                        issues
                    ),
                "sku":
                    sku,
                "product_name":
                    name,
                "category":
                    category,
            })

    # =====================================================
    # 8. Write duplicate SKU investigation file
    # =====================================================

    with DUPLICATE_SKU_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        fieldnames = [
            "sku",
            "product_count",
            "product_ids",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for sku, product_ids in sorted(
            duplicate_skus.items(),
            key=lambda item: (
                -len(item[1]),
                item[0],
            ),
        ):

            writer.writerow({
                "sku":
                    sku,
                "product_count":
                    len(
                        product_ids
                    ),
                "product_ids":
                    "|".join(
                        product_ids
                    ),
            })

    # =====================================================
    # 9. Write anomalies
    # =====================================================

    with ANOMALY_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        fieldnames = [
            "product_id",
            "issues",
            "sku",
            "product_name",
            "category",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            anomaly_rows
        )

    # =====================================================
    # 10. Report
    # =====================================================

    description_min = (
        min(description_lengths)
        if description_lengths
        else 0
    )

    description_max = (
        max(description_lengths)
        if description_lengths
        else 0
    )

    description_median = (
        statistics.median(
            description_lengths
        )
        if description_lengths
        else 0
    )

    description_p95 = percentile(
        description_lengths,
        0.95,
    )

    top_categories = "\n".join(
        f"{category}: {count:,}"
        for category, count
        in category_counter.most_common(
            20
        )
    )

    top_duplicate_skus = "\n".join(
        (
            f"{sku}: "
            f"{len(product_ids):,}"
        )
        for sku, product_ids
        in sorted(
            duplicate_skus.items(),
            key=lambda item:
                -len(item[1]),
        )[:20]
    )

    report = f"""
========== DIM_PRODUCT SEMANTIC PROFILE ==========

STATUS
--------------------------------------------------
total_rows:
{len(rows):,}

enriched:
{len(enriched):,}

not_enriched:
{len(not_enriched):,}

enriched_missing_metadata:
{len(enriched_missing_metadata):,}

not_enriched_with_enrichment_metadata:
{len(not_enriched_with_metadata):,}


SKU
--------------------------------------------------
unique_skus:
{len(sku_to_products):,}

duplicate_sku_values:
{len(duplicate_skus):,}

products_using_duplicate_skus:
{duplicate_sku_products:,}

TOP DUPLICATE SKUS
--------------------------------------------------
{top_duplicate_skus or "NONE"}


PRODUCT NAME
--------------------------------------------------
unique_product_names:
{len(name_counter):,}

duplicate_product_name_values:
{len(duplicate_names):,}


CATEGORY
--------------------------------------------------
unique_categories:
{len(category_counter):,}

TOP CATEGORIES
--------------------------------------------------
{top_categories or "NONE"}


DESCRIPTION LENGTH
--------------------------------------------------
min:
{description_min}

median:
{description_median}

p95:
{description_p95}

max:
{description_max}


URL / HOST INTEGRITY
--------------------------------------------------
crawl_host_mismatch:
{len(crawl_host_mismatch):,}

representative_host_mismatch:
{len(representative_host_mismatch):,}

invalid_image_urls:
{len(invalid_image_urls):,}


SEMANTIC ANOMALIES
--------------------------------------------------
anomaly_rows:
{len(anomaly_rows):,}


OUTPUTS
--------------------------------------------------
duplicate_sku_file:
{DUPLICATE_SKU_FILE}

anomaly_file:
{ANOMALY_FILE}
""".strip()

    REPORT_FILE.write_text(
        report + "\n",
        encoding="utf-8",
    )

    print(report)


if __name__ == "__main__":
    main()
