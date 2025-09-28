#!/usr/bin/env python3
"""Crea/normaliza la columna `emision_total` en tablas RM fusionadas."""
from __future__ import annotations

import argparse
import csv
import unicodedata
from pathlib import Path
from typing import Dict

import pandas as pd

NA_VALUES = {"", "na", "nan", "none", "null"}
SOURCE_OVERRIDE: Dict[str, str] = {
    "retc_2023_RM.csv": "emision_total",
}
DEFAULT_COLUMN = "cantidad_toneladas"


def normalize_number(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in NA_VALUES or text == "":
        return None
    norm = unicodedata.normalize("NFKC", text)
    norm = norm.replace(" ", "")
    if "," in norm and "." in norm:
        norm = norm.replace(".", "")
    norm = norm.replace(",", ".")
    norm = norm.replace("·", "")
    norm = norm.strip()
    return norm or None


def process_file(path: Path) -> None:
    df = pd.read_csv(path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip')
    df.columns = [c.lstrip('\ufeff') for c in df.columns]

    source_col = SOURCE_OVERRIDE.get(path.name, DEFAULT_COLUMN)
    if source_col not in df.columns:
        raise KeyError(f"{path.name}: no se encuentra columna '{source_col}'")

    emision_values = [normalize_number(val) for val in df[source_col]]

    # Consolida desde columnas de respaldo si la principal está vacía o "-"
    if 'emision_total' in df.columns:
        fallback_cols = ['emision_total', 'emision_primario', 'emision_combustible_primario']
    else:
        fallback_cols = ['emision_primario', 'emision_total', 'emision_combustible_primario']

    for idx, primary in enumerate(emision_values):
        if primary not in (None, '-'):
            continue
        backup = None
        row = df.iloc[idx]
        for col in fallback_cols:
            if col not in df.columns:
                continue
            candidate = normalize_number(row[col])
            if candidate not in (None, '-'):
                backup = candidate
                break
        emision_values[idx] = backup

    if 'emision_total' in df.columns:
        df.drop(columns=['emision_total'], inplace=True)

    # Insertimos después de actividad_macro si existe, sino al final
    if 'actividad_macro' in df.columns:
        insert_idx = df.columns.get_loc('actividad_macro') + 1
    else:
        insert_idx = len(df.columns)

    df.insert(insert_idx, 'emision_total', emision_values)

    df.to_csv(path, index=False, sep=';', encoding='utf-8-sig', quoting=csv.QUOTE_NONE, escapechar='\\')
    print(f"[✓] emision_total normalizada en {path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Añade columna emision_total homogénea")
    parser.add_argument(
        "--indir",
        default="../data/interim/03_emisiones_rm_fusionadas",
        help="Carpeta con los CSV RM fusionados",
    )
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    if not indir.is_dir():
        raise SystemExit(f"No se encontró el directorio: {indir}")

    for csv_path in sorted(indir.glob('retc*_RM.csv')):
        process_file(csv_path)

    print("[✓] Columna emision_total creada/actualizada en todas las tablas")


if __name__ == '__main__':
    main()
