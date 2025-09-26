#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Separa un consolidado RETC (2005–2023) en archivos por grupo canónico de contaminante.
- Entrada: un CSV con columnas al menos: id_contaminantes y/o contaminante_id (y opcionalmente 'contaminantes').
- Salida: carpeta con un CSV por grupo + resúmenes.

Uso:
  python separar_por_grupo_canonico.py \
    --in "/ruta/CONSOLIDADO_RETC_2005-2023.csv" \
    --outdir "/ruta/salida/por_grupo_canonico"
"""
import argparse, re
from pathlib import Path
import pandas as pd

# ====== Mapeo ID -> Grupo canónico (ajústalo si sumas IDs) ======
ID_A_GRUPO = {
    116:"Toluene", 397:"Toluene",
    8:"Benzene", 98:"Benzene",
    261:"Methane",
    45:"Carbon dioxide (CO2)", 136:"Carbon dioxide (CO2)",
    73:"Carbon monoxide (CO)", 137:"Carbon monoxide (CO)",
    123:"Nitrogen oxides (NOx)", 303:"Nitrogen oxides (NOx)",
    304:"Nitrous oxide (N2O)",
    44:"Sulfur dioxide (SO2)", 380:"Sulfur dioxide (SO2)",
    381:"Sulfur oxides (SOx) [familia]",
    77:"Ammonia (NH3)", 87:"Ammonia (NH3)",
    84:"Lead (Pb)", 250:"Lead (Pb)",
    67:"Mercury (Hg)", 260:"Mercury (Hg)",
    80:"Particulate matter (PM, sin tamaño)", 336:"Particulate matter (PM, sin tamaño)",
    74:"PM10", 339:"PM10",
    122:"PM2.5", 341:"PM2.5",
    35:"Volatile organic compounds (VOC)", 417:"Volatile organic compounds (VOC)",
    121:"PCDD/F", 999:"PCDD/F",
    998:"Black Carbon",
    6:"Arsenic (As)", 93:"Arsenic (As)",
}

def to_int_safe(x):
    try:
        s = str(x).strip()
        if s == "": return None
        return int(float(s))  # por si viene "44.0"
    except:
        return None

def slug(s: str) -> str:
    s = re.sub(r"[\\/:*?\"<>|]+", "_", s)
    s = re.sub(r"\\s+", "_", s.strip())
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True, help="CSV consolidado (2005–2023)")
    ap.add_argument("--outdir", required=True, help="Carpeta de salida para los CSV por grupo")
    ap.add_argument("--xlsx", action="store_true", help="Además, exportar XLSX por grupo")
    args = ap.parse_args()

    infile = Path(args.infile).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # Leer CSV (intenta utf-8, luego latin-1)
    try:
        df = pd.read_csv(infile, dtype=str)
    except Exception:
        df = pd.read_csv(infile, dtype=str, encoding="latin-1")

    # Detectar columna de ID
    id_col = "id_contaminantes" if "id_contaminantes" in df.columns else (
             "contaminante_id"   if "contaminante_id"   in df.columns else None)
    if not id_col:
        raise SystemExit("No encontré columna de ID ('id_contaminantes' o 'contaminante_id').")

    # Columna de nombre (opcional, pero útil)
    name_col = "contaminantes" if "contaminantes" in df.columns else None

    # Asignar grupo
    df["_id_int_"] = df[id_col].map(to_int_safe)
    df["grupo_canonico"] = df["_id_int_"].map(lambda i: ID_A_GRUPO.get(i, "OTROS"))

    # Resúmenes
    resumen = (df.groupby("grupo_canonico")[id_col]
                 .size().reset_index(name="n_filas")
                 .sort_values("n_filas", ascending=False))
    resumen.to_csv(outdir / "resumen_por_grupo.csv", index=False, encoding="utf-8-sig")

    if name_col:
        dicc = (df.loc[df["grupo_canonico"]!="OTROS", ["_id_int_", name_col, "grupo_canonico"]]
                  .dropna().astype({name_col:str})
                  .drop_duplicates()
                  .sort_values(["grupo_canonico","_id_int_",name_col]))
        dicc.to_csv(outdir / "diccionario_id_nombre_por_grupo.csv", index=False, encoding="utf-8-sig")

    # Exportar un CSV por grupo
    grupos = sorted(df["grupo_canonico"].dropna().unique().tolist())
    for g in grupos:
        sub = df[df["grupo_canonico"] == g].drop(columns=["_id_int_"])
        fname = f"{slug(g)}.csv"
        sub.to_csv(outdir / fname, index=False, encoding="utf-8-sig")
        if args.xlsx:
            try:
                sub.to_excel(outdir / f"{slug(g)}.xlsx", index=False)
            except Exception:
                pass

    print("✓ Separación completada")
    print("  Entrada :", infile)
    print("  Salida  :", outdir)
    print("  Resumen :", outdir / "resumen_por_grupo.csv")

if __name__ == "__main__":
    main()
