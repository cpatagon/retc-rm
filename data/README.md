# Datos

Esta carpeta agrupa los insumos tabulares utilizados en el pipeline.

- `raw/`: descargas originales desde el RETC u otras fuentes. Se recrean con `codigo/src/descarga_retc.py` u otros scripts; no se versionan.
- `interim/`: resultados intermedios luego de filtrados o limpiezas. Deben poder regenerarse a partir de `raw/`.
  - `emisiones_por_variable/`: tablas fusionadas por contaminante (output de `reconstruir_emisiones_por_variable.py`).
  - `emisiones_por_variable_fusionadas/`: versión consolidada con columnas unificadas.
  - `emisiones_por_variable_extractos/`: extractos con columnas clave (`exportar_extractos_por_variable.py`).
- `processed/`: tablas livianas listas para análisis o visualización. Versiona únicamente los archivos pequeños acompañados de su comando de generación.

Incluye un README o notebook de soporte cuando se agreguen nuevas subcarpetas o procesos.
