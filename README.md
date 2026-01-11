# cvec-db

CVE Database Builder - generates parquet files for the [cvec](https://github.com/your-org/cvec) tool.

## Overview

This repository provides the infrastructure for building and distributing pre-built CVE parquet databases. Instead of each user downloading and processing the raw CVE JSON files (which is slow and disk-intensive), we build the parquet files centrally and distribute them via GitHub Releases.

## How it Works

1. **Daily builds**: A GitHub Action runs daily to download the latest CVE data from the [cvelistV5](https://github.com/CVEProject/cvelistV5) repository
2. **Extraction**: The data is extracted into normalized parquet files using the `cvec` library
3. **Embeddings**: Semantic embeddings are generated using sentence-transformers (all-MiniLM-L6-v2 model) for semantic search (this currently takes over an hour, this needs to be optimized someday)
4. **Manifest**: A manifest file is generated with checksums for integrity verification
5. **Release**: The parquet files are published as a GitHub Release

## Schema Versioning

The parquet files include a `manifest.json` with a `schema_version` field. The cvec tool checks this version before downloading to ensure compatibility. When the parquet schema changes in a breaking way, this version is incremented.

## Files Produced

| File | Description |
|------|-------------|
| `cves.parquet` | Core CVE metadata (1:1 with CVE) |
| `cve_descriptions.parquet` | All descriptions with language info |
| `cve_metrics.parquet` | CVSS metrics with full component breakdown |
| `cve_products.parquet` | Affected products |
| `cve_versions.parquet` | Version ranges per product |
| `cve_cwes.parquet` | CWE/problem types |
| `cve_references.parquet` | References with tags |
| `cve_credits.parquet` | Credits/acknowledgments |
| `cve_tags.parquet` | CVE-level tags |
| `cve_embeddings.parquet` | Embeddings for semantic search (384-dimensional vectors) |
| `manifest.json` | Metadata, statistics, and checksums |

## Local Development

🚧 TODO 🚧

## Manual Release Trigger

🚧 TODO 🚧

## Usage with cvec

🚧 TODO 🚧

## License

MIT