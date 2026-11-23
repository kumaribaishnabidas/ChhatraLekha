#!/usr/bin/env python3
"""
ChhatraLekha — Project Governance Documents Gate Verifier (Alias)

Redirects to or executes the mandatory project documents verification.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import verify_docs from verify_mandatory_docs
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from verify_mandatory_docs import verify_docs

if __name__ == "__main__":
    sys.exit(verify_docs())
