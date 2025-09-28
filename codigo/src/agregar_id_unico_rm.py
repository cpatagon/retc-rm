#!/usr/bin/env python3
"""Genera un `id_unico` secuencial por fila en cada tabla RM fusionada."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ID_FORMAT = "{year}{seq:09d}"  # año + 9 dígitos (cero relleno) => 13 caracteres


def year_from_path(path: Path) -> str:
    stem = path.stem
    if stem.endswith('_RM'):
        stem = stem[:-3]
    parts = stem.split('_')
    for part in parts:
        if len(part) == 4 and part.isdigit():
            return part
    raise ValueError(f"No se pudo inferir año desde el nombre {path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Añade id_unico a tablas RM")
    parser.add_argument(
        "--indir",
        default="../data/interim/03_emisiones_rm_fusionadas",
        help="Carpeta con los CSV a actualizar",
    )
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    if not indir.is_dir():
        raise SystemExit(f"No se encontró el directorio: {indir}")

    for csv_path in sorted(indir.glob('retc*_RM.csv')):
        year = year_from_path(csv_path)
        df = pd.read_csv(csv_path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip')
        df.columns = [c.lstrip('\ufeff') for c in df.columns]

        if 'id_unico' in df.columns:
            df.drop(columns=['id_unico'], inplace=True)

        sequences = range(1, len(df) + 1)
        ids = [ID_FORMAT.format(year=year, seq=seq) for seq in sequences]
        df.insert(0, 'id_unico', ids)

        df.to_csv(csv_path, index=False, sep=';', encoding='utf-8-sig', quoting=0, escapechar='\\')
        print(f"[✓] id_unico añadido en {csv_path.name}")

    print("[✓] Todas las tablas cuentan con identificadores únicos")


if __name__ == '__main__':
    main()
