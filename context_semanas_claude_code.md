# Contexto para Claude Code — Feature: Segmentación por Semana
## Proyecto: Calculadora de Capacidad Sanoviv
## Fecha: Marzo 2026

---

## 1. QUÉ HAY QUE HACER

Actualmente la calculadora trabaja con un **consumo semanal promedio** para toda la duración del programa. El objetivo es reemplazar eso por un **consumo diferenciado por semana**, de modo que al ingresar pacientes el usuario pueda especificar en **qué semana de su estancia** están (semana 1, semana 2, etc.), y el cálculo de recursos refleje el consumo real de esa semana.

### División de trabajo en este contexto
- **Este documento cubre**: cambios en `BD_sanoviv.py` y `optimizador_v2.py`
- `app.py` se aborda en un contexto separado

---

## 2. STACK Y ARCHIVOS

| Archivo | Rol |
|---|---|
| `BD_sanoviv.py` | Fuente única de verdad — datos de programas, actividades, recursos |
| `optimizador_v2.py` | Motor ILP — `construir_modelo_datos()`, `ejecutar_optimizacion()`, `verificar_admision()` |
| `app.py` | UI Streamlit — no tocar en este contexto |

Dependencias: `pulp` (ILP con CBC), `pandas`, `streamlit`

---

## 3. CAMBIO EN BD_sanoviv.py

### 3.1 Nueva estructura de actividades

Hoy cada actividad en un programa tiene:
```python
{
    "nombre":       "Medical Follow-up Consultation",
    "tipo":         "Consulta",
    "cantidad":     12,          # total por estancia completa
    "duracion_min": 30,
    "recursos_prof": ["Doctor", "Nurse"],
    "recurso_fis":  "Doctor Office",
}
```

Debe cambiar a:
```python
{
    "nombre":       "Medical Follow-up Consultation",
    "tipo":         "Consulta",
    "cantidad":     12,          # total por estancia — se mantiene para compatibilidad
    "duracion_min": 30,
    "recursos_prof": ["Doctor", "Nurse"],
    "recurso_fis":  "Doctor Office",
    "cantidad_por_semana": [4, 5, 3],   # NUEVO — suma debe coincidir con "cantidad"
}
```

### 3.2 Regla de `cantidad_por_semana`

- Es una **lista de enteros**, una entrada por semana del programa.
- `len(cantidad_por_semana)` debe ser **siempre igual** a `duracion_dias // 7`. La función `validar_cantidades_por_semana()` valida esto sin excepciones.
- La suma de los valores debe ser igual a `cantidad`.
- Para **programas de 1 semana** (7 días o menos): `[cantidad]` — lista de un solo elemento.
- Para **extensiones**: todas duran 1 semana → `[cantidad]`.
- El campo `cantidad` original **se mantiene** sin cambios (necesario para compatibilidad con partes de app.py que aún no se migran).

**Regla para actividades NO listadas en las tablas de distribución** (consultas iniciales, estudios de admisión, EKG, Lab, X-Ray, etc. — actividades que ocurren una sola vez al inicio):
- Programas de 2 semanas → `[cantidad, 0]`
- Programas de 3 semanas → `[cantidad, 0, 0]`

**IMPORTANTE**: las **consultas de egreso** (Discharge Consultations de todas las disciplinas) **sí están listadas en las tablas** con su distribución correcta — siempre con 0 en semanas anteriores y la cantidad en la última semana (ej. `[0, 1]` o `[0, 0, 1]`). No son "actividades no listadas". Usar exactamente los valores de las tablas para ellas.

### 3.3 Programas y sus distribuciones por semana

A continuación el mapa completo validado. Para cada actividad se indica `[sem1, sem2, sem3]`.  
**Regla**: si una actividad no aparece en la lista de un programa, mantener su `cantidad_por_semana` como `[cantidad]` (todo en semana 1, ya que Bedroom/Dining y actividades únicas no requieren distribución especial).

---

#### CANCER TREATMENT (21 días → 3 semanas)

Nota: `Subclavian Catheter Placement` ya está listado en la tabla con `[1, 0, 0]`.

| Actividad | cantidad | cantidad_por_semana |
|---|---|---|
| Medical Follow-up Consultation | 12 | [4, 5, 3] |
| Nutrition Follow-up Consultation | 7 | [2, 3, 2] |
| Nutrition Discharge Consultation | 1 | [0, 0, 1] |
| Chiropractic Follow-up Consultation | 3 | [1, 1, 1] |
| Chiropractic Discharge Consultation | 1 | [0, 0, 1] |
| Psychology Follow-up Consultation | 7 | [2, 3, 2] |
| Psychology Discharge Consultation | 1 | [0, 0, 1] |
| Mind-Body Follow-up Consultation | 6 | [1, 3, 2] |
| Mind-Body Discharge Consultation | 1 | [0, 0, 1] |
| Individual Fitness Session | 4 | [1, 2, 1] |
| Fitness Discharge Consultation | 1 | [0, 0, 1] |
| Medical Discharge Consultation | 1 | [0, 0, 1] |
| Bioelectrical Bioimpedance | 2 | [1, 0, 1] |
| Chest X-Ray PA and Lateral | 2 | [1, 0, 1] |
| Computed Tomography (CT) | 1 | [0, 0, 1] |
| IV: Amygdalin | 6 | [2, 2, 2] |
| IV: Artesunate (240 mg) | 3 | [1, 1, 1] |
| IV: Vitamin C - 25 grams | 1 | [1, 0, 0] |
| IV: Vitamin C - 50 grams | 1 | [0, 1, 0] |
| IV: Vitamin C - 75 grams | 4 | [0, 1, 3] |
| IV: Chelation | 3 | [1, 1, 1] |
| IV: Macrophage Activating Protein Therapy | 9 | [3, 3, 3] |
| Regional Hyperthermia | 9 | [3, 3, 3] |
| Full Body Hyperthermia | 6 | [2, 2, 2] |
| Hyperbaric Oxygen | 12 | [4, 4, 4] |
| Colon Hydrotherapy | 6 | [2, 2, 2] |
| Quiet Room 60 min | 18 | [6, 6, 6] |
| Medical SPA Session 30 min | 2 | [0, 1, 1] |
| Medical SPA Session 60 min | 10 | [4, 3, 3] |
| Medical SPA Session 90 min | 1 | [0, 0, 1] |
| Laparoscopy Surgery | 1 | [0, 0, 1] |
| Subclavian Catheter Placement | 1 | [1, 0, 0] |
| Bedroom Use | 21 | [7, 7, 7] |
| Dining Area Use | 63 | [21, 21, 21] |
| — resto de actividades no listadas (Admission Consultation, Initial Medical Consultation, Initial Nutrition Consultation, Dental Initial Consultation, EKG, Lab Sample, Dental X-Ray, etc.) — | cantidad | [cantidad, 0, 0] |

---

#### LYME DISEASE & CO-INFECTIONS (14 días → 2 semanas)

| Actividad | cantidad | cantidad_por_semana |
|---|---|---|
| Medical Follow-up Consultation | 8 | [4, 4] |
| Nutrition Follow-up Consultation | 4 | [2, 2] |
| Nutrition Discharge Consultation | 1 | [0, 1] |
| Chiropractic Follow-up Consultation | 3 | [2, 1] |
| Chiropractic Discharge Consultation | 1 | [0, 1] |
| Psychology Follow-up Consultation | 4 | [3, 1] |
| Psychology Discharge Consultation | 1 | [0, 1] |
| Mind-Body Follow-up Consultation | 2 | [1, 1] |
| Mind-Body Discharge Consultation | 1 | [0, 1] |
| Individual Fitness Session | 1 | [1, 0] |
| Fitness Discharge Consultation | 1 | [0, 1] |
| Medical Discharge Consultation | 1 | [0, 1] |
| Dental Cleaning | 1 | [0, 1] |
| Ozone Autohemotherapy (60 min) | 4 | [2, 2] |
| Full Body Hyperthermia with Sedation | 2 | [1, 1] |
| IV: Alpha Lipoic Acid | 4 | [1, 3] |
| IV: Artesunate (240 mg) | 4 | [2, 2] |
| IV: Methylene Blue | 2 | [0, 2] |
| IV: Cellular Nutrition | 2 | [1, 1] |
| IV: Glutathione | 6 | [2, 4] |
| IV: Chelation | 2 | [1, 1] |
| IV: Electrolyte Solution | 2 | [1, 1] |
| IV: Superimmune | 4 | [2, 2] |
| Hyperbaric Oxygen | 4 | [2, 2] |
| Colon Hydrotherapy | 4 | [2, 2] |
| Quiet Room 60 min | 6 | [3, 3] |
| Medical SPA Session 60 min | 6 | [2, 4] |
| Bedroom Use | 14 | [7, 7] |
| Dining Area Use | 42 | [21, 21] |

---

#### DETOX AND REJUVENATION (7 días → 1 semana)
Todas las actividades: `cantidad_por_semana = [cantidad]`

---

#### STEM CELL REJUVENATION (7 días → 1 semana)
Todas las actividades: `cantidad_por_semana = [cantidad]`

---

#### NEUROFEEDBACK DETOX (7 días → 1 semana)
Todas las actividades: `cantidad_por_semana = [cantidad]`

---

#### MEDICAL TREATMENT (14 días → 2 semanas)

**IMPORTANTE**: este programa necesita además que se **agregue una nueva actividad** que no está actualmente en BD_sanoviv:

```python
{
    "nombre":        "Hyperbaric Oxygen",
    "tipo":          "Terapia",
    "cantidad":      10,
    "duracion_min":  60,          # mismo que otros programas que lo usan
    "recursos_prof": ["Hyperbaric Nurse"],   # verificar nombre exacto en catálogo
    "recurso_fis":   "Hyperbaric Chamber",   # verificar nombre exacto en catálogo
    "cantidad_por_semana": [5, 5],
}
```
→ Antes de insertar, verificar que `"Hyperbaric Oxygen"` ya existe en `catalogo_actividades` y copiar los campos `recursos_prof` y `recurso_fis` exactamente del catálogo.

Distribuciones del resto de actividades:

| Actividad | cantidad | cantidad_por_semana |
|---|---|---|
| Medical Follow-up Consultation | 7 | [4, 3] |
| Nutrition Follow-up Consultation | 4 | [1, 3] |
| Nutrition Discharge Consultation | 1 | [0, 1] |
| Chiropractic Follow-up Consultation | 4 | [1, 3] |
| Chiropractic Discharge Consultation | 1 | [0, 1] |
| Psychology Follow-up Consultation | 4 | [1, 3] |
| Psychology Discharge Consultation | 1 | [0, 1] |
| Mind-Body Follow-up Consultation | 3 | [1, 2] |
| Mind-Body Discharge Consultation | 1 | [0, 1] |
| Individual Fitness Session | 2 | [1, 1] |
| Fitness Discharge Consultation | 1 | [0, 1] |
| Medical Discharge Consultation | 1 | [0, 1] |
| Dental Follow-up Consultation | 1 | [0, 1] |
| Dental Cleaning | 1 | [0, 1] |
| Ozone Autohemotherapy (60 min) | 1 | [0, 1] |
| IV: Alpha Lipoic Acid | 6 | [3, 3] |
| IV: Glutathione | 6 | [2, 4] |
| IV: Mitochondrial Energy | 6 | [3, 3] |
| Hyperbaric Oxygen | 10 | [5, 5] |
| Colon Hydrotherapy | 4 | [2, 2] |
| Sauna Session 60 min | 12 | [5, 7] |
| Medical SPA Session 60 min | 4 | [2, 2] |
| Medical SPA Session 90 min | 2 | [1, 1] |
| Quiet Room 60 min | 6 | [2, 4] |
| Bedroom Use | 14 | [7, 7] |
| Dining Area Use | 42 | [21, 21] |

---

#### INTEGRATIVE PHYSICAL (4 días → 1 semana)
Todas las actividades: `cantidad_por_semana = [cantidad]`

---

#### LONG COVID TREATMENT (14 días → 2 semanas)

| Actividad | cantidad | cantidad_por_semana |
|---|---|---|
| Medical Follow-up Consultation | 8 | [4, 4] |
| Nutrition Follow-up Consultation | 4 | [1, 3] |
| Nutrition Discharge Consultation | 1 | [0, 1] |
| Chiropractic Follow-up Consultation | 3 | [0, 3] |
| Chiropractic Discharge Consultation | 1 | [0, 1] |
| Psychology Follow-up Consultation | 4 | [1, 3] |
| Psychology Discharge Consultation | 1 | [0, 1] |
| Mind-Body Follow-up Consultation | 2 | [0, 2] |
| Mind-Body Discharge Consultation | 1 | [0, 1] |
| Individual Fitness Session | 4 | [0, 4] |
| Fitness Discharge Consultation | 1 | [0, 1] |
| Medical Discharge Consultation | 1 | [0, 1] |
| Dental Cleaning | 1 | [0, 1] |
| Computed Tomography (CT) | 1 | [0, 1] |
| Specialist Interconsultation | 2 | [1, 1] |
| Minor Ozone Autohemotherapy | 4 | [0, 4] |
| Full Body Hyperthermia | 2 | [0, 2] |
| IV: Methylene Blue | 2 | [0, 2] |
| IV: Mitochondrial Energy | 2 | [0, 2] |
| Protocol PC 1, 2, 3 | 10 | [1, 9] |
| Hyperbaric Oxygen | 9 | [4, 5] |
| Colon Hydrotherapy | 3 | [0, 3] |
| Quiet Room 30 min | 6 | [0, 6] |
| Quiet Room 60 min | 4 | [1, 3] |
| Medical SPA Session 60 min | 6 | [1, 5] |
| Medical SPA Session 90 min | 2 | [1, 1] |
| Bedroom Use | 14 | [7, 7] |
| Dining Area Use | 42 | [21, 21] |

---

#### NEURO COGNITIVE (14 días → 2 semanas)

**IMPORTANTE**: este programa necesita que se **agregue una nueva actividad** que no está actualmente en BD_sanoviv:

```python
{
    "nombre":        "Subclavian Catheter Placement",
    "tipo":          "Terapia",
    "cantidad":      1,
    "duracion_min":  30,          # copiar del catálogo
    "recursos_prof": [...],       # copiar exactamente del catálogo
    "recurso_fis":   "...",       # copiar exactamente del catálogo
    "cantidad_por_semana": [1, 0],
}
```
→ El nombre `"Subclavian Catheter Placement"` ya existe en otros programas y en el catálogo. Copiar sus campos exactamente.

Distribuciones del resto:

| Actividad | cantidad | cantidad_por_semana |
|---|---|---|
| Medical Follow-up Consultation | 8 | [4, 4] |
| Nutrition Follow-up Consultation | 3 | [1, 2] |
| Nutrition Discharge Consultation | 1 | [0, 1] |
| Chiropractic Follow-up Consultation | 3 | [1, 2] |
| Chiropractic Discharge Consultation | 1 | [0, 1] |
| Psychology Follow-up Consultation | 4 | [1, 3] |
| Psychology Discharge Consultation | 1 | [0, 1] |
| Mind-Body Follow-up Consultation | 2 | [1, 1] |
| Mind-Body Discharge Consultation | 1 | [0, 1] |
| Individual Fitness Session | 4 | [1, 3] |
| Fitness Discharge Consultation | 1 | [0, 1] |
| Medical Discharge Consultation | 1 | [0, 1] |
| Dental Cleaning | 1 | [0, 1] |
| Specialist Interconsultation | 1 | [0, 1] |
| Subclavian Catheter Placement | 1 | [1, 0] |
| Carsilaza | 2 | [1, 1] |
| Minor Ozone Autohemotherapy | 4 | [1, 3] |
| Full Body Hyperthermia | 2 | [1, 1] |
| IV: Methylene Blue | 2 | [1, 1] |
| IV: Cellular Nutrition | 2 | [1, 1] |
| IV: Stem Cells (up to 120 million) | 1 | [0, 1] |
| Protocol PC 1, 2, 3 | 10 | [4, 6] |
| Assisted Neurofeedback (30 min) | 20 | [10, 10] |
| Hyperbaric Oxygen | 10 | [3, 7] |
| Colon Hydrotherapy | 3 | [1, 2] |
| Sauna Session 60 min | 10 | [5, 5] |
| Quiet Room 60 min | 6 | [2, 4] |
| Medical SPA Session 60 min | 6 | [3, 3] |
| Medical SPA Session 90 min | 2 | [1, 1] |
| Bedroom Use | 14 | [7, 7] |
| Dining Area Use | 42 | [21, 21] |

---

#### MYCOTOXIN DETOX (14 días → 2 semanas)

| Actividad | cantidad | cantidad_por_semana |
|---|---|---|
| Medical Follow-up Consultation | 6 | [4, 2] |
| Nutrition Follow-up Consultation | 2 | [1, 1] |
| Nutrition Discharge Consultation | 1 | [0, 1] |
| Chiropractic Follow-up Consultation | 2 | [1, 1] |
| Chiropractic Discharge Consultation | 1 | [0, 1] |
| Psychology Follow-up Consultation | 3 | [2, 1] |
| Psychology Discharge Consultation | 1 | [0, 1] |
| Mind-Body Follow-up Consultation | 2 | [1, 1] |
| Mind-Body Discharge Consultation | 1 | [0, 1] |
| Individual Fitness Session | 2 | [1, 1] |
| Fitness Discharge Consultation | 1 | [0, 1] |
| Medical Discharge Consultation | 1 | [0, 1] |
| Dental Cleaning | 1 | [0, 1] |
| Neural Therapy | 2 | [1, 1] |
| Full Body Hyperthermia | 2 | [1, 1] |
| IV: Methylene Blue | 2 | [1, 1] |
| IV: Glutathione | 2 | [0, 2] |
| IV: Chelation | 2 | [0, 2] |
| Protocol PC 1, 2, 3 | 8 | [4, 4] |
| Hyperbaric Oxygen | 6 | [2, 4] |
| Colon Hydrotherapy | 2 | [1, 1] |
| Sauna Session 60 min | 10 | [5, 5] |
| Medical SPA Session 30 min | 1 | [1, 0] |
| Medical SPA Session 60 min | 8 | [4, 4] |
| Medical SPA Session 90 min | 2 | [1, 1] |
| Quiet Room 60 min | 6 | [2, 4] |
| Bedroom Use | 14 | [7, 7] |
| Dining Area Use | 42 | [21, 21] |

---

#### MICROBIOME RESTORE (5 días → 1 semana)
Todas las actividades: `cantidad_por_semana = [cantidad]`

---

#### EXTENSIONES (todas → 1 semana)
Todas las extensiones: `cantidad_por_semana = [cantidad]` en cada actividad.

---

### 3.4 Validación en BD_sanoviv.py

Después de todos los cambios, agregar al final del archivo una función de validación:

```python
def validar_cantidades_por_semana():
    """Valida que cantidad_por_semana sea consistente con cantidad y duracion_dias."""
    errores = []
    for nombre, prog in programas.items():
        n_semanas_esperadas = prog["duracion_dias"] // 7
        for act in prog["actividades"]:
            cps = act.get("cantidad_por_semana", [act["cantidad"]])
            if sum(cps) != act["cantidad"]:
                errores.append(
                    f"{nombre} / {act['nombre']}: suma {sum(cps)} ≠ cantidad {act['cantidad']}"
                )
            if len(cps) != n_semanas_esperadas:
                errores.append(
                    f"{nombre} / {act['nombre']}: len {len(cps)} ≠ semanas esperadas {n_semanas_esperadas}"
                )
    if errores:
        raise ValueError("Errores en cantidad_por_semana:\n" + "\n".join(errores))
    return True
```

Llamar `validar_cantidades_por_semana()` al final del archivo para que se ejecute en cada importación.

---

## 4. CAMBIO EN optimizador_v2.py

### 4.1 Nueva función: `construir_modelo_datos_semana(semana)`

Crear una nueva función paralela a `construir_modelo_datos()` que recibe el número de semana (1-indexed) y calcula el consumo usando solo las actividades de esa semana:

```python
def construir_modelo_datos_semana(semana: int) -> dict:
    """Igual que construir_modelo_datos() pero usando cantidad_por_semana[semana-1].
    
    Args:
        semana: int — semana de la estancia (1, 2 o 3 según el programa)
    
    Returns:
        Mismo dict que construir_modelo_datos(), con consumo calculado
        usando solo las actividades correspondientes a esa semana.
    """
```

La lógica de cálculo de consumo cambia de:
```python
consumo_h = (cantidad * dur_min / 60.0) / semanas
```
a:
```python
cantidad_semana = act.get("cantidad_por_semana", [act["cantidad"]] * n_semanas)[semana - 1]
consumo_h = cantidad_semana * dur_min / 60.0  # ya es consumo de 1 semana, no promedio
```

**Nota crítica**: para programas cuya duración en semanas es menor que `semana`, el consumo debe ser 0 (el paciente ya no está en el hospital). Ejemplo: un paciente de Detox (7 días) no tiene consumo en semana 2.

```python
n_semanas_prog = prog["duracion_dias"] // 7
if semana > n_semanas_prog:
    # Este programa no tiene actividad en esta semana — consumo = 0
    continue
```

### 4.2 Mantener `construir_modelo_datos()` sin cambios

La función original **no se modifica**. Sigue siendo usada para la optimización global (tab "Executive Summary" y "Patients" en app.py), que sigue trabajando con promedios.

### 4.3 Nueva función: `verificar_admision_semana(pacientes_por_semana, solicitudes_semana)`

Crear una versión de `verificar_admision()` que recibe pacientes segmentados por semana:

```python
def verificar_admision_semana(
    pacientes_por_semana: dict[int, list[int]],
    solicitudes_semana: dict[int, dict[int, int]]
) -> dict:
    """Verifica admisión considerando qué semana está cada grupo de pacientes.

    Args:
        pacientes_por_semana: {semana: [pacientes por programa]}
            Ejemplo: {1: [3, 2, 0, ...], 2: [5, 1, 0, ...]}
        solicitudes_semana: {semana: {idx_programa: cantidad_solicitada}}
            Ejemplo: {1: {0: 2}, 2: {3: 1}}

    Returns:
        Mismo formato que verificar_admision() actual.
    """
```

Lógica interna:
1. Para cada semana presente en `pacientes_por_semana` o `solicitudes_semana`, llamar a `construir_modelo_datos_semana(semana)` para obtener la matriz de consumo de esa semana.
2. Calcular el uso total de recursos como la **suma de consumos de todas las semanas activas**.
3. Verificar si el total excede la capacidad semanal disponible.

### 4.4 Mantener `verificar_admision()` sin cambios

La función original sigue disponible para el flujo actual de app.py.

---

## 5. REGLAS DE IMPLEMENTACIÓN

1. **No romper compatibilidad hacia atrás**: `construir_modelo_datos()`, `ejecutar_optimizacion()` y `verificar_admision()` deben seguir funcionando exactamente igual que hoy. Las nuevas funciones son **adiciones**, no reemplazos.

2. **`cantidad` se mantiene en cada actividad**: no eliminar ni modificar el campo existente. `cantidad_por_semana` es un campo adicional.

3. **Actividades sin distribución explícita en las tablas**: para programas multi-semana, toda actividad debe tener `cantidad_por_semana` con longitud igual a `duracion_dias // 7`. Las actividades no listadas en las tablas (consultas iniciales, estudios únicos de admisión, EKG, Lab, etc.) van con toda su cantidad en semana 1: `[cantidad, 0]` o `[cantidad, 0, 0]`. Las **consultas de egreso** siempre están listadas explícitamente en las tablas — nunca asumir su distribución.

4. **Nombres de recursos**: no inventar nombres. Siempre copiar los valores de `recursos_prof` y `recurso_fis` exactamente del catálogo existente en `BD_sanoviv.py`.

5. **Validación automática**: la función `validar_cantidades_por_semana()` debe ejecutarse al importar `BD_sanoviv.py`. Si hay errores, debe lanzar `ValueError` descriptivo.

---

## 6. PRUEBA MÍNIMA DE SANITY CHECK

Después de los cambios, ejecutar este script para verificar que nada se rompió:

```python
import BD_sanoviv as datos
import optimizador_v2 as opt

# 1. Validación de estructura
datos.validar_cantidades_por_semana()
print("✓ Validación de cantidad_por_semana OK")

# 2. Modelo original sigue funcionando
md = opt.construir_modelo_datos()
assert len(md["nombres_programas"]) == 23
print(f"✓ construir_modelo_datos OK — {md['n_programas']} programas")

# 3. Modelo por semana
md1 = opt.construir_modelo_datos_semana(1)
md2 = opt.construir_modelo_datos_semana(2)
md3 = opt.construir_modelo_datos_semana(3)
print("✓ construir_modelo_datos_semana OK para semanas 1, 2, 3")

# 4. Cancer Treatment: verificar que consumo semana 1 ≠ semana 2 ≠ semana 3
idx_cancer = md1["nombres_programas"].index("Cancer Treatment")
c1 = md1["consumo"][0][idx_cancer]
c2 = md2["consumo"][0][idx_cancer]
c3 = md3["consumo"][0][idx_cancer]
assert c1 != c2 or c2 != c3, "Cancer debería tener consumo distinto por semana"
print(f"✓ Cancer semana 1/2/3 tienen consumos diferenciados: {c1:.4f} / {c2:.4f} / {c3:.4f}")

# 5. Detox (1 semana): semana 2 debe tener consumo 0
idx_detox = md2["nombres_programas"].index("Detox and Rejuvenation")
consumo_detox_s2 = sum(md2["consumo"][r][idx_detox] for r in range(md2["n_recursos"]))
assert consumo_detox_s2 == 0.0, "Detox no debería tener consumo en semana 2"
print("✓ Detox semana 2 = consumo 0 OK")

print("\n✅ Todos los checks pasaron")
```

---

## 7. LO QUE NO SE HACE EN ESTE CONTEXTO

- No modificar `app.py` — eso es un contexto separado.
- No cambiar la UI, tabs ni flujos existentes.
- No modificar `ejecutar_optimizacion()` — la optimización global sigue con promedios por ahora.
- No cambiar la estructura de `recursos_profesionales` ni `recursos_fisicos`.
