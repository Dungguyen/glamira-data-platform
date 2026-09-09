from __future__ import annotations

import hashlib
import os

import functions_framework
from cloudevents.http import CloudEvent
from google.api_core.exceptions import Conflict
from google.cloud import bigquery


BQ_PROJECT = os.getenv(
    "BQ_PROJECT",
    "glamira-pipeline-506706",
)

BQ_DATASET = os.getenv(
    "BQ_DATASET",
    "raw",
)

BQ_TABLE = os.getenv(
    "BQ_TABLE",
    "events",
)

BQ_LOCATION = os.getenv(
    "BQ_LOCATION",
    "asia-southeast1",
)

OBJECT_PREFIX = os.getenv(
    "OBJECT_PREFIX",
    "staging/events/incoming/",
)


def build_job_id(
    bucket: str,
    object_name: str,
    generation: str,
) -> str:
    """
    Build a deterministic BigQuery job ID.

    Eventarc can redeliver the same event.
    The same GCS object generation must map
    to the same BigQuery load job.
    """

    identity = (
        f"{bucket}/{object_name}#{generation}"
    )

    digest = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()[:32]

    return f"gcs_load_{digest}"


@functions_framework.cloud_event
def load_gcs_jsonl_to_bigquery(
    cloud_event: CloudEvent,
) -> str:

    data = cloud_event.data

    bucket = data["bucket"]
    object_name = data["name"]
    generation = str(
        data.get("generation", "")
    )

    print(
        f"received bucket={bucket} "
        f"object={object_name} "
        f"generation={generation}"
    )

    # Eventarc Storage filters operate at bucket level.
    # Only our ingestion prefix should be processed.
    if not object_name.startswith(
        OBJECT_PREFIX
    ):
        print(
            f"ignored: object outside "
            f"prefix {OBJECT_PREFIX}"
        )
        return "ignored"

    if not object_name.endswith(
        ".jsonl.gz"
    ):
        print(
            "ignored: unsupported file format"
        )
        return "ignored"

    source_uri = (
        f"gs://{bucket}/{object_name}"
    )

    destination = (
        f"{BQ_PROJECT}."
        f"{BQ_DATASET}."
        f"{BQ_TABLE}"
    )

    job_id = build_job_id(
        bucket=bucket,
        object_name=object_name,
        generation=generation,
    )

    client = bigquery.Client(
        project=BQ_PROJECT
    )

    job_config = bigquery.LoadJobConfig(
        source_format=(
            bigquery.SourceFormat
            .NEWLINE_DELIMITED_JSON
        ),
        write_disposition=(
            bigquery.WriteDisposition
            .WRITE_APPEND
        ),
        ignore_unknown_values=False,
        max_bad_records=0,
    )

    print(
        f"loading {source_uri} "
        f"to {destination} "
        f"job_id={job_id}"
    )

    try:
        job = client.load_table_from_uri(
            source_uris=source_uri,
            destination=destination,
            job_id=job_id,
            location=BQ_LOCATION,
            job_config=job_config,
        )

    except Conflict:
        # Same event delivery / same GCS generation.
        # Reuse the existing BigQuery job instead
        # of starting a second load.
        print(
            f"job already exists: {job_id}"
        )

        job = client.get_job(
            job_id=job_id,
            project=BQ_PROJECT,
            location=BQ_LOCATION,
        )

    job.result()

    print(
        f"load completed "
        f"job_id={job_id} "
        f"output_rows={job.output_rows}"
    )

    return "ok"