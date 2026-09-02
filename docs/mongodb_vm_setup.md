# MongoDB VM Setup Validation

## Purpose

Validate that MongoDB can run on a Google Compute Engine VM and be accessed
securely from the local development machine through SSH tunneling.

## Compute Engine VM

- Instance: `glamira-mongodb`
- Zone: `asia-southeast1-b`
- Machine type: `e2-standard-4`
- vCPU: 4
- Memory: approximately 16 GB
- Operating system: Ubuntu 24.04 LTS
- Architecture: x86_64
- Boot disk: 30 GB balanced persistent disk

The boot disk is used for the operating system and MongoDB software.
MongoDB data capacity for the full dataset will be handled separately.

## MongoDB

Installed MongoDB versions:

- MongoDB Server: `8.0.29`
- MongoDB Shell: `2.10.0`

MongoDB runs as a Linux systemd service.

The service was validated as running successfully.

## Network Security

MongoDB port `27017` was not exposed directly to the public Internet.

Local access uses an SSH tunnel:

`localhost:27018 -> VM localhost:27017`

This allows the local development machine to access MongoDB without creating
a public firewall rule for the MongoDB service.

## Connectivity Validation

Local MongoDB connection:

`mongodb://localhost:27018`

MongoDB ping returned:

`{ ok: 1 }`

The MongoDB host information returned the Compute Engine VM hostname:

`glamira-mongodb.c.glamira-pipeline-506706.internal`

This confirms that the local MongoDB client successfully connected to the
MongoDB instance running on the GCP VM.

## Scope

This checkpoint validates infrastructure and connectivity only.

The full Glamira dataset has not been loaded into this MongoDB instance.

Data disk sizing, full dataset loading, and row-count reconciliation are part
of the next checkpoint.

## Checkpoint Result

**PASS**

The MongoDB Compute Engine VM is running and securely reachable from the local
development environment through SSH tunneling.