"""Tests for guest profile contact field validation."""

import pytest

from models.guest_profile import (
    GuestProfile,
    infer_contact_preference,
    normalize_email,
    normalize_whatsapp,
)


class TestContactNormalization:
    def test_valid_email(self):
        assert normalize_email("Guest@Example.com") == "guest@example.com"

    def test_invalid_email_rejected(self):
        assert normalize_email("not-an-email") is None
        assert normalize_email("@missing.com") is None

    def test_skip_email(self):
        assert normalize_email("skip") is None
        assert normalize_email("no thanks") is None

    def test_whatsapp_with_country_code(self):
        assert normalize_whatsapp("+94 77 123 4567") == "+94771234567"
        assert normalize_whatsapp("94-77-123-4567") == "+94771234567"

    def test_whatsapp_too_short(self):
        assert normalize_whatsapp("12345") is None

    def test_whatsapp_skip(self):
        assert normalize_whatsapp("prefer not") is None


class TestProfileCompletion:
    def test_complete_without_contact(self):
        profile = GuestProfile(
            travel_style="nature",
            group_type="couple",
            budget_tier="mid_range",
            dietary_restrictions="vegetarian",
            duration_nights=3,
        )
        assert profile.is_complete()

    def test_contact_fields_optional(self):
        profile = GuestProfile(
            travel_style="nature",
            group_type="couple",
            budget_tier="mid_range",
            dietary_restrictions="none",
            duration_nights=2,
            email="guest@leafycave.com",
            whatsapp_number="+94771234567",
            contact_preference="both",
        )
        assert profile.is_complete()

    def test_infer_contact_preference(self):
        assert infer_contact_preference("a@b.co", "+94771234567", None) == "both"
        assert infer_contact_preference("a@b.co", None, None) == "email"
        assert infer_contact_preference(None, "+94771234567", None) == "whatsapp"
