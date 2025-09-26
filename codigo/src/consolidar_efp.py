
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolida archivos EFP filtrados por RM en dos bloques:
  - 2005–2018 (estructura EFP v1 + 'sistema' 2016–2018)
  - 2019–2022 (EFP v2 con CIIU6, tipo/combustibles, emisiones)

Luego une ambos en un consolidado 2005–2022 (rellenando columnas faltantes con vacío).

Pensado para ejecutarse desde `src/`.
Lee de:   ../data/interim/filtrados_region/CSV
Escribe en: el mismo directorio.

Uso:
  cd src
  python consolidar_efp.py

Opcionales:
  --indir  ../data/interim/filtrados_region/CSV
  --outbase EFP_RM   (prefijo para nombres de salida)
"""
import argparse
from pathlib import Path
import pandas as pd

def load_csv(path):
    return pd.read_csv(path, dtype=str, encoding='utf-8', keep_default_na=False, na_values=[])

RENAMES_COMMON = {
    'contaminante': 'contaminantes',
    'id_contaminante': 'id_contaminantes',
    'rut': 'rut_razon_social',
    'CCF8_primario': 'ccf8_primario',
    'CCF8_secundario': 'ccf8_secundario',
    'CCF8_materia_prima': 'ccf8_materia_prima',
}

ORDER_2005_2018 = [
    'año','razon_social','rut_razon_social','nombre_establecimiento','id_vu',
    'ciiu4','id_ciiu4','rubro_vu','id_rubro_vu','region','provincia','comuna','id_comuna',
    'latitud','longitud','cantidad_toneladas','unidad',
    'contaminantes','id_contaminantes','fuente_emisora_general','id_fuente_emisora',
    'sistema'
]

ORDER_2019_2022 = [
    'año','razon_social','rut_razon_social','nombre_establecimiento','id_vu',
    'ciiu4','id_ciiu4','ciiu6','id_ciiu6','rubro_vu','id_rubro_vu',
    'region','provincia','comuna','id_comuna','latitud','longitud',
    'cantidad_toneladas','unidad',
    'contaminantes','id_contaminantes','fuente_emisora_general','id_fuente_emisora',
    'tipo_fuente','combustible_primario','ccf8_primario','combustible_secundario','ccf8_secundario','ccf8_materia_prima',
    'emision_primario','emision_secundario','emision_materia_prima',
    'sistema'
]

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: str(c).strip() for c in df.columns})
    for old, new in RENAMES_COMMON.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
    return df

def keep_and_order(df: pd.DataFrame, order: list) -> pd.DataFrame:
    for c in order:
        if c not in df.columns:
            df[c] = ""
    extras = [c for c in df.columns if c not in order]
    return df[order + extras]

def collect_files(indir: Path, years):
    files = []
    for y in years:
        p = indir / f"ruea-efp-{y}-ckan_RM.csv"
        if p.exists():
            files.append(p)
    return files

def concat_save(dfs, out_csv):
    if not dfs:
        return None
    out = pd.concat(dfs, ignore_index=True)
    out.to_csv(out_csv, index=False, encoding='utf-8-sig')
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '--indir',
        default='../data/interim/filtrados_region/CSV',
        help='Carpeta con CSV filtrados (RM)',
    )
    ap.add_argument('--outbase', default='EFP_RM', help='Prefijo para nombres de salida')
    args = ap.parse_args()

    indir = Path(args.indir).resolve()
    outdir = indir

    y_2005_2018 = list(range(2005, 2019))
    y_2019_2022 = list(range(2019, 2023))

    files_2005_2018 = collect_files(indir, y_2005_2018)
    files_2019_2022 = collect_files(indir, y_2019_2022)

    dfs_2005_2018 = []
    for f in files_2005_2018:
        df = load_csv(f)
        df = normalize_columns(df)
        df = keep_and_order(df, ORDER_2005_2018)
        dfs_2005_2018.append(df)

    dfs_2019_2022 = []
    for f in files_2019_2022:
        df = load_csv(f)
        df = normalize_columns(df)
        df = keep_and_order(df, ORDER_2019_2022)
        dfs_2019_2022.append(df)

    out_2005_2018 = outdir / f"{args.outbase}_2005_2018_consolidado.csv"
    out_2019_2022 = outdir / f"{args.outbase}_2019_2022_consolidado.csv"
    c1 = concat_save(dfs_2005_2018, out_2005_2018)
    c2 = concat_save(dfs_2019_2022, out_2019_2022)

    if c1 is not None and c2 is not None:
        all_cols = list(dict.fromkeys(list(c1.columns) + list(c2.columns)))
        for df in (c1, c2):
            for c in all_cols:
                if c not in df.columns:
                    df[c] = ""
        c1 = c1[all_cols]
        c2 = c2[all_cols]
        combined = pd.concat([c1, c2], ignore_index=True)
        out_both = outdir / f"{args.outbase}_2005_2022_consolidado.csv"
        combined.to_csv(out_both, index=False, encoding='utf-8-sig')

    print("[✓] Consolidación lista.")
    print("  -", out_2005_2018 if files_2005_2018 else "(sin archivos 2005–2018)")
    print("  -", out_2019_2022 if files_2019_2022 else "(sin archivos 2019–2022)")
    if (indir / f"{args.outbase}_2005_2022_consolidado.csv").exists():
        print("  -", indir / f"{args.outbase}_2005_2022_consolidado.csv")

if __name__ == '__main__':
    main()
