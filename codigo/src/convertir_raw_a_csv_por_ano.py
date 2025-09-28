#!/usr/bin/env python3
"""Convierte archivos RAW del RETC a CSV normalizados por año.

- Lee archivos CSV/XLS/XLSX en `data/raw/descargas_retc` (por defecto).
- Normaliza separadores decimales: usa `.` como decimal y elimina separadores de miles.
- Fuerza la columna `unidad` (si existe) a `t/año`.
- Exporta cada archivo como `retc_<año>.csv` en `data/interim/01_emisiones_por_ano` con separador `;`
  y campos entre comillas.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Optional

import pandas as pd

RAW_PATTERN = re.compile(r"(\d{4})")
NA_VALUES = {"", "na", "nan", "none", "null"}


def detect_year(path: Path) -> str:
    """Obtiene el último año de cuatro dígitos presente en el nombre del archivo."""
    matches = RAW_PATTERN.findall(path.stem)
    if not matches:
        raise ValueError(f"No se encontró año en el nombre del archivo: {path.name}")
    return matches[-1]


def load_raw(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, dtype=str)
    if path.suffix.lower() == ".csv":
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        seps = [None, ";", ","]
        for enc in encodings:
            for sep in seps:
                try:
                    return pd.read_csv(
                        path,
                        dtype=str,
                        engine="python",
                        encoding=enc,
                        sep=sep,
                    )
                except UnicodeDecodeError:
                    continue
                except Exception:
                    continue
        raise ValueError(f"No fue posible leer el CSV con los encodings probados: {path}")
    raise ValueError(f"Formato no soportado: {path.suffix}")


def normalize_cell(value: Optional[str]) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text.lower() in NA_VALUES:
        return None

    # Normalización de números con separadores.
    number_like = re.fullmatch(r"[+-]?[0-9.,]+", text)
    if number_like:
        if "," in text and "." in text:
            text = text.replace(".", "")
        text = text.replace(",", ".")
        # Evitar devolver cadenas vacías tras limpieza.
        text = text.strip()
        if text == "":
            return None
        return text
    return text


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.applymap(normalize_cell)
    if "unidad" in df.columns:
        df["unidad"] = "t/año"
    return df


def detect_type(series: pd.Series) -> str:
    sample = series.dropna().head(10)
    if sample.empty:
        return "texto"
    numeric = pd.to_numeric(sample, errors="coerce")
    if numeric.notna().all():
        return "numerico"
    return "texto"


def convert_file(path: Path, outdir: Path) -> Path:
    year = detect_year(path)
    df = load_raw(path)
    df = normalize_dataframe(df)
    type_row = {col: detect_type(df[col]) for col in df.columns}
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / f"retc_{year}.csv"
    df_out = pd.concat([pd.DataFrame([type_row]), df], ignore_index=True)
    df_out.to_csv(
        out_path,
        index=False,
        sep=';',
        encoding="utf-8-sig",
        quoting=csv.QUOTE_NONE,
        escapechar='\\',
    )
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convierte archivos RAW del RETC a CSV normalizados")
    parser.add_argument(
        "--indir",
        default="../data/raw/descargas_retc",
        help="Directorio con archivos originales del RETC",
    )
    parser.add_argument(
        "--outdir",
        default="../data/interim/01_emisiones_por_ano",
        help="Directorio de salida para los CSV normalizados",
    )
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    if not indir.is_dir():
        raise SystemExit(f"No se encontró el directorio de entrada: {indir}")

    raw_files = sorted([p for p in indir.iterdir() if p.suffix.lower() in {".csv", ".xls", ".xlsx"}])
    if not raw_files:
        raise SystemExit("No se encontraron archivos RAW para convertir")

    for raw_path in raw_files:
        out_path = convert_file(raw_path, outdir)
        print(f"[✓] Convertido {raw_path.name} -> {out_path.name}")

    print(f"[✓] Archivos normalizados disponibles en: {outdir}")


if __name__ == "__main__":
    main()
