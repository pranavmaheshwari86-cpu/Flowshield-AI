"""
ml/src/utils/hashing.py
Cryptographic SHA-256 artifact verification and integrity checks.
"""

import hashlib
from pathlib import Path
from typing import Union


def compute_sha256(filepath: Union[str, Path]) -> str:
    """Computes hexadecimal SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_file_sha256(filepath: Union[str, Path], expected_hash: str) -> bool:
    """Verifies whether a file matches its expected SHA-256 hash."""
    actual_hash = compute_sha256(filepath)
    return actual_hash.lower() == expected_hash.lower()
