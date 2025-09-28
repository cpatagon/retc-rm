#!/usr/bin/env python3
"""Añade columna canonizada de actividad económica a tablas RM fusionadas."""
from __future__ import annotations

import argparse
import csv
import unicodedata
from pathlib import Path
from typing import Dict, Set, Tuple

import pandas as pd

METADATA_PATH = Path('metadata/ciiu_codigo_descripcion.csv')

NA_VALUES = {"", "na", "nan", "none", "null"}


def load_ciiu_mapping(metadata_path: Path) -> Dict[str, str]:
    df = pd.read_csv(metadata_path, dtype=str, encoding='utf-8')
    mapping = {}
    for _, row in df.iterrows():
        code = str(row['codigo']).strip()
        if code in NA_VALUES:
            continue
        desc = str(row['descripcion']).strip() if pd.notna(row['descripcion']) else ""
        mapping[code] = desc
    return mapping


def prefer_value(row: pd.Series, columns) -> str | None:
    for col in columns:
        if col in row and pd.notna(row[col]) and row[col].strip() not in NA_VALUES:
            return row[col].strip()
    return None


LETTER_MACRO = {
    'A': 'AGRO_FORESTRY',
    'B': 'MINING',
    'C': 'MANUFACTURING',
    'D': 'ENERGY',
    'E': 'WASTE_WATER',
    'F': 'CONSTRUCTION',
    'G': 'TRADE',
    'H': 'TRANSPORT',
    'I': 'SERVICES',
    'J': 'SERVICES',
    'K': 'SERVICES',
    'L': 'SERVICES',
    'M': 'SERVICES',
    'N': 'SERVICES',
    'O': 'PUBLIC_SOCIAL',
    'P': 'PUBLIC_SOCIAL',
    'Q': 'PUBLIC_SOCIAL',
    'R': 'SERVICES',
    'S': 'SERVICES',
    'T': 'OTHER',
    'U': 'OTHER',
}

KEYWORD_MACRO = [
    ('electric', 'ENERGY'),
    ('energia', 'ENERGY'),
    ('energ', 'ENERGY'),
    ('generacion electrica', 'ENERGY'),
    ('generación eléctrica', 'ENERGY'),
    ('gas', 'ENERGY'),
    ('petrol', 'ENERGY'),
    ('min', 'MINING'),
    ('mina', 'MINING'),
    ('cantera', 'MINING'),
    ('extract', 'MINING'),
    ('const', 'CONSTRUCTION'),
    ('obras', 'CONSTRUCTION'),
    ('transp', 'TRANSPORT'),
    ('logist', 'TRANSPORT'),
    ('almacen', 'TRANSPORT'),
    ('comerc', 'TRADE'),
    ('hotel', 'TRADE'),
    ('restaur', 'TRADE'),
    ('agric', 'AGRO_FORESTRY'),
    ('ganad', 'AGRO_FORESTRY'),
    ('forest', 'AGRO_FORESTRY'),
    ('pesca', 'AGRO_FORESTRY'),
    ('acuic', 'AGRO_FORESTRY'),
    ('residu', 'WASTE_WATER'),
    ('desech', 'WASTE_WATER'),
    ('alcantar', 'WASTE_WATER'),
    ('aguas', 'WASTE_WATER'),
    ('sanitari', 'WASTE_WATER'),
    ('salud', 'PUBLIC_SOCIAL'),
    ('hospital', 'PUBLIC_SOCIAL'),
    ('educ', 'PUBLIC_SOCIAL'),
    ('universidad', 'PUBLIC_SOCIAL'),
    ('public', 'PUBLIC_SOCIAL'),
]


def normalize_text(text: str) -> str:
    s = unicodedata.normalize('NFKD', text.lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('.', ' ').replace(',', ' ')
    s = ' '.join(s.split())
    return s


def classify_macro(code: str | None, desc: str | None) -> str:
    if code:
        for ch in code:
            if ch.isalpha():
                macro = LETTER_MACRO.get(ch.upper())
                if macro:
                    return macro
                break
    if desc:
        norm = normalize_text(desc)
        for kw, macro in KEYWORD_MACRO:
            if kw in norm:
                return macro
    return 'OTHER'


def add_activity_column(df: pd.DataFrame, code_map: Dict[str, str], missing_codes: Set[str]) -> Tuple[pd.DataFrame, Set[str]]:
    # Clean BOM
    df.columns = [c.lstrip('\ufeff') for c in df.columns]

    if 'actividad_canon' in df.columns:
        df = df.drop(columns=['actividad_canon'])
    if 'actividad_macro' in df.columns:
        df = df.drop(columns=['actividad_macro'])

    # Determine best code available
    candidate_cols = ['ciiu6_id', 'id_ciiu6', 'ciiu4_id', 'id_ciiu4', 'rubro_id', 'id_rubro_vu']
    activity_codes = []
    macro_labels = []
    macros_used: Set[str] = set()
    for _, row in df.iterrows():
        code = prefer_value(row, candidate_cols)
        if code and code in code_map:
            desc = code_map[code]
            activity_codes.append(code)
            macro_labels.append(classify_macro(code, desc))
        else:
            activity_codes.append(None)
            macro = classify_macro(code, None)
            macro_labels.append(macro)
            if code:
                missing_codes.add(code)
        macros_used.add(macro_labels[-1])

    # Insert after contaminante_canon if present else after año
    if 'contaminante_canon' in df.columns:
        insert_idx = df.columns.get_loc('contaminante_canon') + 1
    elif 'año' in df.columns:
        insert_idx = df.columns.get_loc('año') + 1
    else:
        insert_idx = 1

    df.insert(insert_idx, 'actividad_canon', activity_codes)
    df.insert(insert_idx + 1, 'actividad_macro', macro_labels)
    return df, macros_used


def main() -> None:
    parser = argparse.ArgumentParser(description="Estandariza códigos CIIU en tablas RM")
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
    parser.add_argument(
        "--metadata",
        default=str(METADATA_PATH),
        help="Ruta del CSV con códigos CIIU normalizados",
    )
    args = parser.parse_args()

    metadata_path = Path(args.metadata).expanduser().resolve()
    if not metadata_path.exists():
        raise SystemExit(f"No se encuentra el metadata de CIIU: {metadata_path}")

    code_map = load_ciiu_mapping(metadata_path)

    indir = Path(args.indir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    missing: Set[str] = set()
    macros_total: Set[str] = set()

    for csv_path in sorted(indir.glob('retc*_RM.csv')):
        df = pd.read_csv(csv_path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip')
        df, macros_used = add_activity_column(df, code_map, missing)
        macros_total.update(macros_used)
        out_path = outdir / csv_path.name
        df.to_csv(out_path, index=False, sep=';', encoding='utf-8-sig', quoting=csv.QUOTE_NONE, escapechar='\\')
        print(f"[✓] Actualizado {csv_path.name}")

    if missing:
        print("[!] Códigos sin mapeo registrado en metadata/ciiu_codigo_descripcion.csv:")
        for code in sorted(missing):
            print(" -", code)
    else:
        print("[✓] Todos los códigos CIIU/rubro encontraron correspondencia")

    print("[i] Categorías macro detectadas:", ', '.join(sorted(macros_total)))


if __name__ == '__main__':
    main()
