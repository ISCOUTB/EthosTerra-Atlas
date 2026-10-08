from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger("ocr_processor")


class OCRError(Exception):
    """Error base en el procesamiento OCR local."""


class LocalOCRProcessor:
    """Procesador OCR 100% soberano y offline mediante Poppler (pdftoppm) y Tesseract OCR."""

    def __init__(self, ocr_cache_dir: Path | None = None) -> None:
        self.ocr_cache_dir = ocr_cache_dir or Path("outputs/atlas/ocr")
        self.ocr_cache_dir.mkdir(parents=True, exist_ok=True)
        self.tesseract_bin = self._find_bin(["/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract", "/usr/bin/tesseract", "tesseract"])
        self.pdftoppm_bin = self._find_bin(["/opt/homebrew/bin/pdftoppm", "/usr/local/bin/pdftoppm", "/usr/bin/pdftoppm", "pdftoppm"])

    def _find_bin(self, candidates: list[str]) -> str:
        for c in candidates:
            resolved = shutil.which(c) if not c.startswith("/") else c
            if resolved and Path(resolved).is_file() and os.access(resolved, os.X_OK):
                return resolved
        raise OCRError(f"No se encontró binario ejecutable para: {candidates}")

    def extract_text_with_ocr(self, pdf_path: Path, max_pages: int = 15) -> str:
        """Extrae texto digitalizado de las páginas escaneadas de un PDF sin servicios en nube."""
        if not pdf_path.exists():
            raise OCRError(f"Archivo PDF no existe: {pdf_path}")

        cache_file = self.ocr_cache_dir / f"{pdf_path.stem}_ocr.txt"
        if cache_file.exists():
            logger.info(f"Cargando texto OCR desde caché: {cache_file.name}")
            return cache_file.read_text(encoding="utf-8")

        logger.info(f"Iniciando OCR local soberano para {pdf_path.name} (máx {max_pages} páginas)...")
        with tempfile.TemporaryDirectory(prefix="atlas_ocr_") as tmpdir:
            tmp_path = Path(tmpdir)
            img_prefix = tmp_path / "page"

            # 1. Renderizar páginas PDF a PNG a 150 DPI (óptimo balance OCR/velocidad)
            cmd_ppm = [
                self.pdftoppm_bin,
                "-png",
                "-r", "150",
                "-f", "1",
                "-l", str(max_pages),
                str(pdf_path),
                str(img_prefix),
            ]
            res_ppm = subprocess.run(cmd_ppm, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_ppm.returncode != 0:
                raise OCRError(f"Fallo en pdftoppm al renderizar páginas: {res_ppm.stderr}")

            # 2. Ejecutar Tesseract sobre cada página renderizada con fallback de idioma
            res_langs = subprocess.run([self.tesseract_bin, "--list-langs"], stdout=subprocess.PIPE, text=True)
            avail_langs = set(res_langs.stdout.split())
            lang = "spa" if "spa" in avail_langs else "eng"

            extracted_pages: list[str] = []
            page_images = sorted(list(tmp_path.glob("page-*.png")))
            if not page_images:
                raise OCRError("pdftoppm no generó imágenes de página.")

            for img in page_images:
                cmd_tess = [self.tesseract_bin, str(img), "stdout", "-l", lang, "--psm", "3"]
                res_tess = subprocess.run(cmd_tess, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res_tess.returncode == 0 and res_tess.stdout.strip():
                    extracted_pages.append(res_tess.stdout.strip())
                else:
                    logger.warning(f"Error o texto vacío en Tesseract para {img.name}: {res_tess.stderr.strip()}")

            full_ocr_text = "\n\n--- PÁGINA ---\n\n".join(extracted_pages)
            if not full_ocr_text.strip():
                raise OCRError(f"Tesseract OCR no extrajo texto de {pdf_path.name}")

            # Persistir en caché local soberano
            cache_file.write_text(full_ocr_text, encoding="utf-8")
            logger.info(f"OCR finalizado con éxito ({len(full_ocr_text)} caracteres extraídos).")
            return full_ocr_text
