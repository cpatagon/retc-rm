#!/usr/bin/env python3
"""Añade columna canonizada de contaminantes a tablas RM fusionadas."""
from __future__ import annotations

import argparse
import csv
import unicodedata
from pathlib import Path
from typing import Dict, Set

import pandas as pd

RAW_CANON: Dict[str, str] = {
    "Ammonia": "NH3",
    "Nitrógeno amoniacal (o NH3)": "NH3",
    "Nitrógeno amoniacal": "NH3",
    "Arsenic": "ARSENIC",
    "Arsénico": "ARSENIC",
    "Arsenico": "ARSENIC",
    "Benceno": "BENZENE",
    "Benzene": "BENZENE",
    "Toluene": "TOLUENE",
    "Tolueno / metil benceno / Toluol / Fenilmetano": "TOLUENE",
    "Black Carbon": "BLACK_CARBON",
    "Carbon dioxide": "CO2",
    "Dióxido de carbono (CO2)": "CO2",
    "Carbon monoxide": "CO",
    "Monóxido de carbono": "CO",
    "Compuestos Orgánicos Volátiles": "VOC",
    "Volatile organic compounds (VOC)": "VOC",
    "Dibenzoparadioxinas policloradas y furanos (PCDD/F)": "PCDD_F",
    "PCDD-F": "PCDD_F",
    "Dióxido de azufre (SO2)": "SO2",
    "Dióxido de azúfre (SO2)": "SO2",
    "Sulfur dioxide": "SO2",
    "Sulfur oxides (SOx)": "SOX",
    "Lead": "PB",
    "Plomo": "PB",
    "MP10": "PM10",
    "PM10": "PM10",
    "PM10, primary": "PM10",
    "MP2,5": "PM2_5",
    "PM2.5": "PM2_5",
    "PM2.5, primary": "PM2_5",
    "PM, primary": "PM_PRIMARY",
    "Material particulado": "PM_TOTAL",
    "Mercury": "HG",
    "Mercurio": "HG",
    "Methane": "CH4",
    "NOx": "NOX",
    "Nitrogen oxides (NOx)": "NOX",
    "Nitrous oxide": "N2O",
}


def normalize(text: str | None) -> str:
    if text is None:
        return ""
    s = str(text).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    replacements = {
        ",": "",
        "(": "",
        ")": "",
        ":": "",
        "[": "",
        "]": "",
        "'": "",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    s = " ".join(s.split())
    return s


CANON_MAP: Dict[str, str] = {normalize(name): label for name, label in RAW_CANON.items()}


def apply_canon(df: pd.DataFrame, missing: Set[str]) -> pd.DataFrame:
    columns = {c.lstrip('\ufeff') for c in df.columns}
    df.columns = [c.lstrip('\ufeff') for c in df.columns]

    if "contaminante_canon" in df.columns:
        df = df.drop(columns=["contaminante_canon"])

    contaminant_col = "contaminantes" if "contaminantes" in df.columns else "contaminante"
    if contaminant_col not in df.columns:
        raise KeyError("No se encontró columna de contaminantes")

    canon_values = []
    for value in df[contaminant_col]:
        norm = normalize(value)
        canon = CANON_MAP.get(norm)
        if canon is None and value is not None:
            missing.add(value)
        canon_values.append(canon)

    if "año" in df.columns:
        insert_idx = df.columns.get_loc("año") + 1
    elif "ano" in df.columns:
        insert_idx = df.columns.get_loc("ano") + 1
    elif '\ufeffaño' in columns:
        insert_idx = 1
    else:
        insert_idx = 1

    df.insert(insert_idx, "contaminante_canon", canon_values)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Estandariza los nombres de contaminantes en tablas RM")
    parser.add_argument(
        "--indir",
        default="../data/interim/03_emisiones_rm_fusionadas",
        help="Carpeta con CSV fusionados",
    )
    parser.add_argument(
        "--outdir",
        default="../data/interim/03_emisiones_rm_fusionadas",
        help="Carpeta de salida (puede ser la misma)",
    )
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    missing: Set[str] = set()

    for csv_path in sorted(indir.glob('retc*_RM.csv')):
        df = pd.read_csv(csv_path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip')
        df = apply_canon(df, missing)
        out_path = outdir / csv_path.name
        df.to_csv(out_path, index=False, sep=';', encoding='utf-8-sig', quoting=csv.QUOTE_NONE, escapechar='\\')
        print(f"[✓] Actualizado {csv_path.name}")

    if missing:
        print("[!] Valores de contaminante sin mapeo:")
        for val in sorted(missing):
            print(" -", val)
    else:
        print("[✓] Todos los contaminantes fueron mapeados")


if __name__ == "__main__":
    main()
