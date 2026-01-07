"""CLI for cvec-db - CVE database builder."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

from cvec.core.config import Config
from cvec.services.downloader import DownloadService
from cvec.services.extractor import ExtractorService

from cvec_db import MANIFEST_SCHEMA_VERSION

app = typer.Typer(
    name="cvec-db",
    help="CVE database builder - generates parquet files for cvec tool",
    no_args_is_help=True,
)


def create_manifest(output_dir: Path, stats: dict) -> Path:
    """Create a manifest file with metadata about the generated parquet files.
    
    The manifest includes:
    - Schema version for compatibility checking
    - Generation timestamp
    - Statistics about the data
    - List of parquet files with their checksums
    
    Args:
        output_dir: Directory containing the parquet files
        stats: Statistics from the extraction process
        
    Returns:
        Path to the created manifest file
    """
    import hashlib
    
    parquet_files = []
    for pq_file in sorted(output_dir.glob("*.parquet")):
        # Calculate SHA256 hash
        sha256 = hashlib.sha256()
        with open(pq_file, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        
        parquet_files.append({
            "name": pq_file.name,
            "size": pq_file.stat().st_size,
            "sha256": sha256.hexdigest(),
        })
    
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cvec_db_version": "0.1.0",
        "stats": stats,
        "files": parquet_files,
    }
    
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    
    return manifest_path


@app.command()
def build(
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for parquet files"
    ),
    years: int = typer.Option(
        10, "--years", "-y", help="Number of years to include"
    ),
    skip_download: bool = typer.Option(
        False, "--skip-download", help="Skip downloading, use existing JSON files"
    ),
) -> None:
    """Build the CVE database: download JSON files and extract to parquet.
    
    This is the main command for building the database. It:
    1. Downloads CVE JSON files from GitHub cvelistV5 repository
    2. Extracts the data into normalized parquet files
    3. Creates a manifest file with checksums for verification
    """
    output_dir = output_dir or Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    config = Config()
    config.default_years = years
    config.data_dir = output_dir
    
    if not skip_download:
        typer.echo(f"Downloading CVE data (last {years} years)...")
        downloader = DownloadService(config)
        downloader.download_cves()
        downloader.extract_cves()
        typer.echo("Download complete.")
    
    typer.echo("Extracting CVE data to parquet...")
    extractor = ExtractorService(config)
    result = extractor.extract_all(output_dir=output_dir)
    
    stats = result.get("stats", {})
    typer.echo(f"Extracted {stats.get('cves', 0)} CVEs")
    
    typer.echo("Creating manifest...")
    manifest_path = create_manifest(output_dir, stats)
    typer.echo(f"Manifest created: {manifest_path}")
    
    typer.echo("Build complete!")


@app.command()
def download_json(
    years: int = typer.Option(
        10, "--years", "-y", help="Number of years to include"
    ),
) -> None:
    """Download CVE JSON files from GitHub cvelistV5 repository.
    
    This downloads the raw JSON files without extracting to parquet.
    Useful for debugging or if you need the original JSON data.
    """
    config = Config()
    config.default_years = years
    
    typer.echo(f"Downloading CVE data (last {years} years)...")
    downloader = DownloadService(config)
    downloader.download_cves()
    count = downloader.extract_cves()
    typer.echo(f"Downloaded and extracted {count} CVE JSON files")


@app.command()
def extract_parquet(
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for parquet files"
    ),
    years: int = typer.Option(
        10, "--years", "-y", help="Number of years to include"
    ),
) -> None:
    """Extract CVE JSON files to parquet format.
    
    This assumes JSON files have already been downloaded.
    Use 'download-json' first if you haven't downloaded the data.
    """
    output_dir = output_dir or Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    config = Config()
    config.default_years = years
    config.data_dir = output_dir
    
    typer.echo("Extracting CVE data to parquet...")
    extractor = ExtractorService(config)
    result = extractor.extract_all(output_dir=output_dir)
    
    stats = result.get("stats", {})
    typer.echo(f"Extracted {stats.get('cves', 0)} CVEs")
    
    typer.echo("Creating manifest...")
    manifest_path = create_manifest(output_dir, stats)
    typer.echo(f"Manifest created: {manifest_path}")


@app.command()
def manifest(
    data_dir: Optional[Path] = typer.Option(
        None, "--data-dir", "-d", help="Directory containing parquet files"
    ),
) -> None:
    """Generate a manifest file for existing parquet files.
    
    This creates a manifest.json with checksums for all parquet files
    in the specified directory. Useful after manual modifications.
    """
    data_dir = data_dir or Path("data")
    
    if not data_dir.exists():
        typer.echo(f"Error: Directory {data_dir} does not exist", err=True)
        raise typer.Exit(1)
    
    # Read existing stats from parquet if available
    stats = {}
    cves_parquet = data_dir / "cves.parquet"
    if cves_parquet.exists():
        import polars as pl
        df = pl.read_parquet(cves_parquet)
        stats["cves"] = len(df)
    
    manifest_path = create_manifest(data_dir, stats)
    typer.echo(f"Manifest created: {manifest_path}")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
