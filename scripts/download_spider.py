"""Download Spider 1.0 from the official Yale-linked Google Drive file.

Spider is optional for this portfolio's runnable Chinook demo. This script keeps
its separate license/provenance clear and avoids committing the large benchmark.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

FILE_ID = "1403EGqzIDoHMdQF4c9Bkyl7dZLZ5Wt6J"
OUTPUT = Path("data/spider/spider_data.zip")


def main() -> None:
    if shutil.which("gdown") is None:
        raise SystemExit(
            "The official Spider file is hosted on Google Drive. Install gdown with "
            "`python -m pip install gdown`, then run this script again."
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    command = ["gdown", "--id", FILE_ID, "--output", str(OUTPUT)]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    print(f"Downloaded Spider archive to {OUTPUT}")
    print("Verify the current license and release notes on https://yale-lily.github.io/spider before use.")


if __name__ == "__main__":
    main()
