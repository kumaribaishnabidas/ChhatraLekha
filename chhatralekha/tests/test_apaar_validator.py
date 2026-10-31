"""Tests for the APAAR identifier validator."""

from __future__ import annotations

from app.services import apaar_validator


def test_a_valid_identifier_passes():
    result = apaar_validator.validate("984210357890")
    assert result.is_structurally_valid
    assert result.normalised == "984210357890"
    assert not result.errors


def test_an_empty_identifier_is_rejected():
    result = apaar_validator.validate("")
    assert not result.is_structurally_valid
    assert "mandatory" in result.errors[0].lower()


def test_a_short_identifier_is_rejected():
    result = apaar_validator.validate("9842103578")
    assert not result.is_structurally_valid
    assert any("exactly 12 digits" in error for error in result.errors)


def test_a_long_identifier_is_rejected():
    result = apaar_validator.validate("9842103578901")
    assert not result.is_structurally_valid


def test_non_digit_characters_are_rejected():
    result = apaar_validator.validate("98421035789A")
    assert not result.is_structurally_valid
    assert any("digits only" in error for error in result.errors)


def test_a_repeated_digit_is_rejected():
    result = apaar_validator.validate("111111111111")
    assert not result.is_structurally_valid


def test_an_ascending_run_is_rejected():
    result = apaar_validator.validate("012345678901")
    assert not result.is_structurally_valid
    assert any("placeholder" in error or "run" in error for error in result.errors)


def test_a_descending_run_is_rejected():
    result = apaar_validator.validate("987654321098")
    assert not result.is_structurally_valid


def test_a_padded_zero_prefix_is_rejected():
    result = apaar_validator.validate("000012345678")
    assert not result.is_structurally_valid


def test_the_luhn_advisory_is_non_blocking():
    # Structurally fine, but the checksum does not match.
    result = apaar_validator.validate("984210357891")
    assert result.is_structurally_valid
    assert not result.is_checksum_valid
    assert result.advisories


def test_the_mask_hides_all_but_the_first_group():
    assert apaar_validator.mask("984210357890") == "9842 **** ****"


def test_formatting_groups_the_identifier():
    assert apaar_validator.format_id("984210357890") == "9842 1035 7890"
    assert apaar_validator.format_with_separator("984210357890") == "9842-1035-7890"


def test_luhn_accepts_a_known_valid_number():
    assert apaar_validator.luhn_valid("4532015112830366")


def test_luhn_rejects_a_known_invalid_number():
    assert not apaar_validator.luhn_valid("4532015112830367")


def test_luhn_rejects_non_digits():
    assert not apaar_validator.luhn_valid("453201511283036x")
    assert not apaar_validator.luhn_valid("")


def test_the_check_digit_completes_a_prefix():
    prefix = "453201511283036"
    assert apaar_validator.luhn_valid(prefix + str(apaar_validator.luhn_check_digit(prefix)))
