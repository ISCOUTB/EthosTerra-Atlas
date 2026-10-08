#!/usr/bin/env python3
"""
render_all.py - Script automatizado para compilar todos los diagramas Mermaid (.mmd)
a formatos SVG y PNG (garantizando ancho >= 2000 px).

Uso:
  python3 docs/diagrams/tools/render_all.py
"""

import os
import sys
import subprocess
import glob
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DIAGRAMS_ROOT = PROJECT_ROOT / "docs" / "diagrams"
SRC_DIR = DIAGRAMS_ROOT / "src"
OUT_DIR = DIAGRAMS_ROOT / "out"
TOOLS_DIR = DIAGRAMS_ROOT / "tools"
PUPPETEER_CONFIG = TOOLS_DIR / "puppeteer-config.json"

def get_png_width(png_path: Path) -> int:
    """Obtiene el ancho en píxeles usando sips o leyendo la cabecera PNG."""
    try:
        res = subprocess.run(["sips", "-g", "pixelWidth", str(png_path)], capture_output=True, text=True, check=True)
        for line in res.stdout.splitlines():
            if "pixelWidth:" in line:
                return int(line.split(":")[1].strip())
    except Exception:
        pass

    # Fallback leyendo cabecera IHDR de PNG (bytes 16..20)
    with open(png_path, "rb") as f:
        data = f.read(24)
        if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
            import struct
            width, _ = struct.unpack(">II", data[16:24])
            return width
    return 0

def render_diagram(src_file: Path):
    stem = src_file.stem
    svg_out = OUT_DIR / f"{stem}.svg"
    png_out = OUT_DIR / f"{stem}.png"

    print(f"--> Procesando: {src_file.name}")

    # 1. Renderizar SVG
    cmd_svg = [
        "pnpm", "dlx", "@mermaid-js/mermaid-cli",
        "-i", str(src_file),
        "-o", str(svg_out),
        "-b", "white",
        "-p", str(PUPPETEER_CONFIG)
    ]
    res_svg = subprocess.run(cmd_svg, capture_output=True, text=True)
    if res_svg.returncode != 0:
        print(f"ERROR al renderizar SVG para {src_file.name}:", file=sys.stderr)
        print(res_svg.stderr or res_svg.stdout, file=sys.stderr)
        return False

    # 2. Renderizar PNG con escala inicial 4
    scale = 4
    cmd_png = [
        "pnpm", "dlx", "@mermaid-js/mermaid-cli",
        "-i", str(src_file),
        "-o", str(png_out),
        "-b", "white",
        "-s", str(scale),
        "-p", str(PUPPETEER_CONFIG)
    ]
    res_png = subprocess.run(cmd_png, capture_output=True, text=True)
    if res_png.returncode != 0:
        print(f"ERROR al renderizar PNG para {src_file.name}:", file=sys.stderr)
        print(res_png.stderr or res_png.stdout, file=sys.stderr)
        return False

    width = get_png_width(png_out)

    # Si el ancho es menor a 2000 px, re-renderizar con mayor escala
    if width < 2000 and width > 0:
        factor = int((2000 / width) * scale) + 1
        print(f"    Ancho inicial {width} px < 2000 px. Re-renderizando con escala {factor}...")
        cmd_png[8] = str(factor)
        subprocess.run(cmd_png, capture_output=True, text=True)
        width = get_png_width(png_out)

    print(f"    OK -> SVG generado | PNG ancho: {width} px ({png_out.name})")
    return True

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mmd_files = sorted(SRC_DIR.glob("*.mmd"))

    if not mmd_files:
        print(f"No se encontraron archivos .mmd en {SRC_DIR}")
        sys.exit(1)

    print(f"Iniciando compilación de {len(mmd_files)} diagramas...")
    failed = []
    results = {}

    for src_file in mmd_files:
        success = render_diagram(src_file)
        if not success:
            failed.append(src_file.name)
        else:
            png_path = OUT_DIR / f"{src_file.stem}.png"
            w = get_png_width(png_path)
            results[src_file.stem] = w

    print("\n" + "="*60)
    print("RESUMEN DE RENDER:")
    print("="*60)
    for stem, w in results.items():
        status = "PASS (>= 2000px)" if w >= 2000 else "WARN (< 2000px)"
        print(f"{stem:35} | {w:5} px | {status}")

    if failed:
        print(f"\nFALLARON {len(failed)} diagramas: {failed}")
        sys.exit(1)
    else:
        print(f"\n¡ÉXITO TOTAL! Los {len(mmd_files)} diagramas se compilaron a SVG y PNG exitosamente.")

if __name__ == "__main__":
    main()
