import pytest
from pydantic import ValidationError
from app.schema.agent_schema import AgentRequest, AgentResponse
from app.core.tools import (
    CreateExpenseSchema,
    UpdateExpenseSchema,
    FilterExpensesSchema,
    GetExpenseByIdSchema,
    DeleteExpenseSchema,
)


class TestAgentRequest:
    def test_valid_message(self):
        req = AgentRequest(message="Hello")
        assert req.message == "Hello"

    def test_empty_message_rejected(self):
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            AgentRequest(message="")

    def test_whitespace_only_is_valid(self):
        req = AgentRequest(message="   ")
        assert req.message == "   "

    def test_long_message(self):
        msg = "a" * 10000
        req = AgentRequest(message=msg)
        assert req.message == msg


class TestAgentResponse:
    def test_valid_response(self):
        resp = AgentResponse(response="Some output")
        assert resp.response == "Some output"

    def test_empty_response_is_valid(self):
        resp = AgentResponse(response="")
        assert resp.response == ""


class TestCreateExpenseSchema:
    def test_valid(self):
        schema = CreateExpenseSchema(expense_type="Food", amount=10.50, item="Lunch")
        assert schema.expense_type == "Food"
        assert schema.amount == 10.50
        assert schema.item == "Lunch"
        assert schema.date is None

    def test_valid_with_date(self):
        schema = CreateExpenseSchema(
            expense_type="Travel", amount=200, item="Cab", date="2026-06-08"
        )
        assert schema.date == "2026-06-08"

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            CreateExpenseSchema(expense_type="Food", amount=-1, item="X")

    def test_zero_amount_rejected(self):
        with pytest.raises(ValidationError):
            CreateExpenseSchema(expense_type="Food", amount=0, item="X")

    def test_empty_expense_type_rejected(self):
        with pytest.raises(ValidationError):
            CreateExpenseSchema(expense_type="", amount=10, item="X")

    def test_empty_item_rejected(self):
        with pytest.raises(ValidationError):
            CreateExpenseSchema(expense_type="Food", amount=10, item="")

    def test_invalid_date_format_rejected(self):
        with pytest.raises(ValidationError):
            CreateExpenseSchema(
                expense_type="Food", amount=10, item="X", date="01-15-2026"
            )

    def test_invalid_date_random_string_rejected(self):
        with pytest.raises(ValidationError):
            CreateExpenseSchema(
                expense_type="Food", amount=10, item="X", date="not-a-date"
            )

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            CreateExpenseSchema(
                expense_type="Food",
                amount=10,
                item="X",
                unknown_field="should_fail",
            )

    def test_expense_type_too_long_rejected(self):
        with pytest.raises(ValidationError):
            CreateExpenseSchema(expense_type="A" * 51, amount=10, item="X")

    def test_item_too_long_rejected(self):
        with pytest.raises(ValidationError):
            CreateExpenseSchema(expense_type="Food", amount=10, item="A" * 201)


class TestUpdateExpenseSchema:
    def test_valid_with_all_fields(self):
        schema = UpdateExpenseSchema(
            expense_id=1, date="2026-06-08", expense_type="Food",
            amount=99.99, item="Pizza"
        )
        assert schema.expense_id == 1
        assert schema.date == "2026-06-08"

    def test_valid_with_only_id(self):
        schema = UpdateExpenseSchema(expense_id=5)
        assert schema.expense_id == 5
        assert schema.date is None

    def test_negative_id_rejected(self):
        with pytest.raises(ValidationError):
            UpdateExpenseSchema(expense_id=-1, item="X")

    def test_zero_id_rejected(self):
        with pytest.raises(ValidationError):
            UpdateExpenseSchema(expense_id=0, item="X")

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            UpdateExpenseSchema(expense_id=1, amount=-50)


class TestGetExpenseByIdSchema:
    def test_valid(self):
        schema = GetExpenseByIdSchema(expense_id=1)
        assert schema.expense_id == 1

    def test_negative_id_rejected(self):
        with pytest.raises(ValidationError):
            GetExpenseByIdSchema(expense_id=-5)

    def test_zero_id_rejected(self):
        with pytest.raises(ValidationError):
            GetExpenseByIdSchema(expense_id=0)


class TestDeleteExpenseSchema:
    def test_valid(self):
        schema = DeleteExpenseSchema(expense_id=3)
        assert schema.expense_id == 3

    def test_negative_id_rejected(self):
        with pytest.raises(ValidationError):
            DeleteExpenseSchema(expense_id=-1)


class TestFilterExpensesSchema:
    def test_valid_all_optional(self):
        schema = FilterExpensesSchema()
        assert schema.date_from is None

    def test_valid_date_range(self):
        schema = FilterExpensesSchema(
            date_from="2026-01-01", date_to="2026-12-31"
        )
        assert schema.date_from == "2026-01-01"

    def test_invalid_date_from_rejected(self):
        with pytest.raises(ValidationError):
            FilterExpensesSchema(date_from="bad-date")

    def test_invalid_date_to_rejected(self):
        with pytest.raises(ValidationError):
            FilterExpensesSchema(date_to="bad-date")

    def test_negative_min_amount_rejected(self):
        with pytest.raises(ValidationError):
            FilterExpensesSchema(min_amount=-1)

    def test_zero_min_amount_valid(self):
        schema = FilterExpensesSchema(min_amount=0)
        assert schema.min_amount == 0
