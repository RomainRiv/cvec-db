"""CVE Database Builder - generates parquet files for cvec tool."""

__version__ = "0.1.0"

# Import schema version from cvec to ensure consistency
from cvec import MANIFEST_SCHEMA_VERSION
