import csv
import time
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path.home() / "glamira-product-extraction"

PRODUCT_SET = BASE_DIR / "output" / "product_set.csv"
PRODUCT_URL_SET = BASE_DIR / "output" / "product_url_set.csv"
CRAWL_RESULT = (
    BASE_DIR
    / "output"
    / "product_catalog_10000_results.csv"
)

OUTPUT_DIR = BASE_DIR / "output" / "dimensions"

OUTPUT_FILE = (
    OUTPUT_DIR
    / "dim_product_enriched.csv"
)

SUMMARY_FILE = (
    OUTPUT_DIR
    / "dim_product_enriched_summary.txt"
)

EXPECTED_PRODUCTS = 19_558


def clean(value) -> str:
    if value is None:
        return ""

    value = str(value).strip()

    if value.lower() in {
        "",
        "null",
        "none",
        "nan",
    }:
        return ""

    return value


def is_production_host(host: str) -> bool:
    if not host:
        return False

    host = host.strip().lower()

    if not (
        host == "glamira.com"
        or host.startswith("www.glamira.")
    ):
        return False

    blocked_prefixes = (
        "stage.",
        "staging.",
        "dev.",
        "test.",
        "localhost",
    )

    return not host.startswith(blocked_prefixes)


def is_valid_product_url(url: str) -> bool:
    if not url:
        return False

    try:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            return False

        if not parsed.netloc:
            return False

        if not is_production_host(
            parsed.hostname or ""
        ):
            return False

        path = parsed.path.lower()

        if not path.endswith(".html"):
            return False

        blocked_paths = (
            "/checkout/",
            "/county/recommendation/",
        )

        if any(
            blocked in path
            for blocked in blocked_paths
        ):
            return False

        return True

    except ValueError:
        return False


def is_successful_crawl(row: dict) -> bool:
    success = clean(
        row.get("success")
    ).lower()

    http_status = clean(
        row.get("http_status")
    )

    return (
        success == "true"
        and http_status == "200"
    )


def main():
    start = time.perf_counter()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # =========================================================
    # STEP 1
    # Load authoritative product universe
    # =========================================================

    products = {}

    with PRODUCT_SET.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            product_id = clean(
                row.get("product_id")
            )

            if not product_id:
                continue

            # Hard DQ gate:
            # never silently overwrite duplicates
            if product_id in products:
                raise RuntimeError(
                    "Duplicate product_id "
                    f"in product_set.csv: "
                    f"{product_id}"
                )

            products[product_id] = {
                "product_id": product_id,

                # Product metadata
                "sku": "",
                "product_name": "",
                "category": "",
                "description": "",
                "image_url": "",

                # URL lineage
                "representative_url": "",
                "representative_host": "",

                # Crawl lineage
                "crawl_url": "",
                "crawl_host": "",

                # Source information
                "source_url_count": int(
                    row["url_count"]
                ),
                "source_url_status": clean(
                    row.get("url_status")
                ),

                # Enrichment state
                "product_master_status":
                    "NOT_ENRICHED",
            }

    # =========================================================
    # STEP 2
    # Select deterministic representative URL
    # =========================================================

    eligible_url_rows = 0

    with PRODUCT_URL_SET.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            product_id = clean(
                row.get("product_id")
            )

            url = clean(
                row.get("canonical_url")
            )

            host = clean(
                row.get("storefront_host")
            ).lower()

            if product_id not in products:
                continue

            if not is_valid_product_url(url):
                continue

            eligible_url_rows += 1

            candidate = (
                host,
                url,
            )

            current_url = (
                products[product_id][
                    "representative_url"
                ]
            )

            current_host = (
                products[product_id][
                    "representative_host"
                ]
            )

            if not current_url:
                products[product_id][
                    "representative_url"
                ] = url

                products[product_id][
                    "representative_host"
                ] = host

                continue

            current = (
                current_host,
                current_url,
            )

            if candidate < current:
                products[product_id][
                    "representative_url"
                ] = url

                products[product_id][
                    "representative_host"
                ] = host

    # =========================================================
    # STEP 3
    # Enrich using successful crawl results
    # =========================================================

    crawl_product_ids = set()
    duplicate_crawl_ids = set()
    unknown_crawl_ids = set()

    successful_crawl_rows = 0
    unsuccessful_crawl_rows = 0

    with CRAWL_RESULT.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            product_id = clean(
                row.get("product_id")
            )

            if not product_id:
                continue

            if product_id in crawl_product_ids:
                duplicate_crawl_ids.add(
                    product_id
                )
                continue

            crawl_product_ids.add(
                product_id
            )

            if product_id not in products:
                unknown_crawl_ids.add(
                    product_id
                )
                continue

            if not is_successful_crawl(row):
                unsuccessful_crawl_rows += 1
                continue

            successful_crawl_rows += 1

            product = products[product_id]

            product["sku"] = clean(
                row.get("sku")
            )

            product["product_name"] = clean(
                row.get("name")
            )

            product["category"] = clean(
                row.get("category")
            )

            product["description"] = clean(
                row.get("description")
            )

            product["image_url"] = clean(
                row.get("image")
            )

            product["crawl_url"] = clean(
                row.get("url")
            )

            product["crawl_host"] = clean(
                row.get("domain")
            ).lower()

            product[
                "product_master_status"
            ] = "ENRICHED"

    # =========================================================
    # STEP 4
    # Prepare output
    # =========================================================

    sorted_products = sorted(
        products.values(),
        key=lambda row: (
            int(row["product_id"])
            if row["product_id"].isdigit()
            else row["product_id"]
        ),
    )

    # =========================================================
    # STEP 5
    # Write enriched dimension
    # =========================================================

    fieldnames = [
        "product_id",
        "sku",
        "product_name",
        "category",
        "description",
        "image_url",
        "representative_url",
        "representative_host",
        "crawl_url",
        "crawl_host",
        "source_url_count",
        "source_url_status",
        "product_master_status",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            sorted_products
        )

    # =========================================================
    # STEP 6
    # Dimension DQ
    # =========================================================

    total_products = len(
        sorted_products
    )

    unique_product_ids = len({
        row["product_id"]
        for row in sorted_products
    })

    duplicate_product_ids = (
        total_products
        - unique_product_ids
    )

    enriched_products = sum(
        row["product_master_status"]
        == "ENRICHED"
        for row in sorted_products
    )

    not_enriched_products = (
        total_products
        - enriched_products
    )

    # Metadata coverage
    name_found = sum(
        bool(row["product_name"])
        for row in sorted_products
    )

    sku_found = sum(
        bool(row["sku"])
        for row in sorted_products
    )

    category_found = sum(
        bool(row["category"])
        for row in sorted_products
    )

    image_found = sum(
        bool(row["image_url"])
        for row in sorted_products
    )

    description_found = sum(
        bool(row["description"])
        for row in sorted_products
    )

    representative_url_found = sum(
        bool(row["representative_url"])
        for row in sorted_products
    )

    universe_match = (
        total_products
        == EXPECTED_PRODUCTS
    )

    grain_valid = (
        duplicate_product_ids == 0
    )

    accounted_products = (
        enriched_products
        + not_enriched_products
    )

    coverage_pct = (
        enriched_products
        / total_products
        * 100
        if total_products
        else 0
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    # =========================================================
    # STEP 7
    # Summary
    # =========================================================

    summary = f"""
========== ENRICHED DIM_PRODUCT ==========

INPUT / GRAIN
-----------------------------------------
expected_product_universe:
{EXPECTED_PRODUCTS:,}

total_dimension_rows:
{total_products:,}

unique_product_ids:
{unique_product_ids:,}

duplicate_product_ids:
{duplicate_product_ids:,}

product_universe_match:
{universe_match}

grain_valid:
{grain_valid}


ENRICHMENT
-----------------------------------------
successful_crawl_rows:
{successful_crawl_rows:,}

enriched_products:
{enriched_products:,}

not_enriched_products:
{not_enriched_products:,}

accounted_products:
{accounted_products:,}

enrichment_coverage_pct:
{coverage_pct:.2f}%


METADATA COVERAGE
-----------------------------------------
product_name_found:
{name_found:,}

sku_found:
{sku_found:,}

category_found:
{category_found:,}

image_found:
{image_found:,}

description_found:
{description_found:,}

representative_url_found:
{representative_url_found:,}


CRAWL DQ
-----------------------------------------
unique_crawl_product_ids:
{len(crawl_product_ids):,}

duplicate_crawl_ids:
{len(duplicate_crawl_ids):,}

unknown_crawl_ids:
{len(unknown_crawl_ids):,}

unsuccessful_crawl_rows:
{unsuccessful_crawl_rows:,}


URL DQ
-----------------------------------------
eligible_product_url_rows:
{eligible_url_rows:,}


PERFORMANCE
-----------------------------------------
elapsed_seconds:
{elapsed:.2f}


OUTPUT
-----------------------------------------
{OUTPUT_FILE}
""".strip()

    SUMMARY_FILE.write_text(
        summary + "\n",
        encoding="utf-8",
    )

    print(summary)

    # =========================================================
    # STEP 8
    # Hard DQ gates
    # =========================================================

    if not universe_match:
        raise RuntimeError(
            "Product universe validation failed."
        )

    if not grain_valid:
        raise RuntimeError(
            "dim_product grain validation failed."
        )

    if duplicate_crawl_ids:
        raise RuntimeError(
            "Duplicate product_id found "
            "in crawl result."
        )

    if unknown_crawl_ids:
        raise RuntimeError(
            "Crawl result contains "
            "product_id outside universe."
        )

    if (
        accounted_products
        != EXPECTED_PRODUCTS
    ):
        raise RuntimeError(
            "Product accounting validation "
            "failed."
        )

    print(
        "\nCHECKPOINT 11 TRANSFORMATION: PASS"
    )


if __name__ == "__main__":
    main()
