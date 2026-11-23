#!/usr/bin/env python3
"""
ChhatraLekha — Mandatory Project Documents Gate Verifier

Validates the existence, completeness, and non-empty integrity of the
four mandatory project documents and their references in the repository root:
1. PRODUCT_REQUIREMENTS.md
2. DESIGN_SYSTEM.md
3. ARCHITECTURE.md
4. AI_AGENTS.md
"""

from __future__ import annotations

import sys
from pathlib import Path

# Resolve repository root
REPO_ROOT = Path(__file__).resolve().parents[1]

MANDATORY_DOCS = {
    "PRODUCT_REQUIREMENTS.md": [
        "Product Identity",
        "Target Users",
        "Functional Requirements",
        "Non-Functional Requirements",
        "Roadmap",
    ],
    "DESIGN_SYSTEM.md": [
        "Brand Identity",
        "Color Palette",
        "Typography",
        "Design Tokens",
        "Component Standards",
    ],
    "ARCHITECTURE.md": [
        "System Overview",
        "Technology Stack",
        "Backend Architecture",
        "Frontend Architecture",
        "Security Architecture",
    ],
    "AI_AGENTS.md": [
        "Scope & Applicability",
        "Pre-Flight Operating Rules",
        "Repository Safety",
        "Task Workflow",
        "Audit Reporting",
    ],
}


def verify_docs() -> int:
    errors: list[str] = []
    print("=" * 70)
    print(" ChhatraLekha — Mandatory Project Documents Gate Verification")
    print("=" * 70)
    print(f"Repository Root: {REPO_ROOT}\n")

    for filename, required_sections in MANDATORY_DOCS.items():
        doc_path = REPO_ROOT / filename
        if not doc_path.exists():
            errors.append(f"[MISSING] {filename} does not exist in repository root.")
            continue

        size = doc_path.stat().st_size
        if size < 1000:
            errors.append(
                f"[TRUNCATED] {filename} is suspiciously small ({size} bytes)."
            )
            continue

        content = doc_path.read_text(encoding="utf-8")
        missing_sections = [
            sec for sec in required_sections if sec.lower() not in content.lower()
        ]

        if missing_sections:
            errors.append(
                f"[INCOMPLETE] {filename} missing required sections: {', '.join(missing_sections)}"
            )
        else:
            print(f"  [OK] {filename} ({size:,} bytes) - All required sections present.")

    # Check README references
    readme_path = REPO_ROOT / "README.md"
    if readme_path.exists():
        readme_content = readme_path.read_text(encoding="utf-8")
        for filename in MANDATORY_DOCS.keys():
            if filename not in readme_content:
                errors.append(f"[UNLINKED] README.md does not reference {filename}.")
        print("  [OK] README.md links to all four mandatory documents.")
    else:
        errors.append("[MISSING] README.md does not exist.")

    print("\n" + "-" * 70)
    if errors:
        print(" Gate Verification FAILED:")
        for err in errors:
            print(f"   * {err}")
        print("-" * 70)
        return 1

    print(" Gate Verification PASSED: All 4 mandatory documents are valid.")
    print("-" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(verify_docs())
