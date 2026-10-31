"""Public sustainability, transparency, and data governance charter."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/transparency", tags=["transparency"])


@router.get("", summary="Public benefit, sustainability, and data protection charter")
async def get_transparency_charter() -> dict[str, Any]:
    """Provides official transparency disclosures for ChhatraLekha.
    
    Includes operating principles, financial sustainability model, cost categories,
    and student data privacy guarantees.
    """
    return {
        "product_name": "ChhatraLekha",
        "tagline": "One connected place for institutions to manage academic operations and for students and families to access education services securely.",
        "business_model": {
            "is_free": True,
            "has_ads": False,
            "sells_student_data": False,
            "core_services_free": True,
            "pledge": "ChhatraLekha is a public-benefit, multi-tenant education platform provided completely free of charge to schools, colleges, students, and parents across India.",
        },
        "sustainability_sources": [
            {
                "source": "Grants & Public-Interest Funding",
                "description": "Digital inclusion, open-source education, and accessible digital infrastructure research grants.",
            },
            {
                "source": "Corporate Social Responsibility (CSR)",
                "description": "Transparent computing and server infrastructure grants with strictly zero access to student records or administrative operations.",
            },
            {
                "source": "Philanthropic & University Partnerships",
                "description": "Evaluation pilots and non-profit educational infrastructure contributions.",
            },
            {
                "source": "Open-Source Community Contributions",
                "description": "Peer security reviews, translations in 13 Indian languages, documentation, and maintainer stewardship.",
            },
        ],
        "operating_cost_categories": [
            {
                "category": "Cloud Hosting & Persistent Storage",
                "purpose": "Encrypted MongoDB persistence, multi-region API compute, and daily automated encrypted snapshots.",
            },
            {
                "category": "Communication & Notification Dispatch",
                "purpose": "In-app messaging, email notifications, and webhook delivery infrastructure.",
            },
            {
                "category": "Cryptographic Key Management & Verification",
                "purpose": "Ed25519 digital signature signing key storage and high-availability JWKS verification registries.",
            },
            {
                "category": "Security Audits & Vulnerability Assessments",
                "purpose": "Regular code audits, penetration testing, and dependency vulnerability scans.",
            },
        ],
        "data_protection_charter": {
            "principles": [
                "Privacy before growth: Minimization and strict purpose limitation on every stored record.",
                "Multi-tenant isolation: Complete logical isolation across institutional tenants enforced at API and database layers.",
                "Deny-by-default access control: Explicit role-based permissions verified on every request.",
                "Opaque credential tokens: Public verification endpoints expose only allowlisted metadata; raw identifiers and sensitive PII are never published.",
                "Student ownership & verified guardian access: Parents can only access records linked through verified institution approvals.",
            ],
            "legal_governance": "Designed in alignment with Indian digital personal data protection principles, age-appropriate notices, and verifiable audit logging.",
            "data_export_and_exit": "Institutions maintain complete ownership of their data and can export all student, attendance, and assessment records at any time.",
        },
    }
