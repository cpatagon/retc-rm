#!/usr/bin/env python3
"""Extrae columnas clave desde los CSV fusionados por contaminante y corrige formato.

Para cada archivo en `emisiones_por_variable_fusionadas` genera un nuevo CSV
con las columnas:
  año, razon_social, rut_razon_social, nombre_establecimiento,
  comuna, id_comuna, latitud, longitud, contaminantes, cantidad_toneladas

Además, normaliza `cantidad_toneladas` reemplazando coma por punto en la parte
decimal.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd

COLUMNS_TO_KEEP: List[str] = [
    "año",
    "ano",  # fallback
    "razon_social",
    "rut_razon_social",
    "nombre_establecimiento",
    "comuna",
    "id_comuna",
    "latitud",
    "longitud",
    "contaminantes",
    "cantidad_toneladas",
]

SKIP_FILES = {
    "diccionario_id_nombre_por_grupo.csv",
    "resumen_por_grupo.csv",
}


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "año" not in df.columns and "ano" in df.columns:
        df["año"] = df["ano"]

    if "cantidad_toneladas" in df.columns:
        df["cantidad_toneladas"] = df["cantidad_toneladas"].apply(normalize_number)
    return df


def normalize_number(value) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text == "" or text.lower() in {"na", "nan", "none"}:
        return None
    # si contiene coma y punto, asumir punto como separador de miles
    if "," in text and "." in text:
        text = text.replace(".", "")
    text = text.replace(",", ".")
    return text


def extract_columns(df: pd.DataFrame) -> pd.DataFrame:
    available = [c for c in COLUMNS_TO_KEEP if c in df.columns]
    if "año" not in available:
        raise ValueError("No existe columna 'año' o 'ano' en el DataFrame")
    if "cantidad_toneladas" not in available:
        raise ValueError("No existe columna 'cantidad_toneladas' en el DataFrame")
    desired = [c for c in [
        "año",
        "razon_social",
        "rut_razon_social",
        "nombre_establecimiento",
        "comuna",
        "id_comuna",
        "latitud",
        "longitud",
        "contaminantes",
        "cantidad_toneladas",
    ] if c in available]
    return df[desired]


def process_file(path: Path, outdir: Path) -> None:
    df = load_csv(path)
    df = normalize_columns(df)
    subset = extract_columns(df)
    out_path = outdir / path.name
    outdir.mkdir(parents=True, exist_ok=True)
    subset.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[✓] Extracto generado: {out_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrae columnas clave de emisiones por contaminante")
    parser.add_argument(
        "--indir",
        default="../data/interim/emisiones_por_variable_fusionadas",
        help="Carpeta de entrada con CSV fusionados",
    )
    parser.add_argument(
        "--outdir",
        default="../data/interim/emisiones_por_variable_extractos",
        help="Carpeta de salida para los CSV con columnas clave",
    )
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    if not indir.is_dir():
        raise SystemExit(f"No se encontró el directorio de entrada: {indir}")

    files = [p for p in sorted(indir.glob("*.csv")) if p.name not in SKIP_FILES]
    if not files:
        raise SystemExit("No se encontraron CSV para procesar")

    for path in files:
        process_file(path, outdir)

    print(f"[✓] Extractos disponibles en: {outdir}")


if __name__ == "__main__":
    main()
