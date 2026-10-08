from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO

DEFAULT_CHUNK_SIZE = 65536  # 64 KB por bloque para streaming eficiente


def compute_stream_sha256(stream: BinaryIO, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
    """Calcula el hash criptográfico SHA-256 de un flujo binario en streaming."""
    hasher = hashlib.sha256()
    while chunk := stream.read(chunk_size):
        hasher.update(chunk)
    return hasher.hexdigest()


def compute_file_sha256(file_path: Path | str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
    """Calcula el hash SHA-256 de un archivo en disco por bloques sin saturar memoria."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Archivo no encontrado para hashing: {path}")

    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Calcula el hash SHA-256 directo sobre bytes en memoria."""
    return hashlib.sha256(data).hexdigest()
