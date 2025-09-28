#!/usr/bin/env python3
"""Filtra los CSV anuales para conservar sólo la Región Metropolitana de Santiago.

Detecta automáticamente la columna de región (buscando variantes que contengan
"region" en el nombre) y escribe salidas en `02_emisiones_por_ano_rm` con el
mismo esquema de columnas.
"""
from __future__ import annotations

import argparse
import csv
import unicodedata
from pathlib import Path
from typing import Optional

import pandas as pd

REGION_ALIASES = {
    "metropolitana de santiago",
    "region metropolitana de santiago",
    "region metropolitana",
    "metropolitana",
    "rm",
    "rm de santiago",
}


def remove_diacritics(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = remove_diacritics(text)
    # reemplazar separadores comunes por espacios
    for ch in [",", ".", "-", "(", ")"]:
        text = text.replace(ch, " ")
    text = " ".join(text.split())
    return text


def detect_region_column(df: pd.DataFrame) -> Optional[str]:
    candidates = []
    for col in df.columns:
        norm_col = normalize_text(col)
        if "region" in norm_col:
            candidates.append(col)
    return candidates[0] if candidates else None


def value_is_rm(value: object) -> bool:
    norm = normalize_text(value)
    if not norm:
        return False
    if norm in REGION_ALIASES:
        return True
    # fracciones como "region metropolitana de santiago (rm)"
    if "metropolitana" in norm and "santiago" in norm:
        return True
    if norm.endswith(" rm") or norm == "rm":
        return True
    return False


def process_file(path: Path, outdir: Path) -> Optional[Path]:
    # leer pequeñas filas para detectar columna
    preview = pd.read_csv(path, sep=';', nrows=10, dtype=str, encoding='utf-8', on_bad_lines='skip')
    region_col = detect_region_column(preview)
    if not region_col:
        print(f"[!] No se detectó columna de región en {path.name}; se omite")
        return None

    df = pd.read_csv(path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip')
    if region_col not in df.columns:
        print(f"[!] La columna detectada {region_col} no existe en {path.name}; se omite")
        return None

    mask = df[region_col].map(value_is_rm)
    filtered = df[mask]
    if filtered.empty:
        print(f"[!] Sin registros de RM en {path.name}; se omite")
        return None

    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / f"{path.stem}_RM.csv"
    filtered.to_csv(
        out_path,
        index=False,
        sep=';',
        encoding='utf-8-sig',
        quoting=csv.QUOTE_NONE,
        escapechar='\\',
    )
    print(f"[✓] Filtrado RM -> {out_path.name}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Filtra las emisiones anuales para Región Metropolitana")
    parser.add_argument(
        "--indir",
        default="../data/interim/01_emisiones_por_ano",
        help="Directorio con CSV anuales normalizados",
    )
    parser.add_argument(
        "--outdir",
        default="../data/interim/02_emisiones_por_ano_rm",
        help="Directorio de salida para los CSV filtrados",
    )
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    if not indir.is_dir():
        raise SystemExit(f"No se encontró el directorio de entrada: {indir}")

    files = sorted(indir.glob("retc_*.csv"))
    if not files:
        raise SystemExit("No se encontraron CSV anuales (retc_*.csv)")

    for file in files:
        process_file(file, outdir)

    print(f"[✓] Filtrado completado. Archivos disponibles en: {outdir}")


if __name__ == "__main__":
    main()
