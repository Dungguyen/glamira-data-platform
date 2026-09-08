from __future__ import annotations

import argparse
import os
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient


DEFAULT_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

DEFAULT_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "glamira",
)

DEFAULT_COLLECTION = os.getenv(
    "MONGODB_COLLECTION",
    "summary",
)

DEFAULT_SAMPLE_SIZE = 100_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Explore a bounded sample of the Glamira "
            "MongoDB event collection."
        )
    )

    parser.add_argument(
        "--uri",
        default=DEFAULT_URI,
        help="MongoDB connection URI.",
    )

    parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE,
        help="MongoDB database name.",
    )

    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help="MongoDB collection name.",
    )

    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Maximum number of documents to inspect.",
    )

    return parser.parse_args()


def infer_timestamp(
    value: Any,
) -> tuple[str, str]:
    """
    Return:
        inferred_unit,
        interpreted_utc

    The interpretation is only a heuristic for exploration.
    The original raw value remains authoritative.
    """
    if not isinstance(value, (int, float)):
        return "unknown", ""

    try:
        if value >= 100_000_000_000:
            unit = "milliseconds"
            seconds = value / 1000
        elif value >= 1_000_000_000:
            unit = "seconds"
            seconds = value
        else:
            return "unknown", ""

        dt = datetime.fromtimestamp(
            seconds,
            tz=timezone.utc,
        )

        return (
            unit,
            dt.isoformat(),
        )

    except (
        OverflowError,
        OSError,
        ValueError,
    ):
        return "unknown", ""


def main() -> None:
    args = parse_args()

    if args.sample_size <= 0:
        raise ValueError(
            "--sample-size must be greater than 0"
        )

    client = MongoClient(
        args.uri,
        serverSelectionTimeoutMS=10_000,
    )

    # Fail early if MongoDB is unreachable.
    client.admin.command("ping")

    collection = client[
        args.database
    ][
        args.collection
    ]

    print(
        "========== GLAMIRA DATA EXPLORATION =========="
    )

    print("\nSOURCE")
    print("----------------------------------------------")
    print(
        f"database           : {args.database}"
    )
    print(
        f"collection         : {args.collection}"
    )
    print(
        f"sample_size_limit  : "
        f"{args.sample_size:,}"
    )

    event_counts: Counter[str] = Counter()

    unique_ips: set[str] = set()

    observed_fields: Counter[str] = Counter()

    min_timestamp = None
    max_timestamp = None

    inspected_documents = 0

    projection = {
        "collection": 1,
        "time_stamp": 1,
        "ip": 1,
    }

    cursor = (
        collection
        .find({}, projection)
        .limit(args.sample_size)
    )

    for document in cursor:
        inspected_documents += 1

        event_type = document.get(
            "collection"
        )

        if event_type is None:
            event_type = "<MISSING>"

        event_counts[
            str(event_type)
        ] += 1

        ip = document.get("ip")

        if ip is not None:
            ip = str(ip).strip()

            if ip:
                unique_ips.add(ip)

        timestamp = document.get(
            "time_stamp"
        )

        if isinstance(
            timestamp,
            (int, float),
        ):
            if (
                min_timestamp is None
                or timestamp < min_timestamp
            ):
                min_timestamp = timestamp

            if (
                max_timestamp is None
                or timestamp > max_timestamp
            ):
                max_timestamp = timestamp

        for field in document:
            observed_fields[field] += 1

    print("\nSAMPLE SUMMARY")
    print("----------------------------------------------")
    print(
        f"documents_inspected : "
        f"{inspected_documents:,}"
    )
    print(
        f"unique_event_types  : "
        f"{len(event_counts):,}"
    )
    print(
        f"unique_ips_sample   : "
        f"{len(unique_ips):,}"
    )

    print("\nEVENT TYPES")
    print("----------------------------------------------")

    for event_type, count in (
        event_counts.most_common()
    ):
        pct = (
            count
            / inspected_documents
            * 100
            if inspected_documents
            else 0
        )

        print(
            f"{event_type:<45}"
            f"{count:>10,}"
            f"  ({pct:6.2f}%)"
        )

    print("\nTIMESTAMP RANGE")
    print("----------------------------------------------")

    print(
        f"raw_min : {min_timestamp}"
    )
    print(
        f"raw_max : {max_timestamp}"
    )

    min_unit, min_utc = infer_timestamp(
        min_timestamp
    )

    max_unit, max_utc = infer_timestamp(
        max_timestamp
    )

    print(
        f"inferred_min_unit : {min_unit}"
    )
    print(
        f"inferred_min_utc  : {min_utc}"
    )

    print(
        f"inferred_max_unit : {max_unit}"
    )
    print(
        f"inferred_max_utc  : {max_utc}"
    )

    print(
        "\nNOTE: timestamp conversion above is "
        "an exploration heuristic only."
    )

    print("\nOBSERVED PROJECTED FIELDS")
    print("----------------------------------------------")

    for field, count in sorted(
        observed_fields.items()
    ):
        print(
            f"{field:<30}{count:>10,}"
        )

    print(
        "\nCHECKPOINT 14.1 DATA EXPLORATION: PASS"
    )

    client.close()


if __name__ == "__main__":
    main()