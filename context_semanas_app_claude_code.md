# Contexto para Claude Code — Feature: Segmentación por Semana (app.py)
## Proyecto: Calculadora de Capacidad Sanoviv
## Fecha: Marzo 2026
## PREREQUISITO: Aplicar primero `context_semanas_claude_code.md` (BD_sanoviv.py + optimizador_v2.py)

---

## 1. CONTEXTO GENERAL

Este documento cubre los cambios en `app.py`. Los cambios en `BD_sanoviv.py` y `optimizador_v2.py` ya fueron aplicados en el contexto anterior. Lo que ya existe después de ese contexto:

- Cada actividad en `BD_sanoviv.py` tiene el campo `cantidad_por_semana: list[int]`
- `optimizador_v2.py` tiene dos nuevas funciones:
  - `construir_modelo_datos_semana(semana: int)` — matriz de consumo solo para esa semana
  - `verificar_admision_semana(pacientes_por_semana, solicitudes_semana)` — verificación con pacientes segmentados por semana

---

## 2. ESTRUCTURA ACTUAL DE app.py (lo que NO cambia)

La app tiene 5 tabs (usuario admin) o 4 tabs (usuario normal):
- **tab1 — Executive Summary**: resumen y resultados de optimización
- **tab2 — Patients**: tabla editable de pacientes actuales por programa → botón "Calculate Optimization"
- **tab3 — Resources**: visualización de uso de recursos
- **tab4 — Verify Admission**: verificar si se puede admitir X pacientes de cierto programa
- **tab5 — Administration**: solo admin, edición de recursos y programas

**Estado relevante en `st.session_state`:**
```python
st.session_state.pacientes_actuales  # list[int] — pacientes por programa (orden = nombres_programas)
st.session_state.solicitudes_admision  # dict[int, int] — {idx_programa: cantidad}
st.session_state.resultado_verificacion  # dict — resultado de verificar_admision()
st.session_state.resultados  # dict — resultado de ejecutar_optimizacion()
```

---

## 3. QUÉ CAMBIA Y DÓNDE

### 3.1 tab2 — Patients: agregar columna "Week"

**Cambio**: la tabla editable de pacientes base necesita una nueva columna `"Week"` donde el usuario indica en qué semana de su estancia están los pacientes de ese programa.

**Lógica de la columna Week:**
- Para programas de **1 semana** (duracion_dias ≤ 7): la columna muestra `1` y está **deshabilitada** (no tiene sentido elegir semana).
- Para programas de **2 semanas** (duracion_dias = 14): dropdown con opciones `[1, 2]`.
- Para programas de **3 semanas** (duracion_dias = 21): dropdown con opciones `[1, 2, 3]`.

**Nota sobre extensiones**: las extensiones siempre son 1 semana → columna Week = 1, deshabilitada.

**Nuevo estado en session_state:**
```python
st.session_state.semana_pacientes  # dict[int, int] — {idx_programa: semana_actual (1-indexed)}
```
Inicializar con semana 1 para todos los programas.

**Implementación sugerida con `st.data_editor`:**
```python
# Determinar max semanas por programa
max_semanas = datos_base["duracion_dias"][nombre] // 7

df_base = pd.DataFrame({
    "Program": [...],
    "Current Patients": [...],
    "Week": [st.session_state.semana_pacientes.get(i, 1) for i in indices_base],
    "Priority": [...],
})

# En column_config:
"Week": st.column_config.SelectboxColumn(
    "Week",
    options=[1, 2, 3],   # siempre mostrar hasta 3, pero filtrar por programa al leer
    help="Week of stay the patients are currently in",
    required=True,
),
```

Al leer el valor editado, validar que la semana seleccionada no exceda `duracion_dias // 7` del programa. Si excede, resetear a 1.

**Sync al session_state:**
```python
st.session_state.semana_pacientes[global_idx] = semana_validada
```

---

### 3.2 tab2 — Patients: cambiar llamada a `ejecutar_optimizacion`

**Cambio**: `ejecutar_optimizacion` **no cambia** — sigue recibiendo `pacientes_actuales` como lista plana. La optimización global sigue trabajando con promedios. No hay cambio aquí.

---

### 3.3 tab4 — Verify Admission: agregar selector de semana por solicitud

**Cambio central**: cuando el usuario agrega una solicitud de admisión, ahora debe especificar **en qué semana del programa van a estar** los pacientes solicitados.

**UI actual** (formulario de solicitud):
```
[Selector programa]  [Número de pacientes]  [➕ Add]
```

**UI nueva**:
```
[Selector programa]  [Número de pacientes]  [Semana]  [➕ Add]
```

El selector de semana:
- Mostrar solo si el programa tiene más de 1 semana.
- Si el programa tiene 1 semana, mostrar `Week 1` deshabilitado o simplemente no mostrarlo.
- Opciones dinámicas según `duracion_dias // 7` del programa seleccionado.

**Nuevo estado para solicitudes:**
```python
# Antes:
st.session_state.solicitudes_admision  # dict[int, int] — {idx_prog: cantidad}

# Después: extender para incluir semana
st.session_state.solicitudes_admision  # dict[int, dict] — {idx_prog: {"cantidad": int, "semana": int}}
```

**IMPORTANTE — compatibilidad**: cambiar la estructura de `solicitudes_admision` afecta el código que la lee. Actualizar todos los lugares donde se usa:
1. El `st.dataframe` que muestra las solicitudes pendientes → agregar columna "Week"
2. La llamada a `verificar_admision()` → reemplazar por `verificar_admision_semana()`

---

### 3.4 tab4 — Verify Admission: cambiar llamada a `verificar_admision_semana`

**Cambio**: reemplazar la llamada actual:
```python
# ANTES:
resultado_verificacion = verificar_admision(
    st.session_state.pacientes_actuales,
    st.session_state.solicitudes_admision,   # dict[int, int]
)
```

Por la nueva:
```python
# DESPUÉS:
from optimizador_v2 import verificar_admision_semana

# Construir pacientes_por_semana desde session_state
pacientes_por_semana = {}
for idx_prog, n_pac in enumerate(st.session_state.pacientes_actuales):
    if n_pac > 0:
        semana = st.session_state.semana_pacientes.get(idx_prog, 1)
        if semana not in pacientes_por_semana:
            pacientes_por_semana[semana] = [0] * len(st.session_state.pacientes_actuales)
        pacientes_por_semana[semana][idx_prog] = n_pac

# Construir solicitudes_semana desde solicitudes_admision
solicitudes_semana = {}
for idx_prog, sol in st.session_state.solicitudes_admision.items():
    semana = sol["semana"]
    if semana not in solicitudes_semana:
        solicitudes_semana[semana] = {}
    solicitudes_semana[semana][idx_prog] = sol["cantidad"]

resultado_verificacion = verificar_admision_semana(
    pacientes_por_semana,
    solicitudes_semana,
)
```

---

### 3.5 tab4 — Verify Admission: mostrar semana en resultados

En la sección "Pending Requests to Verify" y "Detail by Program", agregar la columna "Week" al dataframe para que el usuario vea en qué semana está cada solicitud.

```python
# DataFrame de solicitudes pendientes — agregar columna Week
solicitudes_df = pd.DataFrame([
    {
        "Program": datos_base["nombre_programas"][idx],
        "Week": sol["semana"],
        "Requested Patients": sol["cantidad"],
    }
    for idx, sol in st.session_state.solicitudes_admision.items()
])
```

---

### 3.6 tab2 — Patients: mostrar semana en Executive Summary (tab1)

En `tab1`, la tabla "Patients by Program" actualmente muestra:
```
Program | Current | Additional | Total
```

Agregar columna "Week":
```
Program | Week | Current | Additional | Total
```

Usando `st.session_state.semana_pacientes`.

---

## 4. IMPORT A AGREGAR

En la línea 12 de `app.py`, agregar `verificar_admision_semana` al import:

```python
# ANTES:
from optimizador_v2 import obtener_datos_base, ejecutar_optimizacion, verificar_admision

# DESPUÉS:
from optimizador_v2 import obtener_datos_base, ejecutar_optimizacion, verificar_admision, verificar_admision_semana
```

---

## 5. INICIALIZACIÓN DE NUEVOS ESTADOS

Junto al bloque existente que inicializa `pacientes_actuales` (~línea 575), agregar:

```python
# Semana actual por programa (1-indexed)
if "semana_pacientes" not in st.session_state:
    st.session_state.semana_pacientes = {
        i: 1 for i in range(len(datos_base["nombre_programas"]))
    }

# Reset semana al limpiar pacientes
# (en el bloque "if limpiar:", añadir:)
st.session_state.semana_pacientes = {
    i: 1 for i in range(len(datos_base["nombre_programas"]))
}
```

---

## 6. HELPER: duracion_dias por programa

Para saber cuántas semanas tiene un programa al construir los selectores, usar:

```python
# Ya disponible en datos_base:
datos_base["duraciones_dias"]  # dict[str, int] — nombre_programa → dias

# Para obtener n_semanas de un programa por índice:
nombre = datos_base["nombre_programas"][idx]
n_semanas = datos_base["duraciones_dias"][nombre] // 7
```

---

## 7. REGLAS DE IMPLEMENTACIÓN

1. **No tocar tab3, tab5, ni ninguna lógica de recursos** — no cambian.
2. **No modificar `ejecutar_optimizacion()`** — la optimización global sigue con promedios.
3. **Mantener `verificar_admision()` disponible** — no eliminar el import aunque ya no se use directamente, por si hay otros usos.
4. **Extensiones en tab2**: la columna Week para extensiones siempre es 1 y deshabilitada.
5. **Validación de semana**: si el usuario edita una semana fuera del rango válido del programa (ej. semana 3 para un programa de 14 días), silenciosamente resetear a 1.
6. **No romper el flujo existente**: el botón "Calculate Optimization" y toda la lógica de `ejecutar_optimizacion` sigue igual — usa `pacientes_actuales` como lista plana, ignorando semanas.

---

## 8. RESUMEN DE CAMBIOS POR SECCIÓN

| Sección | Tipo de cambio |
|---|---|
| Import línea 12 | Agregar `verificar_admision_semana` |
| Inicialización session_state (~línea 575) | Agregar `semana_pacientes` |
| tab1 — tabla Patients by Program | Agregar columna "Week" |
| tab2 — tabla Base Programs | Agregar columna "Week" (editable con selector) |
| tab2 — tabla Extensions | Agregar columna "Week" (siempre 1, deshabilitada) |
| tab2 — botón Clear All | Reset `semana_pacientes` a todo 1 |
| tab4 — formulario solicitud | Agregar selector "Week" |
| tab4 — estructura `solicitudes_admision` | Cambiar de `{idx: int}` a `{idx: {"cantidad": int, "semana": int}}` |
| tab4 — tabla solicitudes pendientes | Agregar columna "Week" |
| tab4 — botón Verify Feasibility | Llamar `verificar_admision_semana` en vez de `verificar_admision` |
| tab4 — tabla Detail by Program | Agregar columna "Week" en resultados |
