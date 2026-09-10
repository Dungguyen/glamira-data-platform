import hashlib
import logging
import os
import functions_framework
from google.api_core.exceptions import Conflict
from google.cloud import bigquery


PROJECT_ID = os.getenv(
    "BQ_PROJECT_ID",
    "glamira-pipeline-506706",
)

DATASET_ID = os.getenv(
    "BQ_DATASET_ID",
    "raw",
)

BQ_LOCATION = os.getenv(
    "BQ_LOCATION",
    "asia-southeast1",
)


LOAD_ROUTES = {
    "staging/geoip/incoming/": {
        "table": "geoip",
    },
    "staging/products/incoming/": {
        "table": "products",
    },
}


def resolve_route(object_name: str):
    for prefix, config in LOAD_ROUTES.items():
        if object_name.startswith(prefix):
            return config

    return None

@functions_framework.cloud_event
def gcs_reference_to_bigquery(cloud_event):
    data = cloud_event.data

    bucket = data["bucket"]
    object_name = data["name"]
    generation = str(data["generation"])

    logging.info(
        "Received object bucket=%s object=%s generation=%s",
        bucket,
        object_name,
        generation,
    )

    route = resolve_route(object_name)

    if route is None:
        logging.info("Ignoring unsupported object: %s", object_name)
        return

    if not object_name.endswith(".csv.gz"):
        logging.info("Ignoring non-CSV.GZ object: %s", object_name)
        return

    table_id = (
        f"{PROJECT_ID}."
        f"{DATASET_ID}."
        f"{route['table']}"
    )

    source_uri = f"gs://{bucket}/{object_name}"

    identity = f"{bucket}/{object_name}#{generation}"

    digest = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()[:32]

    job_id = f"gcs_ref_load_{digest}"

    client = bigquery.Client(project=PROJECT_ID)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        create_disposition=bigquery.CreateDisposition.CREATE_NEVER,
        encoding="UTF-8",
        allow_quoted_newlines=True,
        max_bad_records=0,
    )

    logging.info(
        "Starting BigQuery load source=%s destination=%s job_id=%s",
        source_uri,
        table_id,
        job_id,
    )

    try:
        job = client.load_table_from_uri(
            source_uri,
            table_id,
            job_id=job_id,
            location=BQ_LOCATION,
            job_config=job_config,
        )

    except Conflict:
        logging.warning(
            "BigQuery job already exists: %s",
            job_id,
        )

        job = client.get_job(
            job_id,
            location=BQ_LOCATION,
        )

    job.result()

    logging.info(
        "BigQuery load completed source=%s destination=%s rows=%s",
        source_uri,
        table_id,
        job.output_rows,
    )