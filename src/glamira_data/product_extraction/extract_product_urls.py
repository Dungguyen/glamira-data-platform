from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from urllib.parse import urlsplit, urlunsplit

from pymongo import MongoClient


MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "glamira"
COLLECTION_NAME = "summary"

BASE_DIR = Path.home() / "glamira-product-extraction"
OUTPUT_DIR = BASE_DIR / "output"

PRODUCT_URLS_CSV = OUTPUT_DIR / "product_url_set.csv"
PRODUCTS_CSV = OUTPUT_DIR / "product_set.csv"
SUMMARY_PATH = OUTPUT_DIR / "product_extraction_summary.txt"

PROGRESS_EVERY = 1_000_000

TRUSTED_URL_COLLECTIONS = {
    "view_product_detail",
    "select_product_option",
    "select_product_option_quality",
    "add_to_cart_action",
}


def normalize_product_id(value: object) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()

    if not normalized:
        return None

    return normalized


def canonicalize_url(value: object) -> tuple[str, str] | None:
    if not isinstance(value, str):
        return None

    raw = value.strip()

    if not raw:
        return None

    try:
        parts = urlsplit(raw)
    except ValueError:
        return None

    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()

    if scheme not in {"http", "https"}:
        return None

    if not hostname:
        return None

    path = parts.path or "/"

    canonical_url = urlunsplit(
        (
            scheme,
            hostname,
            path,
            "",
            "",
        )
    )

    return canonical_url, hostname


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    client = MongoClient(MONGO_URI)
    collection = client[DB_NAME][COLLECTION_NAME]

    product_ids: set[str] = set()

    product_url_pairs: set[tuple[str, str, str]] = set()

    product_url_counts: dict[str, int] = defaultdict(int)

    processed_documents = 0

    top_level_product_occurrences = 0
    cart_product_occurrences = 0
    recommendation_product_occurrences = 0

    trusted_url_observations = 0
    canonical_url_observations = 0
    invalid_url_observations = 0

    start = perf_counter()

    projection = {
        "_id": 0,
        "collection": 1,
        "product_id": 1,
        "recommendation_product_id": 1,
        "cart_products.product_id": 1,
        "current_url": 1,
    }

    cursor = collection.find(
        {},
        projection=projection,
        no_cursor_timeout=True,
        batch_size=10_000,
    )

    try:
        for doc in cursor:
            processed_documents += 1

            collection_name = doc.get("collection")

            # --------------------------------------------------
            # Source A: top-level product_id
            # --------------------------------------------------

            top_product_id = normalize_product_id(
                doc.get("product_id")
            )

            if top_product_id:
                product_ids.add(top_product_id)
                top_level_product_occurrences += 1

                if collection_name in TRUSTED_URL_COLLECTIONS:
                    trusted_url_observations += 1

                    canonical = canonicalize_url(
                        doc.get("current_url")
                    )

                    if canonical is None:
                        invalid_url_observations += 1
                    else:
                        canonical_url, hostname = canonical

                        canonical_url_observations += 1

                        product_url_pairs.add(
                            (
                                top_product_id,
                                canonical_url,
                                hostname,
                            )
                        )

            # --------------------------------------------------
            # Source B: recommendation_product_id
            # --------------------------------------------------

            recommendation_product_id = normalize_product_id(
                doc.get("recommendation_product_id")
            )

            if recommendation_product_id:
                product_ids.add(recommendation_product_id)
                recommendation_product_occurrences += 1

            # --------------------------------------------------
            # Source C: cart_products[].product_id
            # --------------------------------------------------

            cart_products = doc.get("cart_products")

            if isinstance(cart_products, list):
                for item in cart_products:
                    if not isinstance(item, dict):
                        continue

                    cart_product_id = normalize_product_id(
                        item.get("product_id")
                    )

                    if cart_product_id:
                        product_ids.add(cart_product_id)
                        cart_product_occurrences += 1

            if processed_documents % PROGRESS_EVERY == 0:
                elapsed = perf_counter() - start

                print(
                    f"processed={processed_documents:,} "
                    f"unique_products={len(product_ids):,} "
                    f"product_url_pairs={len(product_url_pairs):,} "
                    f"elapsed={elapsed / 60:.2f} min"
                )

    finally:
        cursor.close()
        client.close()

    # ------------------------------------------------------
    # Build product -> URL counts
    # ------------------------------------------------------

    for product_id, _, _ in product_url_pairs:
        product_url_counts[product_id] += 1

    products_with_url = len(product_url_counts)

    products_without_url = len(product_ids) - products_with_url

    # ------------------------------------------------------
    # Write product_url_set.csv
    # grain: 1 row = 1 product_id + canonical_url pair
    # ------------------------------------------------------

    with PRODUCT_URLS_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            [
                "product_id",
                "canonical_url",
                "storefront_host",
                "url_status",
            ]
        )

        for product_id, canonical_url, hostname in sorted(
            product_url_pairs
        ):
            writer.writerow(
                [
                    product_id,
                    canonical_url,
                    hostname,
                    "OBSERVED",
                ]
            )

    # ------------------------------------------------------
    # Write product_set.csv
    # grain: 1 row = 1 product_id
    # ------------------------------------------------------

    with PRODUCTS_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            [
                "product_id",
                "url_count",
                "url_status",
            ]
        )

        for product_id in sorted(product_ids):
            url_count = product_url_counts.get(
                product_id,
                0,
            )

            writer.writerow(
                [
                    product_id,
                    url_count,
                    (
                        "OBSERVED"
                        if url_count > 0
                        else "NOT_OBSERVED"
                    ),
                ]
            )

    elapsed = perf_counter() - start

    # ------------------------------------------------------
    # Assertions from discovery
    # ------------------------------------------------------

    expected_unique_products = 19_558

    universe_match = (
        len(product_ids)
        == expected_unique_products
    )

    summary = f"""
========== PRODUCT EXTRACTION SUMMARY ==========

processed_documents: {processed_documents:,}

top_level_product_occurrences:
{top_level_product_occurrences:,}

cart_product_occurrences:
{cart_product_occurrences:,}

recommendation_product_occurrences:
{recommendation_product_occurrences:,}

unique_product_ids:
{len(product_ids):,}

products_with_url:
{products_with_url:,}

products_without_url:
{products_without_url:,}

trusted_url_observations:
{trusted_url_observations:,}

canonical_url_observations:
{canonical_url_observations:,}

invalid_url_observations:
{invalid_url_observations:,}

unique_product_url_pairs:
{len(product_url_pairs):,}

expected_unique_products:
{expected_unique_products:,}

product_universe_match:
{universe_match}

elapsed_seconds:
{elapsed:.2f}

elapsed_minutes:
{elapsed / 60:.2f}

product_set_csv:
{PRODUCTS_CSV}

product_url_set_csv:
{PRODUCT_URLS_CSV}
""".strip()

    SUMMARY_PATH.write_text(
        summary + "\n",
        encoding="utf-8",
    )

    print()
    print(summary)

    if not universe_match:
        raise RuntimeError(
            "Product universe mismatch: "
            f"expected {expected_unique_products:,}, "
            f"got {len(product_ids):,}"
        )


if __name__ == "__main__":
    main()
