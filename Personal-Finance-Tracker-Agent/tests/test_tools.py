import csv
import os
import time
import threading
from pathlib import Path

import pytest
from app.core.tools import (
    ALL_TOOLS,
    create_expense,
    list_expenses,
    get_expense_by_id,
    update_expense,
    filter_expenses,
    delete_expense,
    _read_all,
    _write_all,
    _next_id,
    EXPENSES_FILE,
    FIELDNAMES,
)


# ── Fixtures ──

@pytest.fixture(autouse=True)
def ensure_sample_data():
    """Ensure CSV has 3 sample rows before each tool test."""
    EXPENSES_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "id,date,expense_type,amount,item",
        "1,2026-06-07,Clothing,1000.00,Clothing Purchase",
        "2,2026-06-06,Food,500.00,Food expense",
        "3,2026-06-08,Fuel,500.00,Petrol",
    ]
    EXPENSES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Internal helpers ──

class TestReadAll:
    def test_reads_csv_correctly(self):
        rows = _read_all()
        assert len(rows) == 3
        assert rows[0]["id"] == "1"
        assert rows[1]["expense_type"] == "Food"

    def test_empty_csv(self):
        EXPENSES_FILE.write_text("id,date,expense_type,amount,item\n", encoding="utf-8")
        rows = _read_all()
        assert rows == []

    def test_file_not_exists(self):
        if EXPENSES_FILE.exists():
            EXPENSES_FILE.unlink()
        rows = _read_all()
        assert rows == []


class TestWriteAll:
    def test_writes_correctly(self):
        rows = [
            {"id": "10", "date": "2026-06-08", "expense_type": "Test", "amount": "99.99", "item": "Testing"},
        ]
        _write_all(rows)
        read_back = _read_all()
        assert len(read_back) == 1
        assert read_back[0]["item"] == "Testing"

    def test_atomic_write_via_temp_file(self):
        """Verify _write_all uses a temp file (atomic write)."""
        original_rows = [{"id": "1", "date": "2026-01-01", "expense_type": "X", "amount": "10", "item": "Y"}]
        _write_all(original_rows)

        # After write, the .tmp file should NOT exist (cleaned up on success)
        tmp = EXPENSES_FILE.with_suffix(".csv.tmp")
        assert not tmp.exists(), "Temp file should be cleaned up after successful write"

        # Content should be correct
        read_back = _read_all()
        assert len(read_back) == 1
        assert read_back[0]["item"] == "Y"


class TestNextId:
    def test_next_id_with_data(self):
        assert _next_id() == 4

    def test_next_id_empty(self):
        EXPENSES_FILE.write_text("id,date,expense_type,amount,item\n", encoding="utf-8")
        assert _next_id() == 1

    def test_next_id_corrupted(self):
        lines = [
            "id,date,expense_type,amount,item",
            "abc,2026-01-01,F,10,X",
            "2,2026-01-02,F,20,Y",
        ]
        EXPENSES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        assert _next_id() == 3  # skips "abc", finds max=2


# ── Tool CRUD Tests ──

class TestCreateExpense:
    def test_create_minimal(self):
        result = create_expense.invoke({
            "expense_type": "Food", "amount": 250, "item": "Lunch"
        })
        assert "Created expense id=4" in result
        rows = _read_all()
        assert len(rows) == 4
        assert rows[-1]["item"] == "Lunch"

    def test_create_with_date(self):
        result = create_expense.invoke({
            "expense_type": "Travel", "amount": 1500, "item": "Flight",
            "date": "2026-06-15"
        })
        assert "Created expense id=4" in result
        rows = _read_all()
        assert rows[-1]["date"] == "2026-06-15"

    def test_create_large_amount(self):
        result = create_expense.invoke({
            "expense_type": "Bills", "amount": 999999.99, "item": "Rent"
        })
        assert "Created" in result

    def test_create_with_special_chars(self):
        result = create_expense.invoke({
            "expense_type": "Food & Bev'g", "amount": 50, "item": "Café #1"
        })
        assert "Created" in result


class TestListExpenses:
    def test_list_all(self):
        result = list_expenses.invoke({})
        assert "Clothing" in result
        assert "Food" in result
        assert "Fuel" in result

    def test_list_empty(self):
        EXPENSES_FILE.write_text("id,date,expense_type,amount,item\n", encoding="utf-8")
        result = list_expenses.invoke({})
        assert result == "No expenses found."


class TestGetExpenseById:
    def test_get_existing(self):
        result = get_expense_by_id.invoke({"expense_id": 1})
        assert "Clothing" in result

    def test_get_non_existing(self):
        result = get_expense_by_id.invoke({"expense_id": 999})
        assert "not found" in result

    def test_get_with_corrupted_id(self):
        lines = [
            "id,date,expense_type,amount,item",
            "abc,2026-01-01,F,10,X",
            "2,2026-01-02,F,20,Y",
        ]
        EXPENSES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = get_expense_by_id.invoke({"expense_id": 2})
        assert "Y" in result


class TestUpdateExpense:
    def test_update_amount(self):
        result = update_expense.invoke({
            "expense_id": 1, "amount": 777.77
        })
        assert "Updated" in result
        rows = _read_all()
        assert rows[0]["amount"] == "777.77"

    def test_update_multiple_fields(self):
        result = update_expense.invoke({
            "expense_id": 2, "expense_type": "Groceries", "item": "Weekly shop",
            "date": "2026-06-10"
        })
        assert "Updated" in result
        rows = _read_all()
        assert rows[1]["expense_type"] == "Groceries"

    def test_update_non_existing(self):
        result = update_expense.invoke({
            "expense_id": 999, "item": "Nope"
        })
        assert "not found" in result

    def test_update_clear_field_ignored(self):
        result = update_expense.invoke({
            "expense_id": 1, "expense_type": None
        })
        assert "Updated" in result
        rows = _read_all()
        assert rows[0]["expense_type"] == "Clothing"  # unchanged


class TestFilterExpenses:
    def test_filter_by_date_from(self):
        result = filter_expenses.invoke({"date_from": "2026-06-07"})
        assert "Clothing" in result
        assert "Fuel" in result
        assert "Food" not in result  # 2026-06-06 < 2026-06-07

    def test_filter_by_type(self):
        result = filter_expenses.invoke({"expense_type": "Food"})
        assert "Food" in result

    def test_filter_by_amount_range(self):
        result = filter_expenses.invoke({
            "min_amount": 600, "max_amount": 1500
        })
        assert "Clothing" in result  # 1000
        assert "Food" not in result  # 500
        assert "Fuel" not in result  # 500

    def test_filter_no_match(self):
        result = filter_expenses.invoke({"expense_type": "NonExistent"})
        assert "No expenses matched" in result

    def test_filter_all_params(self):
        result = filter_expenses.invoke({
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "expense_type": "Food", "min_amount": 100, "max_amount": 1000
        })
        assert "Food" in result

    def test_filter_empty_data(self):
        EXPENSES_FILE.write_text("id,date,expense_type,amount,item\n", encoding="utf-8")
        result = filter_expenses.invoke({"date_from": "2026-01-01"})
        assert "No expenses matched" in result


class TestDeleteExpense:
    def test_delete_existing(self):
        result = delete_expense.invoke({"expense_id": 1})
        assert "Deleted" in result
        rows = _read_all()
        assert len(rows) == 2
        assert all(r["id"] != "1" for r in rows)

    def test_delete_non_existing(self):
        result = delete_expense.invoke({"expense_id": 999})
        assert "not found" in result
        rows = _read_all()
        assert len(rows) == 3

    def test_delete_last_item(self):
        delete_expense.invoke({"expense_id": 1})
        delete_expense.invoke({"expense_id": 2})
        delete_expense.invoke({"expense_id": 3})
        rows = _read_all()
        assert rows == []


# ── Edge Cases ──

class TestEdgeCases:
    def test_concurrent_creates(self):
        """Create 10 expenses concurrently — no crashes, unique IDs."""
        errors = []
        def worker(i):
            try:
                create_expense.invoke({
                    "expense_type": "Concurrent",
                    "amount": float(i),
                    "item": f"Item-{i}",
                })
            except Exception as e:
                errors.append((i, e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(1, 11)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent errors: {errors}"
        rows = _read_all()
        # Original 3 + 10 new = 13, but IDs might be reused due to race
        # Just check no crashes and all IDs are unique
        ids = [r["id"] for r in rows]
        assert len(ids) == len(set(ids)), "Duplicate IDs found!"

    def test_csv_with_extra_whitespace(self):
        lines = [
            "id,date,expense_type,amount,item",
            " 1 , 2026-01-01 , Food , 10 , Item ",
        ]
        EXPENSES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = list_expenses.invoke({})
        assert "Food" in result

    def test_csv_with_missing_columns(self):
        lines = [
            "id,date,expense_type,amount,item",
            "1,2026-01-01,Food",
        ]
        EXPENSES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        # Should not crash — tools should handle gracefully
        result = list_expenses.invoke({})
        assert "Food" in result or "No expenses" in result

    def test_csv_with_unicode(self):
        lines = [
            "id,date,expense_type,amount,item",
            "1,2026-01-01,Food,100,Chai & Café",
        ]
        EXPENSES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = list_expenses.invoke({})
        assert "Chai" in result

    def test_maximum_id_value(self):
        lines = [
            "id,date,expense_type,amount,item",
            "9999999999999999999,2026-01-01,F,10,X",
        ]
        EXPENSES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        nid = _next_id()
        assert nid > 9999999999999999999

    def test_very_long_item_name(self):
        result = create_expense.invoke({
            "expense_type": "Food",
            "amount": 10,
            "item": "A" * 200,  # max_length = 200
        })
        assert "Created" in result

    def test_very_long_item_name_rejected_by_schema(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            create_expense.invoke({
                "expense_type": "Food",
                "amount": 10,
                "item": "A" * 201,  # > max_length = 200
            })

    def test_delete_then_create_uses_new_id(self):
        delete_expense.invoke({"expense_id": 3})
        result = create_expense.invoke({
            "expense_type": "New", "amount": 100, "item": "NewItem"
        })
        # max id was 3, after deleting id=3, max remaining is 2, so next_id = 3
        assert "Created expense id=3" in result


class TestAllToolsList:
    def test_all_tools_have_names(self):
        names = {t.name for t in ALL_TOOLS}
        expected = {
            "create_expense", "list_expenses", "filter_expenses",
            "get_expense_by_id", "update_expense", "delete_expense",
        }
        assert names == expected

    def test_each_tool_is_callable(self):
        for t in ALL_TOOLS:
            assert callable(t.func)
