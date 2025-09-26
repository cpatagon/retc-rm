#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filtra TODOS los archivos descargados en `data/raw/descargas_retc` por región y
escribe los resultados en `data/interim/filtrados_region`.

Pensado para ejecutarse desde la carpeta `src/` del proyecto.

Soporta dos esquemas:
  A) EFP (ruea-efp-YYYY-ckan.csv|xlsx)  -> columnas tipo: año;razon_social;...;id_fuente_emisora
  B) RUEA 2023 (ckan_ruea_2023.csv|xlsx) -> columnas extendidas de RUEA 2023

Si existe el archivo de diagnóstico `data/interim/diagnostico_archivos_originales/diagnostico_headers.csv`,
usa su `encoding_detectado` y `separador` por archivo. Si no, detecta automáticamente.

Uso:
  cd src
  python filtrado_region_todo.py --region "Metropolitana de Santiago"

Opcionales:
  --outprefix "RM_"   # agrega prefijo a los nombres de salida
  --solo {efp,2023}   # procesa solo una familia de archivos

Requisitos:
  pip install pandas openpyxl
"""
from __future__ import annotations

import argparse
import csv
import sys
import re
from pathlib import Path
from typing import Dict, Optional, Tuple, List

import pandas as pd

# ------------------------------------------
# Configuración de columnas esperadas
# ------------------------------------------

EFP_EXPECTED = [
    "año","razon_social","rut_razon_social","nombre_establecimiento","id_vu",
    "ciiu4","id_ciiu4","rubro_vu","id_rubro_vu","region","provincia","comuna",
    "id_comuna","latitud","longitud","cantidad_toneladas","unidad",
    "contaminantes","id_contaminantes","fuente_emisora_general","id_fuente_emisora",
]

RUEA2023_EXPECTED = [
    "año","id_vu","declaracion_id","razon_social","rut_razon_social","nombre_establecimiento",
    "ciiu4","ciiu4_id","ciiu6","ciiu6_id","rubro","rubro_id","region","provincia","comuna",
    "codigo_unico_territorial","latitud","longitud","tipo_fuente","source_id","codigo_fuente",
    "combustible_primario","ccf8_primario","combustible_secundario","ccf8_secundario","ccf8_procesos",
    "contaminante_id","contaminante","emision_combustible_primario","emision_combustible_secundario",
    "emision_procesos","emision_total","origen_data","emision_retc","tipo_outlier",
]

# Columnas numéricas con coma decimal por esquema
EFP_NUMERIC = ["latitud","longitud","cantidad_toneladas"]
RUEA2023_NUMERIC = [
    "latitud","longitud","emision_combustible_primario","emision_combustible_secundario",
    "emision_procesos","emision_total","emision_retc"
]

TRY_ENCODINGS = ["utf-8-sig", "utf-8", "cp1252", "latin-1", "iso-8859-1"]

# ------------------------------------------
# Utilidades
# ------------------------------------------

def remove_diacritics(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def norm_name(name: str) -> str:
    if name is None:
        return ""
    s = str(name).strip()
    s = remove_diacritics(s).lower()
    for ch in [" ", "\t", "\r", "\n", "-", "/", "\\", ".", ",", ";", ":"]:
        s = s.replace(ch, "_")
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")

def to_float_locale(val):
    if pd.isna(val):
        return pd.NA
    if isinstance(val, (int, float)):
        return val
    s = str(val).strip()
    if s == "":
        return pd.NA
    s = s.replace(",", ".")
    s = re.sub(r"\s+", "", s)
    try:
        return float(s)
    except Exception:
        return pd.NA

def detect_encoding_and_delimiter(path: Path) -> Tuple[str, str]:
    sample_bytes = path.read_bytes()[:131072]
    text = None
    enc_used = None
    for enc in TRY_ENCODINGS:
        try:
            text = sample_bytes.decode(enc)
            enc_used = enc
            break
        except Exception:
            continue
    if text is None:
        enc_used = "cp1252"
        text = sample_bytes.decode(enc_used, errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text, delimiters=";,|\t,")
        delim = dialect.delimiter
    except Exception:
        delim = ";" if text.count(";") >= text.count(",") else ","
    return enc_used, delim

def read_diagnostico_map(diag_csv: Path) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
    """Lee diagnostico_headers.csv y retorna {archivo -> (encoding, separador)}"""
    mapping = {}
    if not diag_csv.exists():
        return mapping
    try:
        df = pd.read_csv(diag_csv, dtype=str, encoding="utf-8")
    except Exception:
        df = pd.read_csv(diag_csv, dtype=str, encoding="latin-1")
    for _, row in df.iterrows():
        archivo = str(row.get("archivo", "")).strip()
        enc = str(row.get("encoding_detectado", "") or "").strip() or None
        sep = str(row.get("separador", "") or "").strip() or None
        if archivo:
            mapping[archivo] = (enc, sep)
    return mapping

def load_csv_with_diag(path: Path, diag_map: Dict[str, Tuple[Optional[str], Optional[str]]]) -> pd.DataFrame:
    enc, sep = diag_map.get(path.name, (None, None))
    if enc is None or sep is None:
        enc, sep = detect_encoding_and_delimiter(path)
    # pandas robusto
    try:
        return pd.read_csv(path, sep=sep, dtype=str, encoding=enc, engine="python", on_bad_lines="skip")
    except TypeError:
        return pd.read_csv(path, sep=sep, dtype=str, encoding=enc, engine="python")

def load_any(path: Path, diag_map: Dict[str, Tuple[Optional[str], Optional[str]]]) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return load_csv_with_diag(path, diag_map)
    else:
        return pd.read_excel(path, dtype=str)

# ------------------------------------------
# Normalización de columnas
# ------------------------------------------

# Sinónimos por nombre normalizado -> nombre canónico
EFP_SYNONYMS = {
    "ano": "año",
    "anio": "año",
    "a_o": "año",
    "razon_social": "razon_social",
    "rut_razon_social": "rut_razon_social",
    "nombre_establecimiento": "nombre_establecimiento",
    "id_vu": "id_vu",
    "ciiu4": "ciiu4",
    "id_ciiu4": "id_ciiu4",
    "ciiu4_id": "id_ciiu4",
    "rubro_vu": "rubro_vu",
    "id_rubro_vu": "id_rubro_vu",
    "region": "region",
    "provincia": "provincia",
    "comuna": "comuna",
    "id_comuna": "id_comuna",
    "latitud": "latitud",
    "longitud": "longitud",
    "cantidad_toneladas": "cantidad_toneladas",
    "cantidad_tonelada": "cantidad_toneladas",
    "unidad": "unidad",
    "contaminantes": "contaminantes",
    "id_contaminantes": "id_contaminantes",
    "fuente_emisora_general": "fuente_emisora_general",
    "id_fuente_emisora": "id_fuente_emisora",
}

RUEA2023_SYNONYMS = {
    "ano": "año", "anio": "año", "a_o":"año",
    "id_vu": "id_vu",
    "declaracion_id": "declaracion_id",
    "razon_social": "razon_social",
    "rut_razon_social": "rut_razon_social",
    "nombre_establecimiento": "nombre_establecimiento",
    "ciiu4": "ciiu4",
    "ciiu4_id": "ciiu4_id",
    "id_ciiu4": "ciiu4_id",
    "ciiu6": "ciiu6",
    "ciiu6_id": "ciiu6_id",
    "rubro": "rubro",
    "rubro_id": "rubro_id",
    "region": "region",
    "provincia": "provincia",
    "comuna": "comuna",
    "codigo_unico_territorial": "codigo_unico_territorial",
    "latitud": "latitud",
    "longitud": "longitud",
    "tipo_fuente": "tipo_fuente",
    "source_id": "source_id",
    "codigo_fuente": "codigo_fuente",
    "combustible_primario": "combustible_primario",
    "ccf8_primario": "ccf8_primario",
    "combustible_secundario": "combustible_secundario",
    "ccf8_secundario": "ccf8_secundario",
    "ccf8_procesos": "ccf8_procesos",
    "contaminante_id": "contaminante_id",
    "contaminante": "contaminante",
    "emision_combustible_primario": "emision_combustible_primario",
    "emision_combustible_secundario": "emision_combustible_secundario",
    "emision_procesos": "emision_procesos",
    "emision_total": "emision_total",
    "origen_data": "origen_data",
    "emision_retc": "emision_retc",
    "tipo_outlier": "tipo_outlier",
}

def normalize_columns(df: pd.DataFrame, schema: str) -> pd.DataFrame:
    # strip
    df = df.rename(columns={c: str(c).strip() for c in df.columns})
    # índice normalizado -> columna actual
    norm_index = {norm_name(c): c for c in df.columns}
    if schema == "efp":
        synonyms = EFP_SYNONYMS
        expected = EFP_EXPECTED
    else:
        synonyms = RUEA2023_SYNONYMS
        expected = RUEA2023_EXPECTED

    rename_map = {}
    for norm, current_col in norm_index.items():
        if norm in synonyms:
            target = synonyms[norm]
            if current_col != target:
                rename_map[current_col] = target
    if rename_map:
        df = df.rename(columns=rename_map)

    # Reordenar: primero expected, luego el resto
    present = [c for c in expected if c in df.columns]
    rest = [c for c in df.columns if c not in present]
    df = df[present + rest]
    return df


def normalize_region_text(s: str) -> str:
    t = remove_diacritics(str(s).lower())
    for ch in ["\t", "\r", "\n", ",", ".", ";", ":"]:
        t = t.replace(ch, " ")
    t = t.replace("region", " ")  # quitar la palabra 'región/region'
    t = re.sub(r"\s+", " ", t).strip()
    return t

def region_matches(value: str, target: str) -> bool:
    if value is None:
        return False
    v = normalize_region_text(value)
    t = normalize_region_text(target)
    # Aliases comunes para RM
    aliases_rm = {"metropolitana de santiago", "metropolitana", "rm", "metropolitana santiago"}
    if t in {"metropolitana de santiago", "metropolitana", "rm"}:
        return v in aliases_rm or ("metropolitana" in v and "santiago" in v) or v == t
    # fallback: igualdad estricta normalizada
    return v == t


# ------------------------------------------
# Procesamiento por archivo
# ------------------------------------------

def detect_schema(path: Path) -> str:
    name = path.name.lower()
    if name.startswith("ruea-efp-"):
        return "efp"
    if name.startswith("ckan_ruea_2023"):
        return "ruea2023"
    # fallback por contenido:
    return "efp"  # conservador

def process_one(path: Path, diag_map, region_target: str) -> Tuple[pd.DataFrame, str]:
    schema = detect_schema(path)
    df = load_any(path, diag_map)
    df = normalize_columns(df, "efp" if schema == "efp" else "ruea2023")

    if "region" not in df.columns:
        raise KeyError(f"{path.name}: no se encuentra columna 'region' tras normalización. Columnas: {list(df.columns)}")

    # Filtrar región (flexible con aliases/equivalencias)
    df["__region_match__"] = df["region"].map(lambda x: region_matches(x, region_target))
    filtered = df[df["__region_match__"] == True].copy()
    if "__region_match__" in filtered.columns:
        filtered.drop(columns=["__region_match__"], inplace=True)


    # Numéricos
    if schema == "efp":
        for col in EFP_NUMERIC:
            if col in filtered.columns:
                filtered[col] = filtered[col].map(to_float_locale)
    else:
        for col in RUEA2023_NUMERIC:
            if col in filtered.columns:
                filtered[col] = filtered[col].map(to_float_locale)

    return filtered, schema

# ------------------------------------------
# Main
# ------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Filtra todos los archivos RUEA/RUEA-EFP por región")
    ap.add_argument("--region", default="Metropolitana de Santiago", help="Región exacta a filtrar")
    ap.add_argument("--outprefix", default="", help="Prefijo opcional en archivos de salida")
    ap.add_argument("--solo", choices=["efp","2023"], default=None, help="Procesar solo una familia")
    ap.add_argument(
        "--root",
        default=None,
        help="Ruta a la raíz del proyecto que contiene la carpeta 'data/' (opcional)",
    )
    args = ap.parse_args()

    # Rutas (por defecto relativas a src/, pero se puede forzar con --root)
    here = Path(__file__).resolve().parent
    root = Path(args.root).resolve() if args.root else here.parents[1]
    in_dir = root / "data" / "raw" / "descargas_retc"
    out_dir = root / "data" / "interim" / "filtrados_region"
    diag_dir = root / "data" / "interim" / "diagnostico_archivos_originales"
    out_dir.mkdir(parents=True, exist_ok=True)
    diag_dir.mkdir(parents=True, exist_ok=True)

    diag_csv = diag_dir / "diagnostico_headers.csv"
    diag_map = read_diagnostico_map(diag_csv)

    # Candidatos
    candidates: List[Path] = []
    if args.solo in (None, "efp"):
        candidates += sorted(in_dir.glob("ruea-efp-*-ckan.csv"))
        candidates += sorted(in_dir.glob("ruea-efp-*-ckan.xlsx"))
    if args.solo in (None, "2023"):
        candidates += sorted(in_dir.glob("ckan_ruea_2023.csv"))
        candidates += sorted(in_dir.glob("ckan_ruea_2023.xlsx"))

    if not candidates:
        print(f"[!] No se encontraron archivos a procesar en {in_dir}")
        sys.exit(1)

    resumen_rows = []
    efp_consol: List[pd.DataFrame] = []
    r2023_consol: List[pd.DataFrame] = []

    for p in candidates:
        # Leer entradas totales (para resumen)
        try:
            df_in = load_any(p, diag_map)
            rows_in = len(df_in)
        except Exception as e:
            resumen_rows.append({"archivo": p.name, "filas_entrada": None, "filas_RM": None, "estado": f"error_lectura: {e}"})
            continue

        try:
            filtered, schema = process_one(p, diag_map, args.region)
            rows_out = len(filtered)
            # nombres de salida
            base = p.stem
            suf = "RM" if args.region.strip().lower() == "metropolitana de santiago" else args.region.strip().replace(" ", "_")
            base_out = f"{args.outprefix}{base}_{suf}" if args.outprefix else f"{base}_{suf}"
            out_csv = out_dir / f"{base_out}.csv"
            out_xlsx = out_dir / f"{base_out}.xlsx"
            filtered.to_csv(out_csv, index=False, encoding="utf-8-sig")
            filtered.to_excel(out_xlsx, index=False)
            estado = "ok"
            # Acumular para consolidado
            if schema == "efp":
                efp_consol.append(filtered)
            else:
                r2023_consol.append(filtered)
        except Exception as e:
            rows_out = None
            estado = f"error_proceso: {e}"

        resumen_rows.append({"archivo": p.name, "filas_entrada": rows_in, "filas_RM": rows_out, "estado": estado})

    # Guardar resumen
    resumen_df = pd.DataFrame(resumen_rows, columns=["archivo","filas_entrada","filas_RM","estado"])
    resumen_df.to_csv(out_dir / "resumen_filtrado_region.csv", index=False, encoding="utf-8-sig")

    # Consolidados (si hay)
    def maybe_to_excel(df: pd.DataFrame, path: Path) -> None:
        max_rows_excel = 1_048_576
        if len(df) > max_rows_excel:
            print(f"[!] Omitiendo exportación XLSX ({path.name}) porque excede {max_rows_excel} filas (actual: {len(df)}).")
            return
        df.to_excel(path, index=False)

    if efp_consol:
        efp_all = pd.concat(efp_consol, ignore_index=True)
        efp_csv = out_dir / "ruea_efp_RM_consolidado.csv"
        efp_all.to_csv(efp_csv, index=False, encoding="utf-8-sig")
        maybe_to_excel(efp_all, out_dir / "ruea_efp_RM_consolidado.xlsx")
    if r2023_consol:
        r23_all = pd.concat(r2023_consol, ignore_index=True)
        r23_csv = out_dir / "ckan_ruea_2023_RM_consolidado.csv"
        r23_all.to_csv(r23_csv, index=False, encoding="utf-8-sig")
        maybe_to_excel(r23_all, out_dir / "ckan_ruea_2023_RM_consolidado.xlsx")

    print("[✓] Proceso completado.")
    print(f"    Entrada: {in_dir}")
    print(f"    Salida:  {out_dir}")
    print(f"    Resumen: {out_dir / 'resumen_filtrado_region.csv'}")

if __name__ == "__main__":
    main()
