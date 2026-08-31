#!/usr/bin/env python3
"""Download the approved primary-source NHANES research datasets.

This script intentionally downloads only the P0 public files. Large sensor
datasets and study-specific records have separate access, license, and protocol
considerations recorded in research/dataset_catalog.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_ROOT = PROJECT_ROOT / "research"
RAW = RESEARCH_ROOT / "datasets" / "raw"
CDC_BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public"

COLLECTIONS = {
    "nhanes_2021_2023": {
        "year": "2021",
        "files": ("BMX_L.xpt", "DEMO_L.xpt", "PAQ_L.xpt", "MCQ_L.xpt"),
        "readme": """# NHANES 2021--2023 current reference\n\nDownloaded from CDC/NCHS on demand by `scripts/research/fetch_priority_datasets.py`.\n\n- This is the primary current reference for demographics, body measures,\n  physical activity and self/proxy-reported medical conditions.\n- Join components using `SEQN` **only within this survey cycle**.\n- Use the documented interview or examination weights according to the joined\n  components and intended analysis.\n- Read each source codebook before selecting variables or treating a missing\n  value as a value.\n\nOfficial landing page: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023\n""",
    },
    "nhanes_2017_2018": {
        "year": "2017",
        "files": ("BMX_J.xpt", "DEMO_J.xpt", "DXX_J.xpt", "PAQ_J.xpt", "MCQ_J.xpt"),
        "readme": """# NHANES 2017--2018 core\n\nDownloaded from CDC/NCHS on demand by `scripts/research/fetch_priority_datasets.py`.\n\n- Join components using `SEQN` **only within this survey cycle**.\n- For estimates that include examination data, use the documented NHANES\n  examination weights (normally `WTMEC2YR`) and the component-specific analytic\n  guidance.\n- Read each source codebook before selecting variables or treating a missing\n  value as a value.\n\nOfficial landing page: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2017\n""",
    },
    "nhanes_2013_2014": {
        "year": "2013",
        "files": ("MGX_H.xpt", "BMX_H.xpt", "DEMO_H.xpt"),
        "readme": """# NHANES 2013--2014 grip-strength reference\n\nDownloaded from CDC/NCHS on demand by `scripts/research/fetch_priority_datasets.py`.\n\n- Join components using `SEQN` **only within this survey cycle**.\n- Inspect grip test status (`MGDEXSTS`) and effort fields before analysis.\n- Grip strength is a measured reference, not a proxy for a user's 1RM or a\n  clinical fitness clearance. Use documented examination weights and analytic\n  guidance for population estimates.\n\nOfficial landing page: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2013\n""",
    },
}


def file_metadata(url: str, destination: Path, status: str) -> dict[str, object]:
    digest = hashlib.sha256()
    with destination.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return {
        "path": str(destination.relative_to(RESEARCH_ROOT)),
        "status": status,
        "bytes": destination.stat().st_size,
        "sha256": digest.hexdigest(),
        "source_url": url,
    }


def fetch(url: str, destination: Path, force: bool) -> dict[str, object]:
    if destination.exists() and not force:
        return file_metadata(url, destination, "existing")

    temporary = destination.with_suffix(destination.suffix + ".part")
    request = Request(url, headers={"User-Agent": "TuxedoFitness research dataset fetcher/0.1"})
    print(f"Downloading {url}")
    with urlopen(request, timeout=60) as response, temporary.open("wb") as output:
        content_length = response.headers.get("Content-Length")
        expected = int(content_length) if content_length else None
        digest = hashlib.sha256()
        received = 0
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
            digest.update(chunk)
            received += len(chunk)

    if expected is not None and received != expected:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Incomplete download for {destination.name}: {received} of {expected} bytes")
    if received == 0:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Empty download for {destination.name}")

    temporary.replace(destination)
    return file_metadata(url, destination, "downloaded")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--collection",
        choices=tuple(COLLECTIONS),
        action="append",
        help="Download only this collection. Repeat to select more than one.",
    )
    parser.add_argument("--force", action="store_true", help="Re-download files that already exist.")
    args = parser.parse_args()

    selected = args.collection or list(COLLECTIONS)
    manifest = {"catalog_version": "2026-08-27", "downloads": []}
    for collection_name in selected:
        collection = COLLECTIONS[collection_name]
        target = RAW / collection_name
        target.mkdir(parents=True, exist_ok=True)
        (target / "README.md").write_text(collection["readme"], encoding="utf-8")
        for filename in collection["files"]:
            url = f"{CDC_BASE}/{collection['year']}/DataFiles/{filename}"
            manifest["downloads"].append(fetch(url, target / filename, args.force))

    manifest_path = RAW / "download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {manifest_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # Keep the raw data directory free of partial files.
        print(f"Download failed: {error}", file=sys.stderr)
        raise SystemExit(1)
