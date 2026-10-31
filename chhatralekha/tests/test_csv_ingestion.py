"""Tests for the batch CSV ingestion."""

from __future__ import annotations

from dataclasses import dataclass

from app.services import csv_ingestion


@dataclass
class FakeProgramme:
    program_id: str = "BTECH_CSE"
    program_name: str = "B.Tech Computer Science"
    approved_intake: int = 60
    max_supernumerary_nri: int = 3
    max_supernumerary_fn_oci: int = 9
    max_supernumerary_tfw: int = 3
    max_pmsss: int = 6


HEADER = "APAAR_ID,Full_Name,DOB,Gender,Roll_No,Program_Code,Category,Nationality,Doc_Number"


def context(**overrides) -> csv_ingestion.CsvValidationContext:
    values = {
        "programs": [FakeProgramme()],
        "existing_apaar_ids": set(),
        "existing_regular_counts": {},
        "existing_supernumerary_counts": {},
        "existing_nri_counts": {},
        "existing_oci_fn_counts": {},
        "existing_tfw_counts": {},
        "existing_pmsss_counts": {},
    }
    values.update(overrides)
    return csv_ingestion.CsvValidationContext(**values)


def test_the_parser_handles_quoted_fields():
    header, rows = csv_ingestion.parse_csv('a,b\n"x,1","he said ""hi"""')
    assert header == ["a", "b"]
    assert rows == [["x,1", 'he said "hi"']]


def test_the_parser_strips_a_bom():
    header, _ = csv_ingestion.parse_csv("\ufeffAPAAR_ID,Full_Name")
    assert header[0] == "APAAR_ID"


def test_a_valid_row_produces_no_issues():
    text = f"{HEADER}\n984210357890,Aakash Verma,2004-03-12,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,Indian,"
    report = csv_ingestion.validate_csv(text, context())
    assert report.header_errors == []
    assert report.total_rows == 1
    assert report.critical_rows == 0
    assert report.valid_rows == 1


def test_a_missing_mandatory_column_is_reported():
    report = csv_ingestion.validate_csv("APAAR_ID,Full_Name\n1,2", context())
    assert report.header_errors
    assert any("PROGRAM_CODE" in error for error in report.header_errors)


def test_an_invalid_apaar_id_blocks_the_row():
    text = f"{HEADER}\n12345,Aakash Verma,2004-03-12,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,Indian,"
    report = csv_ingestion.validate_csv(text, context())
    assert report.critical_rows == 1
    assert any(issue.code == "INVALID_APAAR" for issue in report.rows[0].issues)


def test_a_luhn_mismatch_is_only_a_warning():
    text = f"{HEADER}\n984210357891,Aakash Verma,2004-03-12,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,Indian,"
    report = csv_ingestion.validate_csv(text, context())
    assert report.critical_rows == 0
    assert report.warning_rows == 1


def test_an_apaar_id_already_in_the_registry_blocks_the_row():
    text = f"{HEADER}\n984210357890,Aakash Verma,2004-03-12,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,Indian,"
    report = csv_ingestion.validate_csv(
        text, context(existing_apaar_ids={"984210357890"})
    )
    assert report.critical_rows == 1
    assert any(issue.code == "DUPLICATE" for issue in report.rows[0].issues)


def test_a_duplicate_inside_the_batch_blocks_every_copy():
    text = (
        f"{HEADER}\n"
        "984210357890,Aakash Verma,2004-03-12,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,Indian,\n"
        "984210357890,Aakash Verma,2004-03-12,Male,CSE-2,BTECH_CSE,REGULAR_MERIT,Indian,"
    )
    report = csv_ingestion.validate_csv(text, context())
    assert report.duplicate_rows == 2
    assert report.critical_rows == 2


def test_a_missing_name_blocks_the_row():
    text = f"{HEADER}\n984210357890,,2004-03-12,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,Indian,"
    report = csv_ingestion.validate_csv(text, context())
    assert any(issue.code == "MISSING_NAME" for issue in report.rows[0].issues)


def test_an_invalid_date_blocks_the_row():
    text = f"{HEADER}\n984210357890,Aakash,not-a-date,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,Indian,"
    report = csv_ingestion.validate_csv(text, context())
    assert any(issue.code == "INVALID_DOB" for issue in report.rows[0].issues)


def test_an_unknown_quota_blocks_the_row():
    text = f"{HEADER}\n984210357890,Aakash,2004-03-12,Male,CSE-1,BTECH_CSE,WIZARD,Indian,"
    report = csv_ingestion.validate_csv(text, context())
    assert any(issue.code == "INVALID_CATEGORY" for issue in report.rows[0].issues)


def test_an_unknown_programme_blocks_the_row():
    text = f"{HEADER}\n984210357890,Aakash,2004-03-12,Male,CSE-1,BTECH_NAVAL,WIZARD,Indian,"
    report = csv_ingestion.validate_csv(text, context())
    assert any(issue.code == "UNKNOWN_PROGRAM" for issue in report.rows[0].issues)
    assert report.unknown_programs == ["BTECH_NAVAL"]


def test_a_regular_seat_for_a_non_indian_is_a_warning():
    text = f"{HEADER}\n984210357890,Aakash,2004-03-12,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,German,"
    report = csv_ingestion.validate_csv(text, context())
    assert report.warning_rows == 1
    assert any(issue.code == "CATEGORY_MISMATCH" for issue in report.rows[0].issues)


def test_a_foreign_national_without_a_passport_is_a_warning():
    text = f"{HEADER}\n984210357890,Aakash,2004-03-12,Male,CSE-1,BTECH_CSE,SUPERNUMERARY_FN,Chinese,"
    report = csv_ingestion.validate_csv(text, context())
    assert any(issue.code == "MISSING_PASSPORT" for issue in report.rows[0].issues)


def test_the_seat_impact_is_computed():
    text = (
        f"{HEADER}\n"
        "984210357890,A,2004-03-12,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,Indian,\n"
        "984210357891,B,2004-03-12,Male,CSE-2,BTECH_CSE,REGULAR_MERIT,Indian,"
    )
    report = csv_ingestion.validate_csv(text, context())
    impact = report.program_impacts[0]
    assert impact.incoming_regular == 2
    assert impact.existing_regular == 0
    assert impact.projected_regular == 2


def test_an_intake_breach_is_reported_in_the_impact():
    text = (
        f"{HEADER}\n"
        "984210357890,A,2004-03-12,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,Indian,\n"
        "984210357891,B,2004-03-12,Male,CSE-2,BTECH_CSE,REGULAR_MERIT,Indian,"
    )
    report = csv_ingestion.validate_csv(
        text, context(existing_regular_counts={"BTECH_CSE": 59})
    )
    impact = report.program_impacts[0]
    assert impact.projected_regular == 61
    assert impact.regular_overflow == 1
    assert any("Regular intake breach" in message for message in impact.cap_messages)


def test_the_nri_ceiling_is_reported_in_the_impact():
    text = f"{HEADER}\n984210357890,A,2004-03-12,Male,CSE-1,BTECH_CSE,SUPERNUMERARY_NRI,Indian,"
    report = csv_ingestion.validate_csv(
        text, context(existing_nri_counts={"BTECH_CSE": 3})
    )
    impact = report.program_impacts[0]
    assert any("NRI" in message for message in impact.cap_messages)


def test_committable_rows_exclude_the_blocked_ones():
    text = (
        f"{HEADER}\n"
        "984210357890,A,2004-03-12,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,Indian,\n"
        "12345,B,2004-03-12,Male,CSE-2,BTECH_CSE,REGULAR_MERIT,Indian,"
    )
    report = csv_ingestion.validate_csv(text, context())
    assert len(report.committable_rows) == 1


def test_dates_are_normalised():
    assert csv_ingestion.normalise_date("2004-03-12") == "2004-03-12"
    assert csv_ingestion.normalise_date("12-03-2004") == "2004-03-12"
    assert csv_ingestion.normalise_date("12/03/2004") == "2004-03-12"
    assert csv_ingestion.normalise_date("nonsense") is None
    assert csv_ingestion.normalise_date("2004-02-31") is None


def test_the_template_parses_cleanly():
    report = csv_ingestion.validate_csv(csv_ingestion.TEMPLATE, context())
    assert report.header_errors == []
    assert report.total_rows == 4
