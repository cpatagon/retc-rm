#!/usr/bin/env python3
"""Completa latitud/longitud en el consolidado usando centros comunales."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

NA_VALUES = {"", "na", "nan", "none", "null"}


def normalize(text: str | None) -> str:
    if text is None:
        return ""
    s = text.strip().lower()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ñ": "n", "ü": "u",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    s = s.replace('-', ' ')
    s = ' '.join(s.split())
    return s


def load_centers(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding='utf-8')
    df['key'] = df['comuna'].map(normalize)
    df.rename(columns={'latitud': 'latitud_centro', 'longitud': 'longitud_centro'}, inplace=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Completa coordenadas faltantes usando centros comunales")
    parser.add_argument('--centros', default='../data/raw/comunas/comunas_rm_centros.csv')
    parser.add_argument('--consolidado', default='../data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv')
    args = parser.parse_args()

    centros_path = Path(args.centros).expanduser().resolve()
    consolidado_path = Path(args.consolidado).expanduser().resolve()

    if not centros_path.exists():
        raise SystemExit(f'No se encuentra {centros_path}')
    if not consolidado_path.exists():
        raise SystemExit(f'No se encuentra {consolidado_path}')

    centros = load_centers(centros_path)
    df = pd.read_csv(consolidado_path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip')
    df['key_comuna'] = df['comuna'].map(normalize)

    df = df.merge(centros[['key', 'latitud_centro', 'longitud_centro']], how='left', left_on='key_comuna', right_on='key')
    df.drop(columns=['key'], inplace=True)

    def choose(original, centro):
        if pd.isna(original) or original.strip() in NA_VALUES:
            return centro
        return original

    df['latitud_nueva'] = [choose(o, c) for o, c in zip(df.get('latitud', []), df['latitud_centro'])]
    df['longitud_nueva'] = [choose(o, c) for o, c in zip(df.get('longitud', []), df['longitud_centro'])]

    df.drop(columns=['latitud_centro', 'longitud_centro', 'key_comuna'], inplace=True)

    df.to_csv(consolidado_path, index=False, sep=';', encoding='utf-8-sig')
    print(f'[✓] Coordenadas completadas en {consolidado_path}')


if __name__ == '__main__':
    main()
