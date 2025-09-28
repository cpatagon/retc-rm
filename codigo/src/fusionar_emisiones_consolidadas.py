#!/usr/bin/env python3
"""Genera tabla única consolidada desde las tablas RM fusionadas."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd

INPUT_DIR_DEFAULT = "../data/interim/03_emisiones_rm_fusionadas"
OUTPUT_DIR_DEFAULT = "../data/interim/04_emisiones_consolidadas"
OUTPUT_FILE = "retc_RM_consolidado.csv"

TARGET_COLUMNS = [
    "id_unico",
    "año",
    "contaminante_canon",
    "actividad_canon",
    "actividad_macro",
    "emision_total",
    "rut",
    "comuna",
    "latitud",
    "longitud",
    "unidad",
]

RUT_CANDIDATES = [
    "rut_razon_social",
    "rut",
    "rut_establecimiento",
]


def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip')
    df.columns = [c.lstrip('\ufeff') for c in df.columns]
    return df


def ensure_rut_column(df: pd.DataFrame) -> pd.DataFrame:
    if 'rut' in df.columns:
        return df
    for candidate in RUT_CANDIDATES:
        if candidate in df.columns:
            df['rut'] = df[candidate]
            return df
    df['rut'] = None
    return df


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_rut_column(df)
    for col in TARGET_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[TARGET_COLUMNS]


def main() -> None:
    parser = argparse.ArgumentParser(description="Consolida tablas RM en un único CSV")
    parser.add_argument("--indir", default=INPUT_DIR_DEFAULT, help="Carpeta con tablas fusionadas")
    parser.add_argument("--outdir", default=OUTPUT_DIR_DEFAULT, help="Carpeta de salida")
    parser.add_argument("--outfile", default=OUTPUT_FILE, help="Nombre del archivo de salida")
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    frames: List[pd.DataFrame] = []
    for csv_path in sorted(indir.glob('retc*_RM.csv')):
        df = load_csv(csv_path)
        df = ensure_columns(df)
        frames.append(df)
        print(f"[✓] Incorporado {csv_path.name} ({len(df)} filas)")

    if not frames:
        raise SystemExit("No se encontraron tablas para consolidar")

    result = pd.concat(frames, ignore_index=True)
    out_path = outdir / args.outfile
    result.to_csv(out_path, index=False, sep=';', encoding='utf-8-sig')
    print(f"[✓] Consolidado generado en: {out_path} ({len(result)} filas)")


if __name__ == '__main__':
    main()
