#!/usr/bin/env python3
"""Reconstruye tablas por contaminante fusionando columnas duplicadas.

- Combina `cantidad_toneladas` con `emision_total`.
- Combina `id_ciiu6` con `ciiu6_id`.
- Combina `rubro_id` con `id_rubro_vu`.
- Normaliza `unidad` a `t/año` (reemplaza variantes `ton/año`).
- Escribe un CSV por contaminante en el directorio de salida.

Uso:
  python reconstruir_emisiones_por_variable.py \
    --indir ../data/interim/emisiones_por_variable \
    --outdir ../data/interim/emisiones_por_variable_fusionadas
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Tuple

import pandas as pd

DEFAULT_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("cantidad_toneladas", "emision_total"),
    ("id_ciiu6", "ciiu6_id"),
    ("rubro_id", "id_rubro_vu"),
)

SKIP_FILES = {
    "diccionario_id_nombre_por_grupo.csv",
    "resumen_por_grupo.csv",
}


def read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    # homogenizar vacíos como NA para facilitar el merge
    df = df.apply(lambda col: col.replace({"": pd.NA}))
    return df


def merge_columns(df: pd.DataFrame, primary: str, secondary: str) -> pd.DataFrame:
    if primary not in df.columns and secondary not in df.columns:
        return df
    if primary not in df.columns:
        df[primary] = pd.NA
    if secondary not in df.columns:
        return df

    prim = df[primary]
    sec = df[secondary]

    # Detectar conflictos: filas con valores distintos en ambas columnas
    conflicts = prim.notna() & sec.notna() & (prim != sec)
    if conflicts.any():
        conflict_count = int(conflicts.sum())
        print(f"[!] Advertencia: {conflict_count} conflictos al fusionar '{primary}' y '{secondary}'. Se conserva '{primary}'.")

    df[primary] = prim.combine_first(sec)
    df = df.drop(columns=[secondary])
    return df


def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    if "unidad" not in df.columns:
        return df
    df["unidad"] = (
        df["unidad"]
        .fillna(pd.NA)
        .replace({"ton/año": "t/año", "Ton/año": "t/año", "Tn/año": "t/año"})
    )
    return df


def process_file(path: Path, outdir: Path, pairs: Iterable[Tuple[str, str]]) -> None:
    df = read_csv(path)
    for primary, secondary in pairs:
        df = merge_columns(df, primary, secondary)
    df = normalize_units(df)
    outdir.mkdir(parents=True, exist_ok=True)
    df.to_csv(outdir / path.name, index=False, encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fusiona columnas duplicadas en tablas por contaminante")
    parser.add_argument(
        "--indir",
        default="../data/interim/emisiones_por_variable",
        help="Directorio de entrada con CSV por contaminante",
    )
    parser.add_argument(
        "--outdir",
        default="../data/interim/emisiones_por_variable_fusionadas",
        help="Directorio de salida para los CSV fusionados",
    )
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    if not indir.is_dir():
        raise SystemExit(f"No se encontró el directorio de entrada: {indir}")

    files = [p for p in sorted(indir.glob("*.csv")) if p.name not in SKIP_FILES]
    if not files:
        raise SystemExit("No se encontraron archivos CSV de contaminantes en el directorio indicado.")

    for path in files:
        process_file(path, outdir, DEFAULT_PAIRS)
        print(f"[✓] Procesado {path.name}")

    print(f"[✓] CSV fusionados disponibles en: {outdir}")


if __name__ == "__main__":
    main()
