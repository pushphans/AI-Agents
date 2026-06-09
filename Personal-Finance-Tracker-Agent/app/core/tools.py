import csv
import os
import threading
from datetime import date as _date
from pathlib import Path
from typing import Optional

from langchain.tools import tool
from pydantic import BaseModel, Field

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
EXPENSES_FILE = DATA_DIR / "expenses.csv"
FIELDNAMES = ["id", "date", "expense_type", "amount", "item"]

_lock = threading.Lock()


def _ensure_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not EXPENSES_FILE.exists():
        with EXPENSES_FILE.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()


def _read_all() -> list[dict]:
    _ensure_file()
    with EXPENSES_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [r for r in reader if any(v.strip() for v in r.values())]


def _write_all(rows: list[dict]) -> None:
    _ensure_file()
    tmp = EXPENSES_FILE.with_suffix(".csv.tmp")
    try:
        with tmp.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, EXPENSES_FILE)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def _next_id() -> int:
    rows = _read_all()
    max_id = 0
    for r in rows:
        try:
            rid = int(r.get("id", 0))
            if rid > max_id:
                max_id = rid
        except (ValueError, TypeError):
            continue
    return max_id + 1


def _is_blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _safe_str(row: dict, key: str, default: str = "") -> str:
    val = row.get(key, default)
    return str(val) if val is not None else default


# ──────────────────────────── Pydantic schemas ────────────────────────────

_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"


class CreateExpenseSchema(BaseModel):
    expense_type: str = Field(
        min_length=1, max_length=50,
        description="Category of the expense, e.g. 'Food', 'Travel', 'Bills'",
    )
    amount: float = Field(
        gt=0,
        description="Numeric amount spent (no currency symbol). Must be positive.",
    )
    item: str = Field(
        min_length=1, max_length=200,
        description="Short description of what was purchased",
    )
    date: Optional[str] = Field(
        default=None, pattern=_DATE_PATTERN,
        description="Date in YYYY-MM-DD format. Defaults to today if omitted.",
    )

    model_config = {"extra": "forbid"}


class GetExpenseByIdSchema(BaseModel):
    expense_id: int = Field(
        gt=0,
        description="Numeric id of the expense",
    )

    model_config = {"extra": "forbid"}


class UpdateExpenseSchema(BaseModel):
    expense_id: int = Field(
        gt=0,
        description="Numeric id of the expense to update",
    )
    date: Optional[str] = Field(
        default=None, pattern=_DATE_PATTERN,
        description="Date in YYYY-MM-DD format",
    )
    expense_type: Optional[str] = Field(
        default=None, min_length=1, max_length=50,
        description="Category of the expense",
    )
    amount: Optional[float] = Field(
        default=None, gt=0,
        description="Numeric amount spent (no currency symbol). Must be positive.",
    )
    item: Optional[str] = Field(
        default=None, min_length=1, max_length=200,
        description="Short description of what was purchased",
    )

    model_config = {"extra": "forbid"}


class FilterExpensesSchema(BaseModel):
    date_from: Optional[str] = Field(
        default=None, pattern=_DATE_PATTERN,
        description="Inclusive lower bound for date, YYYY-MM-DD",
    )
    date_to: Optional[str] = Field(
        default=None, pattern=_DATE_PATTERN,
        description="Inclusive upper bound for date, YYYY-MM-DD",
    )
    expense_type: Optional[str] = Field(
        default=None, min_length=1, max_length=50,
        description="Exact (case-insensitive) match on the expense_type column",
    )
    item_contains: Optional[str] = Field(
        default=None, max_length=200,
        description="Substring match (case-insensitive) on the item column",
    )
    min_amount: Optional[float] = Field(
        default=None, ge=0,
        description="Inclusive lower bound for amount",
    )
    max_amount: Optional[float] = Field(
        default=None, ge=0,
        description="Inclusive upper bound for amount",
    )

    model_config = {"extra": "forbid"}


class DeleteExpenseSchema(BaseModel):
    expense_id: int = Field(
        gt=0,
        description="Numeric id of the expense to delete",
    )

    model_config = {"extra": "forbid"}


# ──────────────────────────── Tools ────────────────────────────


@tool(args_schema=CreateExpenseSchema)
def create_expense(
    expense_type: str,
    amount: float,
    item: str,
    date: Optional[str] = None,
) -> str:
    """Add a new expense entry to the spreadsheet.

    Args:
        expense_type: Category of the expense, e.g. "Food", "Travel", "Bills".
        amount: Numeric amount spent (no currency symbol).
        item: Short description of what was purchased.
        date: Date in YYYY-MM-DD format. Defaults to today if omitted.
    """
    try:
        with _lock:
            _ensure_file()
            row = {
                "id": _next_id(),
                "date": date or _date.today().isoformat(),
                "expense_type": expense_type.strip(),
                "amount": f"{amount:.2f}",
                "item": item.strip(),
            }
            with EXPENSES_FILE.open("a", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=FIELDNAMES).writerow(row)
        return f"Created expense id={row['id']} for {row['item']} on {row['date']}."
    except Exception as e:
        return f"Error creating expense: {type(e).__name__}: {e}"


@tool
def list_expenses() -> str:
    """Return every expense row as a markdown table."""
    try:
        with _lock:
            rows = _read_all()
        if not rows:
            return "No expenses found."
        header = "| " + " | ".join(FIELDNAMES) + " |"
        sep = "| " + " | ".join("---" for _ in FIELDNAMES) + " |"
        body = "\n".join(
            "| " + " | ".join(str(r.get(c, "")) for c in FIELDNAMES) + " |"
            for r in rows
        )
        return f"{header}\n{sep}\n{body}"
    except Exception as e:
        return f"Error listing expenses: {type(e).__name__}: {e}"


@tool(args_schema=GetExpenseByIdSchema)
def get_expense_by_id(expense_id: int) -> str:
    """Fetch a single expense row by its numeric id."""
    try:
        with _lock:
            for row in _read_all():
                try:
                    rid = int(row.get("id", -1))
                except (ValueError, TypeError):
                    continue
                if rid == expense_id:
                    return ", ".join(f"{k}={_safe_str(row, k)}" for k in FIELDNAMES)
        return f"Expense with id={expense_id} not found."
    except Exception as e:
        return f"Error fetching expense: {type(e).__name__}: {e}"


@tool(args_schema=UpdateExpenseSchema)
def update_expense(
    expense_id: int,
    date: Optional[str] = None,
    expense_type: Optional[str] = None,
    amount: Optional[float] = None,
    item: Optional[str] = None,
) -> str:
    """Update one or more fields of an existing expense.

    Only the fields that are explicitly provided are changed; leave a field
    blank/None to keep its current value.
    """
    try:
        with _lock:
            rows = _read_all()
            for row in rows:
                try:
                    rid = int(row.get("id", -1))
                except (ValueError, TypeError):
                    continue
                if rid == expense_id:
                    if not _is_blank(date):
                        row["date"] = date
                    if not _is_blank(expense_type):
                        row["expense_type"] = expense_type.strip()
                    if not _is_blank(amount):
                        row["amount"] = f"{amount:.2f}"
                    if not _is_blank(item):
                        row["item"] = item.strip()
                    _write_all(rows)
                    return f"Updated expense id={expense_id}."
        return f"Expense with id={expense_id} not found."
    except Exception as e:
        return f"Error updating expense: {type(e).__name__}: {e}"


@tool(args_schema=FilterExpensesSchema)
def filter_expenses(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    expense_type: Optional[str] = None,
    item_contains: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> str:
    """Filter expenses by one or more columns. All filters are optional and combined with AND.

    Args:
        date_from: Inclusive lower bound for date, YYYY-MM-DD.
        date_to: Inclusive upper bound for date, YYYY-MM-DD.
        expense_type: Exact (case-insensitive) match on the expense_type column.
        item_contains: Substring match (case-insensitive) on the item column.
        min_amount: Inclusive lower bound for amount.
        max_amount: Inclusive upper bound for amount.
    """
    try:
        with _lock:
            rows = _read_all()

        def keep(row: dict) -> bool:
            row_date = _safe_str(row, "date")
            row_type = _safe_str(row, "expense_type")
            row_item = _safe_str(row, "item")
            row_amt_str = _safe_str(row, "amount")

            if not _is_blank(date_from) and row_date < date_from:
                return False
            if not _is_blank(date_to) and row_date > date_to:
                return False
            if not _is_blank(expense_type) and row_type.lower() != expense_type.strip().lower():
                return False
            if not _is_blank(item_contains) and item_contains.lower() not in row_item.lower():
                return False
            try:
                amt = float(row_amt_str) if row_amt_str else 0.0
            except (ValueError, TypeError):
                return False
            if not _is_blank(min_amount) and amt < min_amount:
                return False
            if not _is_blank(max_amount) and amt > max_amount:
                return False
            return True

        matched = sorted([r for r in rows if keep(r)], key=lambda r: r.get("date", ""), reverse=True)
        if not matched:
            return "No expenses matched the given filters."
        header = "| " + " | ".join(FIELDNAMES) + " |"
        sep = "| " + " | ".join("---" for _ in FIELDNAMES) + " |"
        body = "\n".join(
            "| " + " | ".join(_safe_str(r, c) for c in FIELDNAMES) + " |" for r in matched
        )
        return f"{header}\n{sep}\n{body}"
    except Exception as e:
        return f"Error filtering expenses: {type(e).__name__}: {e}"


@tool(args_schema=DeleteExpenseSchema)
def delete_expense(expense_id: int) -> str:
    """Remove an expense row from the spreadsheet by its id."""
    try:
        with _lock:
            rows = _read_all()
            kept = []
            found = False
            for r in rows:
                try:
                    rid = int(r.get("id", -1))
                except (ValueError, TypeError):
                    kept.append(r)
                    continue
                if rid == expense_id:
                    found = True
                else:
                    kept.append(r)
            if not found:
                return f"Expense with id={expense_id} not found."
            _write_all(kept)
        return f"Deleted expense id={expense_id}."
    except Exception as e:
        return f"Error deleting expense: {type(e).__name__}: {e}"


ALL_TOOLS = [
    create_expense,
    list_expenses,
    filter_expenses,
    get_expense_by_id,
    update_expense,
    delete_expense,
]
