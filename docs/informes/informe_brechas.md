# Informe de Brechas — Emisiones RETC Región Metropolitana

## 4.1 Aire — Contexto General
- **Periodo analizado:** 2005–2023 (según cobertura disponible en `data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv`).
- **Fuentes de datos:** descargas oficiales RETC (MMA) procesadas mediante los scripts documentados en `README.md`/`AGENTS.md`.
- **Scripts ejecutados (principal):** `convertir_raw_a_csv_por_ano.py`, `filtrar_region_metropolitana.py`, `fusionar_emisiones_por_grupo.py`, `estandarizar_contaminantes_rm.py`, `estandarizar_ciiu_rm.py`, `agregar_emision_total_rm.py`, `agregar_id_unico_rm.py`, `completar_coordenadas_con_centros.py`, `asignar_unidad_paisaje_rm.py`, `fusionar_emisiones_consolidadas.py`.
- **Tablas y gráficos derivados:**
  - Tabla consolidada: `data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv`.
  - Totales anuales por contaminante: `outputs/tablas/datos_resumidos/LBP_AIRE_20250926_totales_por_contaminante.csv`.
  - Distribuciones: `outputs/graficos/emisiones_distribucion/`.
  - Emisiones 2023 por unidad de paisaje: `outputs/tablas/datos_resumidos/LBP_AIRE_20250926_emisiones_por_paisaje_2023.csv` y `outputs/graficos/emisiones_totales_por_paisaje/2023/`.

## 4.1.1 Meteorológicas y Climáticas

> *Nota:* A completar con conjuntos meteorológicos disponibles (temperatura, humedad relativa, precipitación, radiación, viento, presión). Mantener la siguiente estructura por variable.

### 4.1.1.1 Variable(s) Tipo #1 — *Nombre de la variable*
**Análisis de brechas en la variable**  
- Unidad Alta Cordillera: _[resumen cuantitativo/cualitativo + referencia a tabla/gráfico]_  
- Unidad Precordillera: _[...]_  
- Unidad Valle Central Agrícola: _[...]_  
- Unidad Valle Central Espinales: _[...]_  
- Unidad Cordillera de la Costa Sur: _[...]_  
- Unidad Cordillera de la Costa Norte: _[...]_  
- Unidad Áreas Urbanas: _[...]_

**Análisis de brechas espaciales**  
- Comparar la distribución espacial usando `unidad_paisaje` y la figura correspondiente. Resaltar unidades con valores extremos.

**Análisis de brechas temporales**  
- Revisar tendencia anual (`log`/gráficos temporales). Indicar años con máximos o mínimos relevantes.

### 4.1.1.2 Variable(s) Tipo #2 — *Nombre de la variable*
_Repetir la estructura anterior._

### …
### 4.1.1.N Variable(s) Tipo #N — *Nombre de la variable*
_Repetir la estructura anterior._

## 4.1.2 Calidad del Aire

> Enfocado en contaminantes medidos por la red SINCA: PM10, PM2.5, SO₂, NOx, CO, O₃ (si aplica). Usar totales anuales y distribución por unidad de paisaje.

### 4.1.2.1 PM10 — Emisiones totales
**Análisis de brechas en la variable**  
- Unidad Alta Cordillera: _[resumen con apoyo en `outputs/graficos/emisiones_totales_por_paisaje/2023/PM10_2023_paisaje.png` y tabla de totales]_  
- Unidad Precordillera: _[...]_  
- Unidad Valle Central Agrícola: _[...]_  
- Unidad Valle Central Espinales: _[...]_  
- Unidad Cordillera de la Costa Sur: _[...]_  
- Unidad Cordillera de la Costa Norte: _[...]_  
- Unidad Áreas Urbanas: _[...]_

**Análisis de brechas espaciales**  
- Comparar unidades de paisaje destacando las tres con mayores emisiones promedio en 2023.  
- Describir posibles fuentes (`actividad_macro`) asociadas.

**Análisis de brechas temporales**  
- Tendencia 2005–2023 (usar `outputs/graficos/emisiones_totales_acumuladas/contaminantes_por_anio/PM10.png`).  
- Identificar años con incrementos significativos y relacionarlos con cambios en actividades (p.ej. aumento en `MANUFACTURING`).

### 4.1.2.2 PM2.5 — Emisiones totales
_Repetir la estructura anterior apoyándose en los gráficos específicos._

### 4.1.2.3 SO₂ — Emisiones totales
_Repetir la estructura anterior. Incluir análisis de fuentes `ENERGY` y `MANUFACTURING`._

### 4.1.2.4 NOx — Emisiones totales
_Repetir la estructura anterior. Correlacionar con `TRANSPORT` y `ENERGY`._

### 4.1.2.5 Otros contaminantes SINCA (si aplica)
- CO, O₃ u otros, siguiendo el mismo esquema.

## 4.2 Síntesis y Recomendaciones
- **Principales hallazgos:** _[destacar los contaminantes/unidades más críticos, tendencias temporales mayores]_  
- **Vacíos de información:** _[listar variables sin datos confiables, provincias sin cobertura]_  
- **Recomendaciones:**
  - Mejorar monitoreo en unidades de paisaje con altos incrementos.  
  - Integrar series meteorológicas oficiales (DMC) para validar correlaciones clima-emisión.  
  - Consolidar reportes de PM₂․₅ y SO₂ en la red SINCA con parámetros de actividad (`actividad_macro`).

## Referencias y Anexos
- Tablas clave (`retc_RM_consolidado.csv`, `LBP_AIRE_20250926_emisiones_por_paisaje_2023.csv`).
- Gráficos (`outputs/graficos`).
- Glosarios (`metadata/diccionarios/`, `metadata/ciiu_glosario.md`).
- Scripts reproducibles (`README.md` / `AGENTS.md`).

> **Nota:** Mantener la coherencia con `docs/metodologias/homologacion_terminos_formatos.md` para estilos tipográficos, unidades, tablas y acrónimos.

## Gráficos 2023 por comuna y contaminante
- [ARSENIC](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/ARSENIC_comunas_2023.png)
- [BENZENE](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/BENZENE_comunas_2023.png)
- [BLACK_CARBON](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/BLACK_CARBON_comunas_2023.png)
- [CH4](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/CH4_comunas_2023.png)
- [CO2](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/CO2_comunas_2023.png)
- [CO](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/CO_comunas_2023.png)
- [HG](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/HG_comunas_2023.png)
- [N2O](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/N2O_comunas_2023.png)
- [NH3](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/NH3_comunas_2023.png)
- [NOX](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/NOX_comunas_2023.png)
- [PB](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/PB_comunas_2023.png)
- [PCDD_F](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/PCDD_F_comunas_2023.png)
- [PM10](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/PM10_comunas_2023.png)
- [PM2_5](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/PM2_5_comunas_2023.png)
- [PM_PRIMARY](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/PM_PRIMARY_comunas_2023.png)
- [SO2](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/SO2_comunas_2023.png)
- [SOX](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/SOX_comunas_2023.png)
- [TOLUENE](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/TOLUENE_comunas_2023.png)
- [VOC](https://github.com/cpatagon/retc-rm/blob/master/outputs/graficos/emisiones_acumuladas_2023/VOC_comunas_2023.png)
