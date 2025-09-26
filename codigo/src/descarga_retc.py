#!/usr/bin/env python3
"""Descarga todos los archivos publicados en la ficha RETC (EFP/RUEA).

Por defecto guarda los CSV/XLS/XLSX en `data/raw/descargas_retc/` dentro del repo.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup

DEFAULT_URL = "https://datosretc.mma.gob.cl/dataset/emisiones-al-aire-de-fuente-puntuales"


def resolve_outdir(base: Path | None) -> Path:
    if base is not None:
        return base
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "data" / "raw" / "descargas_retc"


def discover_links(url: str) -> Iterable[str]:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href.lower().endswith((".csv", ".xls", ".xlsx")):
            continue
        if href.startswith("/"):
            href = "https://datosretc.mma.gob.cl" + href
        links.append(href)
    return links


def download_all(links: Iterable[str], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for link in links:
        target = outdir / Path(link).name
        print(f"  → Descargando {target.name}")
        resp = requests.get(link, stream=True, timeout=60)
        resp.raise_for_status()
        with target.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description="Descargar archivos RETC EFP/RUEA")
    parser.add_argument("--url", default=DEFAULT_URL, help="URL del dataset RETC a recorrer")
    parser.add_argument(
        "--out",
        dest="outdir",
        default=None,
        help="Carpeta de destino (por defecto data/raw/descargas_retc)",
    )
    args = parser.parse_args()

    outdir = resolve_outdir(Path(args.outdir).expanduser().resolve() if args.outdir else None)

    print(f"[+] Obteniendo listado de archivos desde {args.url}")
    links = list(discover_links(args.url))
    print(f"[+] Encontrados {len(links)} archivos candidatos")
    if not links:
        return

    download_all(links, outdir)
    print(f"[✓] Descarga finalizada. Archivos en: {outdir}")


if __name__ == "__main__":
    main()
