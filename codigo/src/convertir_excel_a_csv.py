#!/usr/bin/env python3
"""Convierte un archivo Excel del RETC a CSV normalizado.

Características:
- Usa `.` como separador decimal, eliminando separadores de miles.
- Mantiene el separador de columnas `;`.
- Fuerza la columna `unidad` a `t/año` si existe.
- Inserta una fila inicial que indica el tipo de dato de cada columna (`numerico` o `texto`).

Uso:
  python convertir_excel_a_csv.py \
    --input ../data/raw/descargas_retc/ruea-efp-2021-ckan.xlsx \
    --output ../data/interim/01_emisiones_por_ano/retc_2021.csv
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Optional

import pandas as pd

NA_VALUES = {"", "na", "nan", "none", "null"}
NUMBER_PATTERN = re.compile(r"^[+-]?[\d.,\s]+$")


def normalize_value(value: Optional[str]) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text.lower() in NA_VALUES:
        return None

    if NUMBER_PATTERN.match(text):
        # Quitar espacios intermedios
        text = text.replace(" ", "")
        # Si existen puntos y comas, asumir puntos como separadores de miles
        if "," in text and "." in text:
            text = text.replace(".", "")
        text = text.replace(",", ".")
        text = text.strip()
        if text == "" or text == "-":
            return None
        return text

    return text


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.applymap(normalize_value)
    if "unidad" in normalized.columns:
        normalized["unidad"] = "t/año"
    return normalized


def detect_type(series: pd.Series) -> str:
    sample = series.dropna()
    if sample.empty:
        return "texto"
    numeric = pd.to_numeric(sample, errors="coerce")
    if numeric.notna().all():
        return "numerico"
    return "texto"


def main() -> None:
    parser = argparse.ArgumentParser(description="Convierte un Excel RETC a CSV estandarizado")
    parser.add_argument("--input", required=True, help="Ruta al archivo Excel de entrada")
    parser.add_argument("--output", required=True, help="Ruta de salida para el CSV")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.exists():
        raise SystemExit(f"No se encontró el archivo de entrada: {input_path}")

    df = pd.read_excel(input_path, dtype=str)
    df = normalize_dataframe(df)

    type_row = {col: detect_type(df[col]) for col in df.columns}
    df_out = pd.concat([pd.DataFrame([type_row]), df], ignore_index=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(
        output_path,
        index=False,
        sep=';',
        encoding='utf-8-sig',
        quoting=csv.QUOTE_NONE,
        escapechar='\\',
    )
    print(f"[✓] CSV generado en {output_path}")


if __name__ == "__main__":
    main()
