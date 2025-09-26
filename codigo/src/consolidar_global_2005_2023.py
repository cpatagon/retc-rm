#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolida EFP 2005–2022 + RUEA 2023 desde una carpeta dada.

- Modo `full` (por defecto): "outer union" conservando todas las columnas, con
  renombres triviales para equiparar conceptos y una columna `fuente_esquema`.
- Modo `minimo`: proyecta ambos a un set común mínimo (comparabilidad 2005–2023).

Uso típico:
  python consolidar_global_2005_2023.py \
      --indir "../outputs/tablas/retc_consolidados/RETConsolidado_original"

Opcionales:
  --modo {full,minimo}               (por defecto: full)
  --efp-name EFP_RM_2005_2022_consolidado.csv
  --r23-name ruea-efp-2023-ckan_RM.csv
  --out    nombre_de_salida.csv      (si no se indica, se infiere según el modo)
"""
import argparse
from pathlib import Path
import pandas as pd

# -----------------------------
# Utilidades de carga
# -----------------------------

def read_csv_any(path: Path) -> pd.DataFrame:
    # intenta utf-8, luego latin-1
    try:
        return pd.read_csv(path, dtype=str, encoding="utf-8")
    except Exception:
        return pd.read_csv(path, dtype=str, encoding="latin-1")

# -----------------------------
# Renombres canónicos
# -----------------------------
RENAME_MAP_R23 = {
    "ciiu4_id": "id_ciiu4",
    "contaminante": "contaminantes",
    "contaminante_id": "id_contaminantes",
}
RENAME_MAP_EFP = {
    "CCF8_primario": "ccf8_primario",
    "CCF8_secundario": "ccf8_secundario",
    "CCF8_materia_prima": "ccf8_materia_prima",
}

# Conjunto mínimo común sugerido
MIN_COMMON = [
    "año","razon_social","nombre_establecimiento","id_vu",
    "ciiu4","id_ciiu4","region","provincia","comuna","latitud","longitud",
]

# Canon extendido que suele alinear conceptos equivalentes
CANON_EQUIV = [
    # básicos
    "año","razon_social","rut_razon_social","nombre_establecimiento","id_vu",
    "ciiu4","id_ciiu4","ciiu6","id_ciiu6",
    "region","provincia","comuna","latitud","longitud",
    # contaminante y fuente
    "contaminantes","id_contaminantes",
    "tipo_fuente","combustible_primario","ccf8_primario","combustible_secundario","ccf8_secundario",
]


def ensure_columns(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df


def consolidate_full(df_efp: pd.DataFrame, df_r23: pd.DataFrame) -> pd.DataFrame:
    # Renombres triviales
    df_r23 = df_r23.rename(columns={k:v for k,v in RENAME_MAP_R23.items() if k in df_r23.columns})
    df_efp = df_efp.rename(columns={k:v for k,v in RENAME_MAP_EFP.items() if k in df_efp.columns})

    # Asegurar columnas canónicas
    df_efp = ensure_columns(df_efp, CANON_EQUIV)
    df_r23 = ensure_columns(df_r23, CANON_EQUIV)

    # Marcar procedencia
    df_efp["fuente_esquema"] = "EFP"
    df_r23["fuente_esquema"] = "RUEA2023"

    # Unión por superconjunto de columnas
    all_cols = list(dict.fromkeys(df_efp.columns.tolist() + df_r23.columns.tolist()))
    for df in (df_efp, df_r23):
        for c in all_cols:
            if c not in df.columns:
                df[c] = ""
    df_efp = df_efp[all_cols]
    df_r23 = df_r23[all_cols]
    return pd.concat([df_efp, df_r23], ignore_index=True)


def consolidate_min(df_efp: pd.DataFrame, df_r23: pd.DataFrame) -> pd.DataFrame:
    df_r23 = df_r23.rename(columns={k:v for k,v in RENAME_MAP_R23.items() if k in df_r23.columns})
    df_efp = ensure_columns(df_efp, MIN_COMMON)
    df_r23 = ensure_columns(df_r23, MIN_COMMON)
    return pd.concat([df_efp[MIN_COMMON], df_r23[MIN_COMMON]], ignore_index=True)


def main():
    ap = argparse.ArgumentParser(description="Consolida EFP_2005_2022 + RUEA_2023")
    ap.add_argument(
        "--indir",
        default="../outputs/tablas/retc_consolidados/RETConsolidado_original",
        help="Carpeta que contiene los dos archivos a consolidar",
    )
    ap.add_argument("--efp-name", dest="efp_name", default="EFP_RM_2005_2022_consolidado.csv")
    ap.add_argument("--r23-name", dest="r23_name", default="ruea-efp-2023-ckan_RM.csv")
    ap.add_argument("--modo", choices=["full","minimo"], default="full")
    ap.add_argument("--out", default=None, help="Nombre del archivo de salida (.csv)")
    args = ap.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    efp_path = indir / args.efp_name
    r23_path = indir / args.r23_name

    if not efp_path.exists() or not r23_path.exists():
        raise SystemExit(f"No se encuentran ambos archivos en {indir}:\n  - {efp_path}\n  - {r23_path}")

    df_efp = read_csv_any(efp_path)
    df_r23 = read_csv_any(r23_path)

    if args.modo == "full":
        outname = args.out or "RUEA_global_2005_2023_full.csv"
        out = consolidate_full(df_efp, df_r23)
    else:
        outname = args.out or "RUEA_global_2005_2023_minimo.csv"
        out = consolidate_min(df_efp, df_r23)

    out_path = indir / outname
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[✓] Consolidado guardado en: {out_path}")

if __name__ == "__main__":
    main()
