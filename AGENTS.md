# Lineamientos del Repositorio

## Objetivo y Alcance
- Analizar brechas temporales y espaciales de emisiones RETC para la Región Metropolitana, cruzándolas con las Unidades del Paisaje.
- Garantizar reproducibilidad: cada resultado debe reconstruirse desde datos descargados y scripts versionados.

## Estructura del Proyecto
```
RetC/
├── codigo/src/                 # scripts del pipeline principal
├── notebooks/
│   ├── 00_exploracion/
│   ├── 10_transformaciones/
│   └── 20_geoespacial/         # cruces emisiones ↔ paisaje
├── data/
│   ├── raw/                    # descargas originales (gitignored)
│   ├── interim/                # intermedios limpios (gitignored)
│   └── processed/              # tablas ligeras publicables
├── geo/
│   ├── insumos/                # shapes originales (gitignored)
│   ├── processed/              # reproyecciones/limpiezas (gitignored)
│   └── public/                 # extractos livianos para GitHub
├── outputs/
│   ├── tablas/
│   │   └── publicados/
│   ├── graficos/
│   │   └── publicados/
│   └── mapas/                  # `LBP_AIRE_<DATETIME>_<descripcion>`
├── metadata/                   # fichas ISO 19115/19115-2, diccionarios
└── docs/
    └── metodologias/           # plantillas y guías (brechas, homologación)
```

## Comandos Clave
- Preparar entorno: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Descargar datos: `python codigo/src/descarga_retc.py` (usa `--out` solo si necesitas otra carpeta).
- Normalizar RAW por año: `python codigo/src/convertir_raw_a_csv_por_ano.py --indir ../data/raw/descargas_retc --outdir ../data/interim/01_emisiones_por_ano`.
- Filtrar RM: `python codigo/src/filtrar_region_metropolitana.py --indir ../data/interim/01_emisiones_por_ano --outdir ../data/interim/02_emisiones_por_ano_rm`.
- Fusionar por tramos: `python codigo/src/fusionar_emisiones_por_grupo.py --indir ../data/interim/02_emisiones_por_ano_rm --outdir ../data/interim/03_emisiones_rm_fusionadas`.
- Estandarizar contaminantes: `python codigo/src/estandarizar_contaminantes_rm.py --indir ../data/interim/03_emisiones_rm_fusionadas --outdir ../data/interim/03_emisiones_rm_fusionadas`.
- Estandarizar actividad económica: `python codigo/src/estandarizar_ciiu_rm.py --indir ../data/interim/03_emisiones_rm_fusionadas --outdir ../data/interim/03_emisiones_rm_fusionadas`.
- Homologar emisiones totales: `python codigo/src/agregar_emision_total_rm.py --indir ../data/interim/03_emisiones_rm_fusionadas`.
- Graficar: `python codigo/src/graficar_emisiones_por_grupo.py --in ../outputs/tablas/datos_resumidos/LBP_AIRE_<DATETIME>_emisiones_por_anio_y_grupo_pivot.csv --outdir ../outputs/graficos`.
- Reconstruir variables (fusionar columnas duplicadas): `python codigo/src/reconstruir_emisiones_por_variable.py --indir ../data/interim/emisiones_por_variable --outdir ../data/interim/emisiones_por_variable_fusionadas`.
- Graficar emisiones totales por contaminante: `python codigo/src/graficar_totales_por_variable.py --indir ../data/interim/emisiones_por_variable_fusionadas --outdir ../outputs/graficos/emisiones_totales`.
- Exportar extractos de columnas clave: `python codigo/src/exportar_extractos_por_variable.py --indir ../data/interim/emisiones_por_variable_fusionadas --outdir ../data/interim/emisiones_por_variable_extractos`.
- Al preparar informes, apóyate en `docs/metodologias/plantilla_analisis_brechas.md` y `docs/metodologias/homologacion_terminos_formatos.md` para mantener consistencia.

## Estilo de Código y Notebooks
- Python 3.8+, indentación de 4 espacios, PEP 8 (`snake_case`, `CamelCase`, constantes en mayúsculas). Usa `pathlib.Path` y encapsula CLI en `main()`.
- Notebooks con prefijo numérico; limpia salidas pesadas antes de versionar.

## Flujo Geoespacial
- CRS oficial: `EPSG:4326 (WGS84)`; documenta cualquier reproyección en `geo/processed/`.
- Resguarda insumos QGIS (`*.qgz`, `*.shp`, `*.gpkg`) en `geo/insumos/`; publica derivados livianos (`GeoJSON`, `GPKG` filtrados) en `geo/public/`.
- Documenta cada capa con ficha ISO (título, alcance, CRS, linaje, fecha) bajo `metadata/iso19115/`.
- Exporta resultados espaciales con prefijo `LBP_AIRE_<DATETIME>_` y README con comandos de generación.

## Pruebas y Validación
- Agrega `pytest` para helpers reutilizables usando CSV/GeoJSON de muestra.
- Tras cada corrida compara salidas con `wc -l`, `head`, `geopandas.GeoDataFrame.plot()` y totales frente a `outputs/tablas/`.

## Commits y Pull Requests
- Commits en presente y de alcance acotado (`filtrado: normaliza CRS a EPSG:4326`).
- PRs deben detallar scripts/notebooks tocados, comandos de reproducción, artefactos regenerados y dependencias nuevas.
