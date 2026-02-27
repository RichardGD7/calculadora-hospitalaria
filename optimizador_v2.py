# -*- coding: utf-8 -*-
"""optimizador.py — Módulo de optimización de capacidad para Sanoviv.

Expone tres funciones públicas:
    construir_modelo_datos()  → Prepara todas las estructuras del modelo a partir
                                de BD_sanoviv.py. Se llama una vez por sesión
                                o cada vez que los datos cambian.
    ejecutar_optimizacion()   → Resuelve el ILP y retorna pacientes adicionales.
    verificar_admision()      → Verifica si una solicitud específica es factible.

Las matrices de consumo se calculan en tiempo real desde las actividades definidas
en BD_sanoviv.programas. No existen matrices precalculadas.

Fórmula de consumo semanal por paciente para una actividad:
    consumo_h = (cantidad * duracion_min / 60) / (duracion_dias / 7)
"""

from pulp import (
    LpProblem,
    LpVariable,
    LpInteger,
    LpStatus,
    lpSum,
    LpMaximize,
    PULP_CBC_CMD,
)
import BD_sanoviv as datos

# Tolerancia numérica para comparaciones de punto flotante
TOL = 1e-9


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTRUCCIÓN DE ESTRUCTURAS DEL MODELO
# ══════════════════════════════════════════════════════════════════════════════

def construir_modelo_datos() -> dict:
    """Construye todas las estructuras necesarias para el modelo ILP.

    Lee BD_sanoviv.programas, recursos_profesionales y recursos_fisicos,
    y calcula las matrices de consumo en tiempo real.

    Returns:
        dict con:
            nombres_programas   : list[str]
            duraciones_dias     : dict[str, int]
            prioridades         : list[float]
            n_programas         : int

            nombres_rec_prof    : list[str]
            nombres_rec_fis     : list[str]
            nombres_rec_total   : list[str]   (prof primero, luego fis)
            n_profesionales     : int
            n_recursos          : int

            cap_rec_prof        : dict[str, float]
            cap_rec_fis         : dict[str, float]
            capacidades         : list[float]  (misma orden que nombres_rec_total)

            consumo             : list[list[float]]  shape [n_recursos][n_programas]
                                  consumo[r][j] = horas semanales que consume 1 paciente
                                  del programa j en el recurso r
    """
    # ── Programas ──────────────────────────────────────────────────────────────
    nombres_programas = datos.nombres_programas
    n_programas       = len(nombres_programas)
    duraciones_dias   = datos.duraciones_dias
    prioridades       = [datos.programas[p]["prioridad"] for p in nombres_programas]

    # ── Recursos ───────────────────────────────────────────────────────────────
    nombres_rec_prof = [r["nombre"] for r in datos.recursos_profesionales]
    nombres_rec_fis  = [r["nombre"] for r in datos.recursos_fisicos]
    nombres_rec_total = nombres_rec_prof + nombres_rec_fis
    n_profesionales  = len(nombres_rec_prof)
    n_recursos       = len(nombres_rec_total)

    cap_rec_prof = datos.cap_rec_prof   # dict nombre → h/semana
    cap_rec_fis  = datos.cap_rec_fis    # dict nombre → h/semana
    capacidades  = (
        [cap_rec_prof[n] for n in nombres_rec_prof]
        + [cap_rec_fis[n] for n in nombres_rec_fis]
    )

    # ── Índices para lookup rápido ─────────────────────────────────────────────
    idx_rec = {nombre: i for i, nombre in enumerate(nombres_rec_total)}

    # ── Calcular matriz de consumo [n_recursos][n_programas] ──────────────────
    # Inicializar en cero
    consumo = [[0.0] * n_programas for _ in range(n_recursos)]

    for j, prog_name in enumerate(nombres_programas):
        prog       = datos.programas[prog_name]
        dias       = prog["duracion_dias"]
        semanas    = dias / 7.0
        actividades = prog["actividades"]

        for act in actividades:
            cantidad     = act["cantidad"]
            dur_min      = act["duracion_min"]
            rec_prof_list = act["recursos_prof"]   # list[str], puede ser vacía
            rec_fis       = act["recurso_fis"]     # str | None

            # Consumo semanal por paciente para esta actividad
            consumo_h = (cantidad * dur_min / 60.0) / semanas

            # Distribuir entre recursos profesionales (cada uno absorbe el consumo completo)
            for rp in rec_prof_list:
                if rp in idx_rec:
                    r = idx_rec[rp]
                    consumo[r][j] += consumo_h

            # Recurso físico
            if rec_fis and rec_fis in idx_rec:
                r = idx_rec[rec_fis]
                consumo[r][j] += consumo_h

    # Redondear a 4 decimales para estabilidad numérica
    consumo = [[round(v, 4) for v in fila] for fila in consumo]

    return {
        "nombres_programas":  nombres_programas,
        "duraciones_dias":    duraciones_dias,
        "prioridades":        prioridades,
        "n_programas":        n_programas,
        "nombres_rec_prof":   nombres_rec_prof,
        "nombres_rec_fis":    nombres_rec_fis,
        "nombres_rec_total":  nombres_rec_total,
        "n_profesionales":    n_profesionales,
        "n_recursos":         n_recursos,
        "cap_rec_prof":       cap_rec_prof,
        "cap_rec_fis":        cap_rec_fis,
        "capacidades":        capacidades,
        "consumo":            consumo,
    }


def obtener_datos_base() -> dict:
    """Retorna los datos base del modelo para uso en la interfaz (app.py).

    Mantiene compatibilidad con la interfaz anterior de app.py.
    Construye el modelo en tiempo real desde BD_sanoviv.py.
    """
    md = construir_modelo_datos()

    # Pacientes actuales por defecto: 0 para todos los programas
    pacientes_actuales = [0] * md["n_programas"]

    # Convertir capacidades a listas para compatibilidad con app.py
    cap_rec_prof_list = [md["cap_rec_prof"][n] for n in md["nombres_rec_prof"]]
    cap_rec_fis_list = [md["cap_rec_fis"][n] for n in md["nombres_rec_fis"]]

    return {
        "n_programas":        md["n_programas"],
        "m_recursos":         md["n_recursos"],
        "n_profesionales":    md["n_profesionales"],
        "nombre_programas":   md["nombres_programas"],
        "nombre_recursos":    md["nombres_rec_total"],
        "pacientes_actuales": pacientes_actuales,
        "prioridad_programas": md["prioridades"],
        "capacidades":        md["capacidades"],
        "consumo":            md["consumo"],
        # Separados para la UI de administración (como listas)
        "nombre_rec_prof":    md["nombres_rec_prof"],
        "nombre_rec_fis":     md["nombres_rec_fis"],
        "cap_rec_prof":       cap_rec_prof_list,
        "cap_rec_fis":        cap_rec_fis_list,
        # Datos completos para edición en admin
        "recursos_profesionales": datos.recursos_profesionales,
        "recursos_fisicos":       datos.recursos_fisicos,
        "programas":              datos.programas,
        "duraciones_dias":        md["duraciones_dias"],
        # Campos de compatibilidad (programas estrella ya no se usan aquí)
        "programas_estrella":     [False] * md["n_programas"],
        "multiplicador_estrella": 1.0,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  OPTIMIZACIÓN
# ══════════════════════════════════════════════════════════════════════════════

def ejecutar_optimizacion(pacientes_actuales: list) -> dict:
    """Ejecuta el modelo ILP y retorna cuántos pacientes adicionales se pueden admitir.

    Args:
        pacientes_actuales: list[int] — pacientes actuales por programa,
                            en el mismo orden que datos.nombres_programas.

    Returns:
        dict con:
            estado                : str  ("Optimal", "Infeasible", etc.)
            pacientes_adicionales : list[int]  por programa
            nombre_programas      : list[str]
            total_ponderado       : float
            total_pacientes       : int
            recursos_excedidos    : list[dict]
            tabla_recursos        : list[dict]
    """
    md = construir_modelo_datos()

    n_programas      = md["n_programas"]
    n_recursos       = md["n_recursos"]
    consumo          = md["consumo"]
    capacidades      = md["capacidades"]
    nombre_programas = md["nombres_programas"]
    nombre_recursos  = md["nombres_rec_total"]
    n_profesionales  = md["n_profesionales"]
    prioridades      = md["prioridades"]

    # ── Calcular uso actual por recurso ────────────────────────────────────────
    uso_actual = [
        sum(consumo[r][j] * pacientes_actuales[j] for j in range(n_programas))
        for r in range(n_recursos)
    ]

    # ── Clasificar recursos ────────────────────────────────────────────────────
    excedidos = [r for r in range(n_recursos) if uso_actual[r] > capacidades[r] + TOL]
    activos   = [r for r in range(n_recursos) if uso_actual[r] <= capacidades[r] + TOL]

    recursos_excedidos = [
        {
            "nombre":    nombre_recursos[r],
            "uso_actual": uso_actual[r],
            "capacidad": capacidades[r],
            "excedente": uso_actual[r] - capacidades[r],
        }
        for r in excedidos
    ]

    # ── Upper bounds por programa ──────────────────────────────────────────────
    cap_restante = {r: max(capacidades[r] - uso_actual[r], 0.0) for r in activos}

    upper_bounds = []
    for j in range(n_programas):
        candidatos = [
            cap_restante[r] / consumo[r][j]
            for r in activos
            if consumo[r][j] > TOL
        ]
        upper_bounds.append(int(max(min(candidatos), 0)) if candidatos else 0)

    if not activos:
        upper_bounds = [0] * n_programas

    # ── Construir y resolver modelo ────────────────────────────────────────────
    modelo = LpProblem("Pacientes_Adicionales", LpMaximize)

    adicionales = [
        LpVariable(f"adicionales_{j+1}", lowBound=0, upBound=upper_bounds[j], cat=LpInteger)
        for j in range(n_programas)
    ]

    modelo += (
        lpSum(prioridades[j] * adicionales[j] for j in range(n_programas)),
        "Total_Ponderado",
    )

    for r in activos:
        rhs = capacidades[r] - uso_actual[r]
        modelo += (
            lpSum(consumo[r][j] * adicionales[j] for j in range(n_programas)) <= rhs + TOL,
            f"Recurso_{r+1}",
        )

    status = modelo.solve(PULP_CBC_CMD(msg=False))
    estado = LpStatus[status]

    # ── Resultados ─────────────────────────────────────────────────────────────
    if estado == "Optimal":
        valores         = [int(v.value()) for v in adicionales]
        total_ponderado = sum(prioridades[j] * valores[j] for j in range(n_programas))
        total_pacientes = sum(valores)
    else:
        valores         = [0] * n_programas
        total_ponderado = 0.0
        total_pacientes = 0

    tabla_recursos = []
    for r in activos:
        uso_adic  = sum(consumo[r][j] * valores[j] for j in range(n_programas))
        uso_total = uso_actual[r] + uso_adic
        cap       = capacidades[r]
        tipo      = "profesional" if r < n_profesionales else "fisico"

        tabla_recursos.append({
            "nombre":        nombre_recursos[r],
            "tipo":          tipo,
            "capacidad":     cap,
            "uso_actual":    uso_actual[r],
            "pct_actual":    (uso_actual[r] / cap * 100) if cap > 0 else 0.0,
            "uso_adicional": uso_adic,
            "pct_adicional": (uso_adic / cap * 100) if cap > 0 else 0.0,
            "uso_total":     uso_total,
            "pct_total":     (uso_total / cap * 100) if cap > 0 else 0.0,
            "ok":            uso_total <= cap + 1e-6,
        })

    return {
        "estado":                estado,
        "pacientes_adicionales": valores,
        "nombre_programas":      nombre_programas,
        "total_ponderado":       total_ponderado,
        "total_pacientes":       total_pacientes,
        "recursos_excedidos":    recursos_excedidos,
        "tabla_recursos":        tabla_recursos,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  VERIFICACIÓN DE ADMISIÓN
# ══════════════════════════════════════════════════════════════════════════════

def verificar_admision(pacientes_actuales: list, solicitudes: dict) -> dict:
    """Verifica si es factible admitir un número específico de pacientes por programa.

    Args:
        pacientes_actuales: list[int] — pacientes actuales por programa.
        solicitudes: dict[int, int]  — {índice_programa: cantidad_solicitada}.

    Returns:
        dict con:
            factible             : bool
            solicitudes_detalle  : list[dict]
            recursos_limitantes  : list[dict]
            impacto_recursos     : list[dict]
    """
    md = construir_modelo_datos()

    n_programas      = md["n_programas"]
    n_recursos       = md["n_recursos"]
    consumo          = md["consumo"]
    capacidades      = md["capacidades"]
    nombre_programas = md["nombres_programas"]
    nombre_recursos  = md["nombres_rec_total"]
    n_profesionales  = md["n_profesionales"]

    # ── Uso actual y capacidad restante ───────────────────────────────────────
    uso_actual = [
        sum(consumo[r][j] * pacientes_actuales[j] for j in range(n_programas))
        for r in range(n_recursos)
    ]
    cap_restante = [max(capacidades[r] - uso_actual[r], 0.0) for r in range(n_recursos)]

    # ── Uso adicional requerido por las solicitudes ────────────────────────────
    uso_adicional = [0.0] * n_recursos
    for prog_idx, cantidad in solicitudes.items():
        for r in range(n_recursos):
            uso_adicional[r] += consumo[r][prog_idx] * cantidad

    # ── Verificar factibilidad ────────────────────────────────────────────────
    factible_global   = True
    recursos_limitantes = []
    impacto_recursos    = []

    for r in range(n_recursos):
        uso_proyectado = uso_actual[r] + uso_adicional[r]
        cap            = capacidades[r]
        excedente      = uso_proyectado - cap
        es_factible    = excedente <= TOL
        tipo           = "profesional" if r < n_profesionales else "fisico"

        if not es_factible:
            factible_global = False
            recursos_limitantes.append({
                "nombre":                  nombre_recursos[r],
                "tipo":                    tipo,
                "capacidad":               cap,
                "uso_actual":              uso_actual[r],
                "uso_adicional_requerido": uso_adicional[r],
                "uso_total_proyectado":    uso_proyectado,
                "excedente":               excedente,
                "pct_uso_proyectado":      (uso_proyectado / cap * 100) if cap > 0 else 0,
            })

        if uso_adicional[r] > TOL:
            impacto_recursos.append({
                "nombre":        nombre_recursos[r],
                "tipo":          tipo,
                "capacidad":     cap,
                "uso_actual":    uso_actual[r],
                "pct_actual":    (uso_actual[r] / cap * 100) if cap > 0 else 0,
                "uso_adicional": uso_adicional[r],
                "uso_proyectado": uso_proyectado,
                "pct_proyectado": (uso_proyectado / cap * 100) if cap > 0 else 0,
                "factible":      es_factible,
            })

    recursos_limitantes.sort(key=lambda x: x["excedente"], reverse=True)
    impacto_recursos.sort(key=lambda x: x["pct_proyectado"], reverse=True)

    # ── Detalle por solicitud ─────────────────────────────────────────────────
    solicitudes_detalle = []
    for prog_idx, cantidad_solicitada in solicitudes.items():
        max_admisible    = float("inf")
        rec_limitante    = None

        for r in range(n_recursos):
            coef = consumo[r][prog_idx]
            if coef > TOL:
                max_por_rec = cap_restante[r] / coef
                if max_por_rec < max_admisible:
                    max_admisible = max_por_rec
                    rec_limitante = nombre_recursos[r]

        max_admisible      = int(max(max_admisible, 0)) if max_admisible != float("inf") else 0
        es_factible_prog   = cantidad_solicitada <= max_admisible

        solicitudes_detalle.append({
            "programa":            nombre_programas[prog_idx],
            "programa_idx":        prog_idx,
            "cantidad_solicitada": cantidad_solicitada,
            "max_admisible":       max_admisible,
            "factible":            es_factible_prog,
            "recurso_limitante":   rec_limitante if not es_factible_prog else None,
            "deficit":             max(cantidad_solicitada - max_admisible, 0),
        })

    return {
        "factible":            factible_global,
        "solicitudes_detalle": solicitudes_detalle,
        "recursos_limitantes": recursos_limitantes,
        "impacto_recursos":    impacto_recursos,
    }
