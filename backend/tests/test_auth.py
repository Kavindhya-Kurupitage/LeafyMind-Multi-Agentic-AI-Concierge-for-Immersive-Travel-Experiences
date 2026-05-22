"""Authentication endpoint tests."""

import re

import pytest
from pydantic import ValidationError

from api.auth import RegisterRequest


def test_register_password_requires_uppercase_and_number() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(email="guest@example.com", password="lowercase1", full_name="Guest")

    with pytest.raises(ValidationError):
        RegisterRequest(email="guest@example.com", password="NoDigits", full_name="Guest")

    req = RegisterRequest(email="guest@example.com", password="ValidPass1", full_name="Guest")
    assert req.password == "ValidPass1"


def test_register_password_min_length() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(email="guest@example.com", password="Ab1", full_name="Guest")


def test_password_pattern_helpers() -> None:
    assert re.search(r"[A-Z]", "Valid1")
    assert re.search(r"\d", "Valid1")
