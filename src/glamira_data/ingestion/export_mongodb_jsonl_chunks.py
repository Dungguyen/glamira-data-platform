from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId, json_util
from google.api_core.exceptions import PreconditionFailed
from google.cloud import storage
from pymongo import ASCENDING, MongoClient


DEFAULT_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

DEFAULT_DATABASE = "glamira"
DEFAULT_COLLECTION = "summary"

EXPECTED_SOURCE_COUNT = 41_432_473


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

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
        "--bucket",
        required=True,
    )

    parser.add_argument(
        "--run-id",
        required=True,
    )

    parser.add_argument(
        "--prefix",
        default="staging/events/incoming",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=250_000,
    )

    parser.add_argument(
        "--max-chunks",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--work-dir",
        default="./full-export",
    )

    return parser.parse_args()


def bson_to_json(document: dict) -> dict:
    serialized = json_util.dumps(
        document,
        json_options=json_util.RELAXED_JSON_OPTIONS,
    )

    return json.loads(serialized)


def transform_document(
    document: dict,
    database: str,
    collection: str,
    run_id: str,
    source_chunk: str,
) -> dict:

    timestamp = document.get(
        "time_stamp"
    )

    return {
        "event_id": str(
            document["_id"]
        ),
        "event_type": (
            str(document["collection"])
            if document.get("collection") is not None
            else None
        ),
        "event_timestamp_raw": (
            timestamp
            if isinstance(timestamp, (int, float))
            else None
        ),
        "source_database": database,
        "source_collection": collection,
        "ingestion_run_id": run_id,
        "source_chunk": source_chunk,
        "payload": bson_to_json(
            document
        ),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def save_state(
    path: Path,
    state: dict,
) -> None:

    temp = path.with_suffix(
        ".tmp"
    )

    temp.write_text(
        json.dumps(
            state,
            indent=2,
        ),
        encoding="utf-8",
    )

    temp.replace(path)


def main() -> None:
    args = parse_args()

    work_dir = Path(
        args.work_dir
    )

    work_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    state_path = (
        work_dir /
        f"{args.run_id}.json"
    )

    if state_path.exists():
        state = json.loads(
            state_path.read_text(
                encoding="utf-8"
            )
        )
    else:
        state = {
            "run_id": args.run_id,
            "expected_source_count":
                EXPECTED_SOURCE_COUNT,
            "chunk_size":
                args.chunk_size,
            "exported_rows": 0,
            "last_id": None,
            "chunks": [],
        }

    mongo = MongoClient(
        args.uri,
        serverSelectionTimeoutMS=10_000,
    )

    mongo.admin.command("ping")

    collection = mongo[
        args.database
    ][
        args.collection
    ]

    storage_client = (
        storage.Client()
    )

    bucket = storage_client.bucket(
        args.bucket
    )

    chunk_number = (
        len(state["chunks"]) + 1
    )

    chunks_this_run = 0

    while True:

        if (
            args.max_chunks is not None
            and chunks_this_run
            >= args.max_chunks
        ):
            break

        query = {}

        if state["last_id"]:
            query = {
                "_id": {
                    "$gt": ObjectId(
                        state["last_id"]
                    )
                }
            }

        filename = (
            f"part-{chunk_number:06d}"
            ".jsonl.gz"
        )

        object_name = (
            f"{args.prefix}/"
            f"{args.run_id}/"
            f"{filename}"
        )

        local_path = (
            work_dir / filename
        )

        cursor = (
            collection
            .find(query)
            .sort(
                "_id",
                ASCENDING,
            )
            .limit(
                args.chunk_size
            )
            .batch_size(1_000)
        )

        rows = 0
        first_id = None
        last_id = None

        with gzip.open(
            local_path,
            "wt",
            encoding="utf-8",
            newline="\n",
        ) as output:

            for document in cursor:

                if first_id is None:
                    first_id = str(
                        document["_id"]
                    )

                last_id = str(
                    document["_id"]
                )

                record = transform_document(
                    document=document,
                    database=args.database,
                    collection=args.collection,
                    run_id=args.run_id,
                    source_chunk=object_name,
                )

                output.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                )

                output.write("\n")

                rows += 1

        if rows == 0:
            local_path.unlink(
                missing_ok=True
            )
            break

        checksum = sha256_file(
            local_path
        )

        blob = bucket.blob(
            object_name
        )

        blob.metadata = {
            "run_id":
                args.run_id,
            "chunk_number":
                str(chunk_number),
            "row_count":
                str(rows),
            "first_id":
                first_id,
            "last_id":
                last_id,
            "sha256":
                checksum,
        }

        try:
            blob.upload_from_filename(
                local_path,
                content_type=(
                    "application/gzip"
                ),
                if_generation_match=0,
            )

            blob.reload()

        except PreconditionFailed:
            blob.reload()

            metadata = (
                blob.metadata or {}
            )

            if (
                metadata.get("sha256")
                != checksum
            ):
                raise RuntimeError(
                    "Existing GCS object "
                    "does not match "
                    "local chunk."
                )

            print(
                f"already uploaded: "
                f"{object_name}"
            )

        chunk_info = {
            "chunk_number":
                chunk_number,
            "rows":
                rows,
            "first_id":
                first_id,
            "last_id":
                last_id,
            "sha256":
                checksum,
            "gcs_object":
                object_name,
            "gcs_generation":
                str(blob.generation),
            "uploaded_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }

        state["chunks"].append(
            chunk_info
        )

        state["exported_rows"] += (
            rows
        )

        state["last_id"] = (
            last_id
        )

        save_state(
            state_path,
            state,
        )

        manifest_blob = bucket.blob(
            (
                "staging/events/"
                "manifests/"
                f"{args.run_id}.json"
            )
        )

        manifest_blob.upload_from_filename(
            state_path,
            content_type=(
                "application/json"
            ),
        )

        print(
            "\n"
            f"chunk={chunk_number} "
            f"rows={rows:,} "
            f"total={state['exported_rows']:,}"
        )

        local_path.unlink(
            missing_ok=True
        )

        chunk_number += 1
        chunks_this_run += 1

        if rows < args.chunk_size:
            break

    mongo.close()

    print(
        "\n========== FULL EXPORT STATE =========="
    )

    print(
        f"run_id        : {args.run_id}"
    )

    print(
        "chunks        : "
        f"{len(state['chunks']):,}"
    )

    print(
        "exported_rows : "
        f"{state['exported_rows']:,}"
    )

    print(
        "last_id       : "
        f"{state['last_id']}"
    )


if __name__ == "__main__":
    main()