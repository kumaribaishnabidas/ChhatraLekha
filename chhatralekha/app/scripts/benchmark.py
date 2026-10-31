"""Reproducible performance benchmark script for ChhatraLekha.

Measures latency and throughput on synthetic datasets for:
1. Batch CSV Ingestion & Validation (50, 100, 250 rows)
2. Credential Cryptographic Seals (HMAC-SHA256, Ed25519 signing and verification)
3. Opaque Verification Token Hashing & Verification
4. Audit Log Hash Chain Verification (500 chained entries)

Usage::
    python -m app.scripts.benchmark
    python -m app.scripts.benchmark --json
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import datetime, timezone
from typing import Any, Callable

from app.models.documents import Doc
from app.repositories.tokens import hash_token
from app.services import audit_chain, seal
from app.services.csv_ingestion import CsvValidationContext, validate_csv


def percentile(data: list[float], p: float) -> float:
    """Compute the p-th percentile (0.0 - 100.0) of a list of floats."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    d = k - f
    return sorted_data[f] + d * (sorted_data[c] - sorted_data[f])


def measure(fn: Callable[[], Any], iterations: int = 20) -> tuple[list[float], int]:
    """Execute fn repeatedly and measure duration in milliseconds per iteration."""
    latencies: list[float] = []
    errors = 0
    # Warm-up run
    try:
        fn()
    except Exception:
        errors += 1

    for _ in range(iterations):
        t0 = time.perf_counter()
        try:
            fn()
        except Exception:
            errors += 1
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)

    return latencies, errors


def generate_synthetic_csv(row_count: int) -> str:
    """Generate a clean synthetic CSV with row_count student records."""
    headers = "APAAR_ID,Full_Name,DOB,Gender,Roll_No,Program_Code,Category,Nationality,Doc_Number\n"
    lines = [headers]
    for i in range(1, row_count + 1):
        # 12-digit APAAR
        apaar = f"9842{i:08d}"
        line = f"{apaar},Student {i},2004-05-15,Male,CSE-24-{i:03d},BTECH_CSE,REGULAR_MERIT,Indian,\n"
        lines.append(line)
    return "".join(lines)


def benchmark_csv_ingestion() -> dict[str, Any]:
    context = CsvValidationContext.empty()
    sizes = [50, 100, 250]
    results = {}

    for size in sizes:
        csv_text = generate_synthetic_csv(size)
        latencies, errors = measure(
            lambda csv_text=csv_text: validate_csv(csv_text, context), iterations=25
        )
        med = percentile(latencies, 50.0)
        p95 = percentile(latencies, 95.0)
        tput = (size / (med / 1000.0)) if med > 0 else 0.0

        results[f"{size}_rows"] = {
            "dataset_rows": size,
            "iterations": len(latencies),
            "errors": errors,
            "median_ms": round(med, 3),
            "p95_ms": round(p95, 3),
            "min_ms": round(min(latencies), 3),
            "max_ms": round(max(latencies), 3),
            "throughput_rows_per_sec": round(tput, 1),
        }

    return results


def benchmark_crypto_seals() -> dict[str, Any]:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    payload = seal.CredentialPayload(
        apaar_id="984210357890",
        institution_id="INST-001",
        program_id="BTECH_CSE",
        academic_year="2024-25",
        enrollment_date="2024-08-01",
        student_name="Aakash Verma",
        date_of_birth="2004-03-12",
        gender="M",
        admission_quota="REGULAR_MERIT",
        nationality="Indian",
        student_institute_roll_no="CSE-001",
    )

    from app.core.config import get_settings
    settings = get_settings()
    secret = settings.seal_hmac_key.encode("utf-8")
    private_key = Ed25519PrivateKey.generate()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    # 1. Sign HMAC
    hmac_sign_lats, hmac_sign_err = measure(
        lambda: seal.sign_hmac(payload, secret), iterations=100
    )
    hmac_seal = seal.sign_hmac(payload, secret)

    # 2. Verify HMAC
    hmac_ver_lats, hmac_ver_err = measure(
        lambda: seal.verify_hmac(hmac_seal, payload, secret), iterations=100
    )

    # 3. Sign Ed25519
    ed_sign_lats, ed_sign_err = measure(
        lambda: seal.sign_ed25519(payload, private_key), iterations=100
    )
    ed_seal = seal.sign_ed25519(payload, private_key)

    # 4. Verify Ed25519
    ed_ver_lats, ed_ver_err = measure(
        lambda: seal.verify_ed25519(ed_seal, payload, public_pem), iterations=100
    )

    return {
        "hmac_sha256": {
            "sign": {
                "operations": len(hmac_sign_lats),
                "errors": hmac_sign_err,
                "median_ms": round(percentile(hmac_sign_lats, 50.0), 4),
                "p95_ms": round(percentile(hmac_sign_lats, 95.0), 4),
            },
            "verify": {
                "operations": len(hmac_ver_lats),
                "errors": hmac_ver_err,
                "median_ms": round(percentile(hmac_ver_lats, 50.0), 4),
                "p95_ms": round(percentile(hmac_ver_lats, 95.0), 4),
            },
        },
        "ed25519_digital_signature": {
            "sign": {
                "operations": len(ed_sign_lats),
                "errors": ed_sign_err,
                "median_ms": round(percentile(ed_sign_lats, 50.0), 4),
                "p95_ms": round(percentile(ed_sign_lats, 95.0), 4),
            },
            "verify": {
                "operations": len(ed_ver_lats),
                "errors": ed_ver_err,
                "median_ms": round(percentile(ed_ver_lats, 50.0), 4),
                "p95_ms": round(percentile(ed_ver_lats, 95.0), 4),
            },
        },
    }


def benchmark_token_verification() -> dict[str, Any]:
    raw_token = "chhatralekha_tok_" + "a" * 32
    lats, errs = measure(lambda: hash_token(raw_token), iterations=200)

    return {
        "token_hash_lookup": {
            "operations": len(lats),
            "errors": errs,
            "median_ms": round(percentile(lats, 50.0), 4),
            "p95_ms": round(percentile(lats, 95.0), 4),
            "ops_per_second": round(1000.0 / percentile(lats, 50.0), 1) if percentile(lats, 50.0) > 0 else 0,
        }
    }


def benchmark_audit_chain() -> dict[str, Any]:
    # Construct 500 audit entries
    now = datetime.now(timezone.utc)
    entries: list[Doc] = []
    prev_hash = audit_chain.GENESIS_HASH

    for i in range(500):
        entry = {
            "prev_hash": prev_hash,
            "timestamp": now,
            "actor": f"actor_{i%5}",
            "action": "CREDENTIAL_VERIFICATION",
            "subject": f"9842103578{i:02d}",
            "details": f"Verification outcome {i}",
            "category": "VERIFIED",
        }
        digest = audit_chain.hash_of(entry)
        entry["hash"] = digest
        entries.append(entry)
        prev_hash = digest

    # Verify chain
    def verify_chain():
        current_prev = audit_chain.GENESIS_HASH
        for e in entries:
            expected = audit_chain.compute_hash(
                prev_hash=current_prev,
                timestamp=e["timestamp"],
                actor=e["actor"],
                action=e["action"],
                subject=e["subject"],
                details=e["details"],
                category=e["category"],
            )
            if e["hash"] != expected:
                raise ValueError("Chain broken")
            current_prev = e["hash"]

    lats, errs = measure(verify_chain, iterations=30)

    return {
        "audit_chain_500_entries": {
            "entries_in_chain": len(entries),
            "iterations": len(lats),
            "errors": errs,
            "median_ms": round(percentile(lats, 50.0), 3),
            "p95_ms": round(percentile(lats, 95.0), 3),
            "throughput_entries_per_sec": round(500 / (percentile(lats, 50.0) / 1000.0), 1) if percentile(lats, 50.0) > 0 else 0,
        }
    }


def run_benchmark() -> dict[str, Any]:
    return {
        "runtime_environment": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_architecture": platform.machine(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
        "csv_ingestion_benchmark": benchmark_csv_ingestion(),
        "cryptographic_seals_benchmark": benchmark_crypto_seals(),
        "token_verification_benchmark": benchmark_token_verification(),
        "audit_chain_benchmark": benchmark_audit_chain(),
        "reproduction_command": "python -m app.scripts.benchmark",
    }


def print_benchmark_report(data: dict[str, Any]) -> None:
    env = data["runtime_environment"]
    print("=" * 80)
    print("CHHATRALEKHA PERFORMANCE & LATENCY BENCHMARK REPORT")
    print("=" * 80)
    print(f"Platform   : {env['platform']} ({env['cpu_architecture']})")
    print(f"Python     : {env['python_version']}")
    print(f"Timestamp  : {env['timestamp_utc']}")
    print(f"Command    : {data['reproduction_command']}")
    print("-" * 80)

    print("1. BATCH CSV INGESTION & VALIDATION:")
    print(f"{'Dataset Size':<16} {'Iterations':<12} {'Errors':<8} {'Median (ms)':<14} {'p95 (ms)':<12} {'Throughput':<16}")
    print("-" * 80)
    for key, val in data["csv_ingestion_benchmark"].items():
        print(
            f"{key:<16} "
            f"{val['iterations']:<12} "
            f"{val['errors']:<8} "
            f"{val['median_ms']:<14.3f} "
            f"{val['p95_ms']:<12.3f} "
            f"{val['throughput_rows_per_sec']:>8.1f} rows/s"
        )
    print("-" * 80)

    print("2. CRYPTOGRAPHIC CREDENTIAL SEALS:")
    seals = data["cryptographic_seals_benchmark"]
    hmac = seals["hmac_sha256"]
    ed = seals["ed25519_digital_signature"]
    print(f"  HMAC-SHA256 Sign   : Median {hmac['sign']['median_ms']:.4f} ms | p95 {hmac['sign']['p95_ms']:.4f} ms (Errors: {hmac['sign']['errors']})")
    print(f"  HMAC-SHA256 Verify : Median {hmac['verify']['median_ms']:.4f} ms | p95 {hmac['verify']['p95_ms']:.4f} ms (Errors: {hmac['verify']['errors']})")
    print(f"  Ed25519 Sign       : Median {ed['sign']['median_ms']:.4f} ms | p95 {ed['sign']['p95_ms']:.4f} ms (Errors: {ed['sign']['errors']})")
    print(f"  Ed25519 Verify     : Median {ed['verify']['median_ms']:.4f} ms | p95 {ed['verify']['p95_ms']:.4f} ms (Errors: {ed['verify']['errors']})")
    print("-" * 80)

    print("3. VERIFICATION TOKEN LOOKUP & AUDIT CHAIN:")
    tok = data["token_verification_benchmark"]["token_hash_lookup"]
    aud = data["audit_chain_benchmark"]["audit_chain_500_entries"]
    print(f"  Token Hash Check   : Median {tok['median_ms']:.4f} ms | p95 {tok['p95_ms']:.4f} ms ({tok['ops_per_second']:.0f} ops/sec)")
    print(f"  Audit Chain (500)  : Median {aud['median_ms']:.3f} ms | p95 {aud['p95_ms']:.3f} ms ({aud['throughput_entries_per_sec']:.0f} entries/sec)")
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ChhatraLekha Performance Benchmark")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    results = run_benchmark()
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_benchmark_report(results)


if __name__ == "__main__":
    main()
