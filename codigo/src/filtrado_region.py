
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filtra registros de "ckan_ruea_2023.xlsx" para la Región Metropolitana de Santiago (o la región que indiques).
Guarda resultados en Excel y CSV preservando columnas originales.

Uso:
  python filtrar_ruea_rm.py --input ckan_ruea_2023.xlsx --region "Metropolitana de Santiago" --outbase ckan_ruea_2023_RM

Requisitos: pandas, openpyxl
    pip install pandas openpyxl
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

EXPECTED_COLS = [
    "año","id_vu","declaracion_id","razon_social","rut_razon_social","nombre_establecimiento",
    "ciiu4","ciiu4_id","ciiu6","ciiu6_id","rubro","rubro_id","region","provincia","comuna",
    "codigo_unico_territorial","latitud","longitud","tipo_fuente","source_id","codigo_fuente",
    "combustible_primario","ccf8_primario","combustible_secundario","ccf8_secundario","ccf8_procesos",
    "contaminante_id","contaminante","emision_combustible_primario","emision_combustible_secundario",
    "emision_procesos","emision_total","origen_data","emision_retc","tipo_outlier"
]

NUMERIC_COMMA_COLS = [
    "latitud","longitud",
    "emision_combustible_primario","emision_combustible_secundario","emision_procesos","emision_total","emision_retc"
]

def to_float_locale(val):
    """Convierte strings con coma decimal (y notación científica con coma) a float. Deja NaN si no se puede."""
    if pd.isna(val):
        return pd.NA
    if isinstance(val, (int, float)):
        return val
    s = str(val).strip()
    if not s:
        return pd.NA
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return pd.NA

def normalize_colnames(df):
    mapping = {c: c.strip() for c in df.columns}
    df = df.rename(columns=mapping)
    if all(col in df.columns for col in EXPECTED_COLS):
        df = df[EXPECTED_COLS]
    return df

def normalize_text(s):
    if pd.isna(s):
        return ""
    return str(s).strip()

def main():
    ap = argparse.ArgumentParser(description="Filtra RUEA por región")
    ap.add_argument("--input", required=True, help="Ruta al Excel de entrada (ckan_ruea_2023.xlsx)")
    ap.add_argument("--region", default="Metropolitana de Santiago", help="Nombre exacto de la región a filtrar")
    ap.add_argument("--outbase", default="ckan_ruea_2023_RM", help="Prefijo base de los archivos de salida")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[✗] No se encontró el archivo: {in_path}", file=sys.stderr)
        sys.exit(1)

    try:
        df = pd.read_excel(in_path, dtype=str)
    except Exception as e:
        print(f"[✗] Error leyendo Excel: {e}", file=sys.stderr)
        sys.exit(1)

    df = normalize_colnames(df)

    if "region" not in df.columns:
        print("[✗] La columna 'region' no existe en el archivo.", file=sys.stderr)
        sys.exit(1)

    df["region_norm"] = df["region"].map(lambda x: normalize_text(x).lower())
    region_target = args.region.strip().lower()

    filtered = df[df["region_norm"] == region_target].copy()

    for col in NUMERIC_COMMA_COLS:
        if col in filtered.columns:
            filtered[col] = filtered[col].map(to_float_locale)

    if "region_norm" in filtered.columns:
        filtered = filtered.drop(columns=["region_norm"])

    out_xlsx = Path(f"{args.outbase}.xlsx")
    out_csv = Path(f"{args.outbase}.csv")

    cols = [c for c in EXPECTED_COLS if c in filtered.columns] + [c for c in filtered.columns if c not in EXPECTED_COLS]
    filtered = filtered[cols]

    try:
        filtered.to_excel(out_xlsx, index=False)
        filtered.to_csv(out_csv, index=False, encoding="utf-8-sig")
    except Exception as e:
        print(f"[✗] Error guardando salidas: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[✓] Filtrado completado.")
    print(f"    Región objetivo: {args.region}")
    print(f"    Filas encontradas: {len(filtered)}")
    print(f"    Columnas en salida: {len(filtered.columns)}")
    print(f"    Archivos: {out_xlsx} , {out_csv}")

if __name__ == "__main__":
    main()
