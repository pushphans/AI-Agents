import os
import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CSV_FILE = DATA_DIR / "expenses.csv"


@pytest.fixture(autouse=True)
def backup_and_restore_csv():
    """Backup CSV before each test, restore after."""
    backup = None
    if CSV_FILE.exists():
        backup = CSV_FILE.with_suffix(".csv.bak")
        shutil.copy2(CSV_FILE, backup)
    yield
    if backup and backup.exists():
        shutil.copy2(backup, CSV_FILE)
        backup.unlink()
    elif backup is None:
        if CSV_FILE.exists():
            CSV_FILE.unlink()


@pytest.fixture
def sample_csv():
    """Create CSV with 3 sample rows."""
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "id,date,expense_type,amount,item",
        "1,2026-06-07,Clothing,1000.00,Clothing Purchase",
        "2,2026-06-06,Food,500.00,Food expense",
        "3,2026-06-08,Fuel,500.00,Petrol",
    ]
    CSV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    yield
