from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path

from bson import json_util
from pymongo import MongoClient


DEFAULT_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

DEFAULT_DATABASE = "glamira"
DEFAULT_COLLECTION = "summary"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stream MongoDB events to compressed JSONL."
        )
    )

    parser.add_argument(
        "--uri",
        default=DEFAULT_URI,
    )

    parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE,
    )

    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10_000,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1_000,
    )

    return parser.parse_args()


def make_json_compatible(document: dict) -> dict:
    """
    Convert BSON-specific values into JSON-compatible
    Extended JSON representations.

    This preserves source semantics better than blindly
    coercing unsupported BSON values to strings.
    """

    serialized = json_util.dumps(
        document,
        json_options=json_util.RELAXED_JSON_OPTIONS,
    )

    return json.loads(serialized)


def main() -> None:
    args = parse_args()

    if args.limit <= 0:
        raise ValueError(
            "--limit must be greater than 0"
        )

    output_path = Path(args.output)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    client = MongoClient(
        args.uri,
        serverSelectionTimeoutMS=10_000,
    )

    client.admin.command("ping")

    collection = client[
        args.database
    ][
        args.collection
    ]

    cursor = (
        collection
        .find({})
        .batch_size(args.batch_size)
        .limit(args.limit)
    )

    written = 0

    with gzip.open(
        output_path,
        "wt",
        encoding="utf-8",
        newline="\n",
    ) as output:

        for document in cursor:

            payload = make_json_compatible(
                document
            )

            event_id = str(
                document.get("_id", "")
            )

            event_type = document.get(
                "collection"
            )

            timestamp = document.get(
                "time_stamp"
            )

            record = {
                "event_id": event_id,
                "event_type": (
                    str(event_type)
                    if event_type is not None
                    else None
                ),
                "event_timestamp_raw": (
                    timestamp
                    if isinstance(
                        timestamp,
                        (int, float),
                    )
                    else None
                ),
                "source_database":
                    args.database,
                "source_collection":
                    args.collection,
                "payload":
                    payload,
            }

            output.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )

            output.write("\n")

            written += 1

            if written % 1_000 == 0:
                print(
                    f"exported: {written:,}"
                )

    client.close()

    print("\n========== EXPORT SUMMARY ==========")
    print(
        f"records_written : {written:,}"
    )
    print(
        f"output          : {output_path}"
    )

    if written != args.limit:
        raise RuntimeError(
            "Export row count does not match requested limit."
        )

    print(
        "\nCHECKPOINT 16 SAMPLE EXPORT: PASS"
    )


if __name__ == "__main__":
    main()