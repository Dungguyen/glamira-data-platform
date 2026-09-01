# GCP Setup Validation

## Project

Project ID:

`glamira-pipeline-506706`

## Cloud Storage

Raw bucket:

`gs://glamira-raw-data-506706`

Region:

`ASIA-SOUTHEAST1`

Storage class:

`STANDARD`

## API Validation

The following required Cloud Storage APIs were confirmed as enabled:

- `storage.googleapis.com`
- `storage-component.googleapis.com`

BigQuery Storage API was also observed as enabled:

- `bigquerystorage.googleapis.com`

BigQuery is not part of this checkpoint and was not configured further.

## Object Storage Validation

A small test object was created locally:

`gcs_test.txt`

The following operations were validated successfully:

1. Upload local file to GCS
2. List uploaded object
3. Download object from GCS
4. Verify downloaded content
5. Delete object from GCS
6. Confirm object no longer exists

Test path:

`gs://glamira-raw-data-506706/tests/gcs_test.txt`

The test object and local temporary files were removed after validation.

## Raw Dataset

Source object:

`gs://glamira-raw-data-506706/summary.bson`

The raw BSON source is stored outside Git and must not be committed to GitHub.

## IAM / Access Observation

The current bucket configuration reports:

`uniform_bucket_level_access: false`

This means bucket/object ACL behavior is still available.

No IAM model changes were performed in this checkpoint.

Access-control hardening should be reviewed separately before production deployment.

## Checkpoint Result

The following capabilities were validated:

- Correct GCP project selected
- Cloud Storage API enabled
- Bucket metadata accessible
- Object listing works
- Object upload works
- Object download works
- Object deletion works

**Checkpoint status: PASS**