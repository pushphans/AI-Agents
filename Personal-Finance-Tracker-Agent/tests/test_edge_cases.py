"""
Edge case tests for the Personal Finance Tracker Agent.
"""
import csv
import os
import threading
from pathlib import Path

import pytest
from app.core.tools import (
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
    DATA_DIR,
    FIELDNAMES,
)


# ── Helper ──

def _reset_csv():
    EXPENSES_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "id,date,expense_type,amount,item",
        "1,2026-06-07,Clothing,1000.00,Clothing Purchase",
        "2,2026-06-06,Food,500.00,Food expense",
        "3,2026-06-08,Fuel,500.00,Petrol",
    ]
    EXPENSES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.fixture(autouse=True)
def sample_data():
    _reset_csv()
    yield


# ── File System Edge Cases ──

class TestFileSystemEdgeCases:
    def test_data_dir_not_exists(self):
        import shutil
        if DATA_DIR.exists():
            shutil.rmtree(DATA_DIR)
        result = create_expense.invoke({
            "expense_type": "Food", "amount": 100, "item": "Test"
        })
        assert "Created" in result
        assert DATA_DIR.exists()
        assert EXPENSES_FILE.exists()

    def test_csv_file_readonly(self):
        try:
            os.chmod(EXPENSES_FILE, 0o444)
            result = create_expense.invoke({
                "expense_type": "Food", "amount": 100, "item": "Test"
            })
            assert isinstance(result, str)
        finally:
            os.chmod(EXPENSES_FILE, 0o644)

    def test_corrupted_csv_invalid_numbers(self):
        lines = [
            "id,date,expense_type,amount,item",
            "1,2026-01-01,F,not-a-number,X",
            "2,2026-01-02,F,20,Y",
        ]
        EXPENSES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = filter_expenses.invoke({"min_amount": 10})
        assert "Y" in result

    def test_corrupted_csv_empty_fields(self):
        lines = [
            "id,date,expense_type,amount,item",
            "1,2026-01-01,,,",
            "2,2026-01-02,F,20,Y",
        ]
        EXPENSES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = list_expenses.invoke({})
        assert "Y" in result

    def test_corrupted_csv_duplicate_ids(self):
        lines = [
            "id,date,expense_type,amount,item",
            "1,2026-01-01,F,10,First",
            "1,2026-01-02,F,20,Second",
        ]
        EXPENSES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = get_expense_by_id.invoke({"expense_id": 1})
        assert "First" in result

    def test_corrupted_csv_only_header(self):
        EXPENSES_FILE.write_text("id,date,expense_type,amount,item\n", encoding="utf-8")
        assert list_expenses.invoke({}) == "No expenses found."
        assert "No expenses matched" in filter_expenses.invoke({"date_from": "2026-01-01"})

    def test_corrupted_csv_empty_file(self):
        EXPENSES_FILE.write_text("", encoding="utf-8")
        result = list_expenses.invoke({})
        assert "No expenses" in result


# ── Input Boundary Edge Cases ──

class TestInputBoundaries:
    def test_amount_just_above_zero(self):
        result = create_expense.invoke({
            "expense_type": "Food", "amount": 0.01, "item": "Candy"
        })
        assert "Created" in result

    def test_amount_very_large(self):
        result = create_expense.invoke({
            "expense_type": "Bills", "amount": 1e9, "item": "Large"
        })
        assert "Created" in result

    def test_expense_type_min_length_1(self):
        result = create_expense.invoke({
            "expense_type": "F", "amount": 10, "item": "X"
        })
        assert "Created" in result

    def test_item_min_length_1(self):
        result = create_expense.invoke({
            "expense_type": "Food", "amount": 10, "item": "X"
        })
        assert "Created" in result

    def test_expense_type_max_length_50(self):
        result = create_expense.invoke({
            "expense_type": "A" * 50, "amount": 10, "item": "X"
        })
        assert "Created" in result

    def test_item_max_length_200(self):
        result = create_expense.invoke({
            "expense_type": "Food", "amount": 10, "item": "A" * 200
        })
        assert "Created" in result

    def test_filter_min_amount_zero(self):
        """min_amount = 0 should include all expenses."""
        result = filter_expenses.invoke({"min_amount": 0})
        assert "Clothing" in result

    def test_filter_max_amount_very_large(self):
        """max_amount very large should include all."""
        result = filter_expenses.invoke({"max_amount": 1e9})
        assert "Clothing" in result


# ── Concurrency Edge Cases ──

class TestConcurrencyEdgeCases:
    def test_concurrent_read_and_write(self):
        results = []
        errors = []

        def reader():
            try:
                for _ in range(20):
                    list_expenses.invoke({})
                results.append("reader_ok")
            except Exception as e:
                errors.append(f"reader: {e}")

        def writer():
            try:
                for i in range(1, 21):  # Start from 1 to avoid 0
                    create_expense.invoke({
                        "expense_type": "Test",
                        "amount": float(i),
                        "item": f"Item-{i}",
                    })
                results.append("writer_ok")
            except Exception as e:
                errors.append(f"writer: {e}")

        threads = [threading.Thread(target=reader), threading.Thread(target=writer)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent errors: {errors}"
        assert "reader_ok" in results
        assert "writer_ok" in results


# ── Tool-Specific Edge Cases ──

class TestSpecificEdgeCases:
    def test_update_no_changes(self):
        """Update with all fields as None should keep original values."""
        result = update_expense.invoke({"expense_id": 1})
        assert "Updated" in result
        row = get_expense_by_id.func(expense_id=1)
        assert "Clothing" in row

    def test_delete_then_get(self):
        delete_expense.invoke({"expense_id": 1})
        result = get_expense_by_id.invoke({"expense_id": 1})
        assert "not found" in result

    def test_create_multiple_sequential(self):
        for i in range(1, 6):  # Start from 1 to avoid 0
            result = create_expense.invoke({
                "expense_type": "Seq",
                "amount": float(i * 10),
                "item": f"Seq-{i}",
            })
            expected_id = 3 + i
            assert f"id={expected_id}" in result, f"Expected id={expected_id}, got: {result}"

    def test_filter_case_insensitivity(self):
        result = filter_expenses.invoke({"expense_type": "clothing"})
        assert "Clothing" in result
        result = filter_expenses.invoke({"expense_type": "CLOTHING"})
        assert "Clothing" in result

    def test_filter_date_exclusive_bounds(self):
        result = filter_expenses.invoke({
            "date_from": "2026-06-07",
            "date_to": "2026-06-07"
        })
        assert "Clothing" in result
        assert "Food" not in result
        assert "Fuel" not in result

    def test_update_non_existent_id(self):
        result = update_expense.invoke({"expense_id": 9999, "item": "X"})
        assert "not found" in result

    def test_very_long_filter_item_contains(self):
        result = filter_expenses.invoke({"item_contains": "a" * 200})
        assert "No expenses matched" in result or result.startswith("|")


# ── Schema Edge Cases ──

class TestSchemaEdgeCases:
    def test_extra_unknown_field_rejected(self):
        from pydantic import ValidationError
        from app.core.tools import CreateExpenseSchema
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            CreateExpenseSchema(
                expense_type="Food", amount=10, item="X",
                unknown_field="should_fail"
            )

    def test_amount_none_rejected(self):
        from pydantic import ValidationError
        from app.core.tools import CreateExpenseSchema
        with pytest.raises(ValidationError):
            CreateExpenseSchema(expense_type="Food", amount=None, item="X")
