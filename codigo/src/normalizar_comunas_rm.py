#!/usr/bin/env python3
"""Normaliza los nombres de comuna en las tablas RM fusionadas."""
from __future__ import annotations

import argparse
import csv
import unicodedata
from pathlib import Path
from typing import Dict, Set

import pandas as pd

# Lista canónica de comunas de la Región Metropolitana
CANON_COMUNAS: Dict[str, str] = {
    "santiago": "Santiago",
    "cerrillos": "Cerrillos",
    "cerro navia": "Cerro Navia",
    "conchali": "Conchalí",
    "el bosque": "El Bosque",
    "estacion central": "Estación Central",
    "huechuraba": "Huechuraba",
    "independencia": "Independencia",
    "la cisterna": "La Cisterna",
    "la florida": "La Florida",
    "la granja": "La Granja",
    "la pintana": "La Pintana",
    "la reina": "La Reina",
    "las condes": "Las Condes",
    "lo barnechea": "Lo Barnechea",
    "lo espejo": "Lo Espejo",
    "lo prado": "Lo Prado",
    "macul": "Macul",
    "maipu": "Maipú",
    "nunoa": "Ñuñoa",
    "pedro aguirre cerda": "Pedro Aguirre Cerda",
    "penalolen": "Peñalolén",
    "providencia": "Providencia",
    "pudahuel": "Pudahuel",
    "quilicura": "Quilicura",
    "quinta normal": "Quinta Normal",
    "recoleta": "Recoleta",
    "renca": "Renca",
    "san joaquin": "San Joaquín",
    "san miguel": "San Miguel",
    "san ramon": "San Ramón",
    "vitacura": "Vitacura",
    "puente alto": "Puente Alto",
    "pirque": "Pirque",
    "san jose de maipo": "San José de Maipo",
    "colina": "Colina",
    "lampa": "Lampa",
    "tiltil": "Tiltil",
    "san bernardo": "San Bernardo",
    "buin": "Buin",
    "calera de tango": "Calera de Tango",
    "paine": "Paine",
    "melipilla": "Melipilla",
    "alhue": "Alhué",
    "curacavi": "Curacaví",
    "maria pinto": "María Pinto",
    "san pedro": "San Pedro",
    "talagante": "Talagante",
    "el monte": "El Monte",
    "isla de maipo": "Isla de Maipo",
    "padre hurtado": "Padre Hurtado",
    "penaflor": "Peñaflor",
}

NA_VALUES = {"", "na", "nan", "none", "null"}


def normalize(text: str | None) -> str:
    if text is None:
        return ""
    s = unicodedata.normalize("NFKD", text.strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace('-', ' ')
    s = " ".join(s.split())
    return s


def main() -> None:
    parser = argparse.ArgumentParser(description="Normaliza nombres de comuna en tablas RM")
    parser.add_argument(
        "--indir",
        default="../data/interim/03_emisiones_rm_fusionadas",
        help="Directorio con los CSV a normalizar",
    )
    parser.add_argument(
        "--outdir",
        default="../data/interim/03_emisiones_rm_fusionadas",
        help="Directorio de salida (puede ser el mismo)",
    )
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    missing: Set[str] = set()

    for csv_path in sorted(indir.glob('retc*_RM.csv')):
        df = pd.read_csv(csv_path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip')
        df.columns = [c.lstrip('\ufeff') for c in df.columns]
        if 'comuna' not in df.columns:
            print(f"[!] {csv_path.name} no contiene columna 'comuna', se omite")
            continue

        normalized = []
        for val in df['comuna']:
            norm = normalize(val)
            if norm in NA_VALUES or norm == "":
                normalized.append(val)
                continue
            canon = CANON_COMUNAS.get(norm)
            if canon is None:
                missing.add(val if pd.notna(val) else "")
                normalized.append(val)
            else:
                normalized.append(canon)

        df['comuna'] = normalized
        out_path = outdir / csv_path.name
        df.to_csv(out_path, index=False, sep=';', encoding='utf-8-sig', quoting=csv.QUOTE_NONE, escapechar='\\')
        print(f"[✓] Comunas normalizadas en {csv_path.name}")

    if missing:
        print("[!] Comunas no reconocidas, revisar manualmente:")
        for val in sorted(missing):
            print(f" - {val}")
    else:
        print("[✓] Todas las comunas fueron normalizadas correctamente")


if __name__ == '__main__':
    main()
