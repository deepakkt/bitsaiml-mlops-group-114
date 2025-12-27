#!/usr/bin/env python
"""
Placeholder dataset acquisition script.

Part-2 will add real download + preprocessing of the UCI Heart Disease dataset.
For now, this script ensures expected directories exist and drops a metadata stub.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.heart.config import settings


def main() -> None:
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "status": "placeholder",
        "note": "Real download implemented in Part-2.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    meta_path = settings.raw_data_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    print(f"Metadata stub written to {meta_path}")


if __name__ == "__main__":
    main()
