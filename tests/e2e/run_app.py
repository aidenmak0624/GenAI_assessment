"""
Prepare deterministic demo data for E2E tests, then launch Streamlit.

This keeps Playwright runs stable on a fresh checkout:
  - resets the SQLite database to seeded demo data
  - re-downloads the default public policy PDFs
  - rebuilds the vector store when OPENAI_API_KEY is available
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from data.generate_policies import DOCS_DIR, generate_all_policies
from data.init_db import DB_PATH, init_database
from utils.vector_store import VECTORSTORE_DIR, build_vector_store


def _remove_path(path_str: str) -> None:
    path = Path(path_str)
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink()


def prepare_demo_data() -> None:
    _remove_path(DB_PATH)
    _remove_path(f"{DB_PATH}-journal")
    _remove_path(DOCS_DIR)
    _remove_path(VECTORSTORE_DIR)

    init_database()
    generate_all_policies()

    if os.getenv("OPENAI_API_KEY"):
        build_vector_store()
    else:
        print("OPENAI_API_KEY not set; skipping vector store build for smoke tests.")


def main() -> None:
    os.chdir(ROOT)
    prepare_demo_data()

    port = os.getenv("PLAYWRIGHT_BASE_PORT", "8503")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
        "--server.port",
        port,
    ]
    os.execvp(command[0], command)


if __name__ == "__main__":
    main()
