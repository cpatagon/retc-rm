#!/usr/bin/env python3
"""Fusiona los CSV de emisiones RM según grupos de años compatibles."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd

GROUPS = {
    "2005_2015": list(range(2005, 2016)),
    "2016_2018": list(range(2016, 2019)),
}


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip')


def fuse_years(years, indir: Path) -> pd.DataFrame:
    frames = []
    for year in years:
        path = indir / f"retc_{year}_RM.csv"
        if not path.exists():
            raise FileNotFoundError(f"No existe {path}")
        frames.append(load_csv(path))
    return pd.concat(frames, ignore_index=True)


def copy_year(year: int, indir: Path, outdir: Path) -> None:
    src = indir / f"retc_{year}_RM.csv"
    dst = outdir / f"retc_{year}_RM.csv"
    dst.parent.mkdir(parents=True, exist_ok=True)
    df = load_csv(src)
    df.to_csv(dst, index=False, sep=';', encoding='utf-8-sig', quoting=csv.QUOTE_NONE, escapechar='\\')
    print(f"[=] Copiado {src.name} -> {dst.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fusiona emisiones RM por grupos de años")
    parser.add_argument(
        "--indir",
        default="../data/interim/02_emisiones_por_ano_rm",
        help="Directorio con CSV RM por año",
    )
    parser.add_argument(
        "--outdir",
        default="../data/interim/03_emisiones_rm_fusionadas",
        help="Directorio de salida para las tablas fusionadas",
    )
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    fused_years = set()
    for label, years in GROUPS.items():
        df = fuse_years(years, indir)
        out_path = outdir / f"retc_{label}_RM.csv"
        df.to_csv(out_path, index=False, sep=';', encoding='utf-8-sig', quoting=csv.QUOTE_NONE, escapechar='\\')
        print(f"[✓] Fusionado {label} -> {out_path.name} ({len(df)} filas)")
        fused_years.update(years)

    # Copiar el resto de años sin fusionar
    for csv_path in sorted(indir.glob('retc_*_RM.csv')):
        year = int(csv_path.stem.split('_')[1])
        if year in fused_years:
            continue
        copy_year(year, indir, outdir)

    print(f"[✓] Tablas disponibles en: {outdir}")


if __name__ == "__main__":
    main()
