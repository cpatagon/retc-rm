
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspección de encabezados RUEA-EFP
----------------------------------
Escanea `data/raw/descargas_retc/` para archivos `ruea-efp-*-ckan.csv` y `ruea-efp-*-ckan.xlsx`,
detecta codificación (CSV) y separador, extrae encabezados y genera:

1) data/interim/diagnostico_archivos_originales/diagnostico_headers.csv
2) data/interim/diagnostico_archivos_originales/columnas_distintas_map.csv
3) data/interim/diagnostico_archivos_originales/columnas_normalizadas_vocab.csv

Uso:
  python inspeccionar_ruea_headers.py --root .

Requisitos: pandas, openpyxl
    pip install pandas openpyxl
"""
import argparse
import csv
import sys
import unicodedata
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd

TRY_ENCODINGS = ["utf-8-sig", "utf-8", "cp1252", "latin-1", "iso-8859-1"]

def remove_diacritics(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )

def normalize_name(name: str) -> str:
    if name is None:
        return ""
    s = str(name).strip()
    s = remove_diacritics(s)
    s = s.lower()
    for ch in [" ", "\t", "\r", "\n", "-", "/", "\\", ".", ",", ";", ":"]:
        s = s.replace(ch, "_")
    while "__" in s:
        s = s.replace("__", "_")
    s = s.strip("_")
    return s

def detect_encoding_and_delimiter(path: Path):
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

def read_csv_header(path: Path):
    enc, delim = detect_encoding_and_delimiter(path)
    with open(path, "r", encoding=enc, newline="") as f:
        reader = csv.reader(f, delimiter=delim)
        for row in reader:
            header = row
            break
    return enc, delim, [h.strip() for h in header]

def read_xlsx_header(path: Path):
    df = pd.read_excel(path, dtype=str, nrows=0)
    return list(df.columns)

def main():
    ap = argparse.ArgumentParser(description="Inspecciona encabezados y codificación de archivos RUEA-EFP")
    ap.add_argument(
        "--root",
        default=None,
        help="Directorio raíz del proyecto (por defecto, la raíz del repo)",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    in_dir = root / "data" / "raw" / "descargas_retc"
    out_dir = root / "data" / "interim" / "diagnostico_archivos_originales"
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(in_dir.glob("ruea-efp-*-ckan.csv"))
    xls_files = sorted(in_dir.glob("ruea-efp-*-ckan.xlsx"))

    if not csv_files and not xls_files:
        print(f"[!] No se encontraron archivos ruea-efp-*-ckan.(csv|xlsx) en {in_dir}", file=sys.stderr)
        sys.exit(1)

    rows_diag = []
    all_columns_counter = Counter()
    original_to_norm = defaultdict(int)
    original_to_files = defaultdict(set)
    norm_to_originals = defaultdict(Counter)
    norm_to_files = defaultdict(set)

    for p in csv_files:
        try:
            enc, delim, headers = read_csv_header(p)
            norm_headers = [normalize_name(h) for h in headers]
            rows_diag.append({
                "archivo": p.name,
                "tipo": "csv",
                "encoding_detectado": enc,
                "separador": delim,
                "num_columnas": len(headers),
                "columnas_original": "|".join(headers),
                "columnas_normalizadas": "|".join(norm_headers),
            })
            for h, nh in zip(headers, norm_headers):
                all_columns_counter[h] += 1
                original_to_norm[h] += 1
                original_to_files[h].add(p.name)
                norm_to_originals[nh][h] += 1
                norm_to_files[nh].add(p.name)
        except Exception as e:
            rows_diag.append({
                "archivo": p.name,
                "tipo": "csv",
                "encoding_detectado": None,
                "separador": None,
                "num_columnas": None,
                "columnas_original": f"[error] {e}",
                "columnas_normalizadas": ""
            })

    for p in xls_files:
        try:
            headers = read_xlsx_header(p)
            norm_headers = [normalize_name(h) for h in headers]
            rows_diag.append({
                "archivo": p.name,
                "tipo": "xlsx",
                "encoding_detectado": "",
                "separador": "",
                "num_columnas": len(headers),
                "columnas_original": "|".join(headers),
                "columnas_normalizadas": "|".join(norm_headers),
            })
            for h, nh in zip(headers, norm_headers):
                all_columns_counter[h] += 1
                original_to_norm[h] += 1
                original_to_files[h].add(p.name)
                norm_to_originals[nh][h] += 1
                norm_to_files[nh].add(p.name)
        except Exception as e:
            rows_diag.append({
                "archivo": p.name,
                "tipo": "xlsx",
                "encoding_detectado": "",
                "separador": "",
                "num_columnas": None,
                "columnas_original": f"[error] {e}",
                "columnas_normalizadas": ""
            })

    df_diag = pd.DataFrame(rows_diag, columns=[
        "archivo","tipo","encoding_detectado","separador","num_columnas","columnas_original","columnas_normalizadas"
    ])
    df_diag.to_csv(out_dir / "diagnostico_headers.csv", index=False, encoding="utf-8-sig")

    rows_map = []
    for orig, count in original_to_norm.items():
        rows_map.append({
            "columna_original": orig,
            "columna_normalizada": normalize_name(orig),
            "apariciones": count,
            "archivos_distintos": len(original_to_files[orig]),
        })
    df_map = pd.DataFrame(rows_map, columns=["columna_original","columna_normalizada","apariciones","archivos_distintos"])
    df_map.sort_values(["columna_normalizada","columna_original"], inplace=True)
    df_map.to_csv(out_dir / "columnas_distintas_map.csv", index=False, encoding="utf-8-sig")

    rows_vocab = []
    for nh, variants in norm_to_originals.items():
        variantes = list(variants.items())
        variantes.sort(key=lambda t: (-t[1], t[0]))
        ejemplos = [v for v, _ in variantes[:5]]
        rows_vocab.append({
            "columna_normalizada": nh,
            "variantes_detectadas": len(variants),
            "ejemplos_variantes": " | ".join(ejemplos),
            "archivos_con_esta_columna": len(norm_to_files[nh])
        })
    df_vocab = pd.DataFrame(rows_vocab, columns=[
        "columna_normalizada","variantes_detectadas","ejemplos_variantes","archivos_con_esta_columna"
    ]).sort_values("columna_normalizada")
    df_vocab.to_csv(out_dir / "columnas_normalizadas_vocab.csv", index=False, encoding="utf-8-sig")

    print("[✓] Inspección completada.")
    print(f"  - {out_dir / 'diagnostico_headers.csv'}")
    print(f"  - {out_dir / 'columnas_distintas_map.csv'}")
    print(f"  - {out_dir / 'columnas_normalizadas_vocab.csv'}")

if __name__ == "__main__":
    main()
