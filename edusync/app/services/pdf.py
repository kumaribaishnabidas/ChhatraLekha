"""PDF rendering for the regulatory reports and the APAAR certificates.

`ReportLab` is used directly (rather than a headless browser) so that the
server can produce a certificate PDF without any external process.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.documents import enum_value, field

# EduSynC brand palette.
NAVY = colors.HexColor("#14246B")
MID_BLUE = colors.HexColor("#0F3A8A")
BRAND_TEAL = colors.HexColor("#12B886")
SAFFRON = colors.HexColor("#F2A413")
CRIMSON = colors.HexColor("#C62828")
GREY = colors.HexColor("#5A6472")
LIGHT = colors.HexColor("#EEF2F8")


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "EdusyncTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=NAVY,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "EdusyncSubtitle",
            parent=base["Normal"],
            fontSize=10,
            textColor=GREY,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "heading": ParagraphStyle(
            "EdusyncHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=MID_BLUE,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "EdusyncBody",
            parent=base["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1A1F2B"),
        ),
        "small": ParagraphStyle(
            "EdusyncSmall",
            parent=base["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=GREY,
        ),
        "centre": ParagraphStyle(
            "EdusyncCentre",
            parent=base["Normal"],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1A1F2B"),
        ),
    }


def _footer(canvas, doc) -> None:
    """Brand footer drawn on every page."""
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, A4[0], 12 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(18 * mm, 4.6 * mm, "EduSynC")
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(
        A4[0] - 18 * mm, 4.6 * mm, f"Page {doc.page}  |  APAAR National Registry"
    )
    canvas.restoreState()


def _header_block(styles, title: str, subtitle: str) -> list:
    return [
        Paragraph(title, styles["title"]),
        Paragraph(subtitle, styles["subtitle"]),
    ]


def build_students_report_pdf(
    rows: Sequence,
    *,
    title: str = "APAAR Student Register",
    subtitle: str = "",
    generated_by: str = "EduSynC",
) -> bytes:
    """Render the student register as a paginated PDF table."""
    styles = _styles()
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
        title=title,
        author=generated_by,
    )

    story = _header_block(
        styles,
        title,
        subtitle
        or f"Generated {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')} by {generated_by}",
    )

    header = [
        "APAAR ID",
        "Student",
        "Institution",
        "Programme",
        "Quota",
        "Status",
    ]
    data = [header]
    for row in rows:
        data.append(
            [
                field(row, "apaar_id", ""),
                field(row, "student_name", ""),
                field(row, "institution_id", ""),
                field(row, "program_id", ""),
                enum_value(field(row, "admission_quota", "")),
                enum_value(field(row, "verification_status", "")),
            ]
        )

    table = Table(data, repeatRows=1, colWidths=[26 * mm, 42 * mm, 26 * mm, 30 * mm, 26 * mm, 30 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C7D0DE")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 6 * mm))
    story.append(
        Paragraph(
            f"{len(rows)} record(s). This report is generated from the live EduSynC "
            "registry and carries the APAAR ID of every student listed.",
            styles["small"],
        )
    )
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def build_anomaly_report_pdf(
    rows: Sequence,
    *,
    title: str = "APAAR Regulatory Anomaly Report",
    subtitle: str = "",
) -> bytes:
    """Render the anomaly register as a PDF table."""
    styles = _styles()
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm,
        title=title,
    )

    story = _header_block(
        styles,
        title,
        subtitle
        or f"Generated {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}",
    )

    data = [["APAAR ID", "Institution", "Programme", "Type", "Severity", "Details"]]
    for row in rows:
        data.append(
            [
                field(row, "student_apaar_id", ""),
                field(row, "institution_id", ""),
                field(row, "program_id", "") or "-",
                enum_value(field(row, "anomaly_type", "")),
                enum_value(field(row, "severity", "")),
                field(row, "details", ""),
            ]
        )

    severity_colours = {
        "CRITICAL": CRIMSON,
        "HIGH": SAFFRON,
        "WARNING": MID_BLUE,
        "INFO": GREY,
    }
    table = Table(
        data,
        repeatRows=1,
        colWidths=[26 * mm, 26 * mm, 28 * mm, 42 * mm, 20 * mm, 118 * mm],
    )
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C7D0DE")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for index, row in enumerate(rows, start=1):
        colour = severity_colours.get(enum_value(field(row, "severity", "")), GREY)
        style.append(("TEXTCOLOR", (4, index), (4, index), colour))
        style.append(("FONTNAME", (4, index), (4, index), "Helvetica-Bold"))
    table.setStyle(TableStyle(style))
    story.append(table)
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def build_compliance_report_pdf(
    rows: Sequence,
    *,
    title: str = "APAAR Intake Compliance Matrix",
) -> bytes:
    """Render the institution compliance matrix as a PDF table."""
    styles = _styles()
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm,
        title=title,
    )

    story = _header_block(
        styles,
        title,
        f"Generated {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}",
    )

    data = [
        [
            "Institution",
            "State",
            "Approved",
            "Enrolled",
            "Utilisation %",
            "Breaches",
            "Risk band",
        ]
    ]
    for row in rows:
        data.append(
            [
                field(row, "institution_name", "") or field(row, "institution_id", ""),
                field(row, "state", ""),
                field(row, "total_approved", 0),
                field(row, "total_enrolled", 0),
                f"{float(field(row, 'utilisation', 0.0) or 0.0) * 100:.1f}",
                field(row, "breaches", 0),
                field(row, "risk_band", "LOW"),
            ]
        )

    table = Table(
        data,
        repeatRows=1,
        colWidths=[62 * mm, 28 * mm, 24 * mm, 22 * mm, 26 * mm, 22 * mm, 26 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C7D0DE")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def build_certificate_pdf(
    *,
    student,
    institution_name: str,
    program_name: str,
    academic_year: str,
    apaar_id: str,
    qr_png: bytes,
    seal_text: str,
    certificate_type: str = "Bonafide Certificate",
    issued_at: int | None = None,
) -> bytes:
    """Render an APAAR certificate carrying the APAAR ID and the QR badge."""
    styles = _styles()
    buffer = io.BytesIO()
    width, height = A4
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=certificate_type,
    )

    moment = datetime.now(timezone.utc)
    issued = (
        datetime.fromtimestamp(issued_at / 1000, tz=timezone.utc)
        if issued_at
        else moment
    )

    story: list = []
    story.append(Paragraph("EduSynC", styles["title"]))
    story.append(
        Paragraph(
            "Automated Permanent Academic Account Registry (APAAR) &middot; AICTE",
            styles["subtitle"],
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(certificate_type, styles["heading"]))
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            f"This is to certify that <b>{field(student, 'student_name', '')}</b>, bearing APAAR ID "
            f"<b>{apaar_id}</b>, is duly enrolled in the programme "
            f"<b>{program_name}</b> at <b>{institution_name}</b> for the academic year "
            f"<b>{academic_year}</b>.",
            styles["body"],
        )
    )
    story.append(Spacer(1, 5 * mm))

    details = [
        ["APAAR ID", apaar_id],
        ["Student name", field(student, "student_name", "")],
        ["Date of birth", field(student, "date_of_birth", "") or "-"],
        ["Institution", institution_name],
        ["Programme", program_name],
        ["Academic year", academic_year],
        ["Institute roll no.", field(student, "student_institute_roll_no", "") or "-"],
        ["Quota category", enum_value(field(student, "admission_quota", ""))],
        ["Enrolment date", field(student, "enrollment_date", "") or "-"],
        ["Verification status", enum_value(field(student, "verification_status", ""))],
    ]
    table = Table(details, colWidths=[48 * mm, 92 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor("#D6DEEA")),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 6 * mm))

    qr_image = Image(io.BytesIO(qr_png), width=30 * mm, height=30 * mm)
    qr_block = [
        [qr_image, Paragraph("Scan to verify this credential at the EduSynC verification portal.", styles["body"])],
    ]
    qr_table = Table(qr_block, colWidths=[34 * mm, 106 * mm])
    qr_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#C7D0DE")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(qr_table)
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            f"Digital seal: {seal_text}",
            styles["small"],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            f"Issued {issued.strftime('%d %B %Y, %H:%M UTC')} by the EduSynC national "
            "registry. This certificate is verifiable offline using the digital seal "
            "and the APAAR QR badge printed above.",
            styles["small"],
        )
    )
    document.build(story)
    return buffer.getvalue()
