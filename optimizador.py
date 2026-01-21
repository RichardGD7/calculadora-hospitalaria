# -*- coding: utf-8 -*-
"""optimizador.py - Módulo de optimización de pacientes para Sanoviv.

Expone la función ejecutar_optimizacion() que calcula cuántos pacientes
adicionales se pueden recibir por programa, respetando las restricciones
de recursos.
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
import datos_sanoviv_generado as datos

# Tolerancia numérica
TOL = 1e-9


def obtener_datos_base():
    """Retorna los datos base del modelo para uso en la interfaz."""
    # Número de recursos profesionales para clasificación
    n_profesionales = len(datos.nom_rec_prof)

    # Configuración de programas estrella (con valores por defecto si no existen)
    programas_estrella = getattr(datos, "programas_estrella", [False] * datos.NO_PROGRAMAS)
    multiplicador_estrella = getattr(datos, "multiplicador_estrella", 1.0)

    return {
        "n_programas": datos.NO_PROGRAMAS,
        "m_recursos": datos.NO_RECURSOS,
        "n_profesionales": n_profesionales,
        "nombre_programas": datos.orden_programas,
        "nombre_recursos": datos.nom_rec_total,
        "pacientes_actuales": datos.pacientes_actuales.copy(),
        "prioridad_programas": datos.prioridad_programas,
        "capacidades": datos.cap_rec_total,
        "consumo": datos.matriz_consumo_total,
        # Datos separados para administración
        "nombre_rec_prof": datos.nom_rec_prof,
        "nombre_rec_fis": datos.nom_rec_fis,
        "cap_rec_prof": datos.cap_rec_prof,
        "cap_rec_fis": datos.cap_rec_fis,
        # Configuración de programas estrella
        "programas_estrella": programas_estrella,
        "multiplicador_estrella": multiplicador_estrella,
    }


def ejecutar_optimizacion(pacientes_actuales: list) -> dict:
    """Ejecuta el modelo de optimización y retorna los resultados.

    Args:
        pacientes_actuales: Lista con el número de pacientes actuales por programa.

    Returns:
        Diccionario con:
        - estado: str ("Optimal", "Infeasible", etc.)
        - pacientes_adicionales: list[int] por programa
        - total_ponderado: float
        - total_pacientes: int
        - recursos_excedidos: list[dict] con info de recursos excedidos
        - tabla_recursos: list[dict] con info de uso por recurso
    """
    # Cargar datos
    n_programas = datos.NO_PROGRAMAS
    m_recursos = datos.NO_RECURSOS
    consumo = datos.matriz_consumo_total
    capacidades = datos.cap_rec_total
    nombre_programas = datos.orden_programas
    nombre_recursos = datos.nom_rec_total

    # Prioridades por programa
    prioridad_programas = getattr(datos, "prioridad_programas", [1.0] * n_programas)
    if not isinstance(prioridad_programas, (list, tuple)) or len(prioridad_programas) != n_programas:
        prioridad_programas = [1.0] * n_programas

    # Configuración de programas estrella
    programas_estrella = getattr(datos, "programas_estrella", [False] * n_programas)
    if not isinstance(programas_estrella, (list, tuple)) or len(programas_estrella) != n_programas:
        programas_estrella = [False] * n_programas
    multiplicador_estrella = getattr(datos, "multiplicador_estrella", 1.0)

    # Calcular prioridades efectivas (aplicando multiplicador a programas estrella)
    prioridad_efectiva = [
        prioridad_programas[j] * (multiplicador_estrella if programas_estrella[j] else 1.0)
        for j in range(n_programas)
    ]

    # Calcular uso actual y clasificar recursos
    uso_actual_por_recurso = []
    excedidos = []
    activos = []

    for r in range(m_recursos):
        uso_actual = sum(consumo[r][j] * pacientes_actuales[j] for j in range(n_programas))
        uso_actual_por_recurso.append(uso_actual)
        if uso_actual > capacidades[r] + TOL:
            excedidos.append(r)
        else:
            activos.append(r)

    # Información de recursos excedidos
    recursos_excedidos = []
    for r in excedidos:
        sobre = uso_actual_por_recurso[r] - capacidades[r]
        recursos_excedidos.append({
            "nombre": nombre_recursos[r],
            "uso_actual": uso_actual_por_recurso[r],
            "capacidad": capacidades[r],
            "excedente": sobre,
        })

    # Calcular capacidad restante y upper bounds
    cap_restante = {r: max(capacidades[r] - uso_actual_por_recurso[r], 0.0) for r in activos}

    upper_bounds = []
    for j in range(n_programas):
        candidatos = []
        for r in activos:
            coef = consumo[r][j]
            if coef > TOL:
                candidatos.append(cap_restante[r] / coef)
        if candidatos:
            ub = int(max(min(candidatos), 0))
        else:
            ub = 0
        upper_bounds.append(ub)

    if len(activos) == 0:
        upper_bounds = [0] * n_programas

    # Construir modelo de optimización
    modelo = LpProblem("Pacientes_Adicionales", LpMaximize)

    adicionales = [
        LpVariable(f"adicionales_{j+1}", lowBound=0, upBound=upper_bounds[j], cat=LpInteger)
        for j in range(n_programas)
    ]

    modelo += (
        lpSum(prioridad_efectiva[j] * adicionales[j] for j in range(n_programas)),
        "Total_Ponderado_Pacientes_Adicionales",
    )

    for r in activos:
        rhs = capacidades[r] - uso_actual_por_recurso[r]
        lhs = lpSum(consumo[r][j] * adicionales[j] for j in range(n_programas))
        modelo += lhs <= rhs + TOL, f"Recurso_{r+1}_no_excedido"

    # Resolver
    status = modelo.solve(PULP_CBC_CMD(msg=False))
    estado = LpStatus[status]

    # Preparar resultados
    if estado == "Optimal":
        valores = [int(v.value()) for v in adicionales]
        total_ponderado = sum(prioridad_efectiva[j] * valores[j] for j in range(n_programas))
        total_pacientes = sum(valores)
    else:
        valores = [0] * n_programas
        total_ponderado = 0.0
        total_pacientes = 0

    # Construir tabla de recursos
    n_profesionales = len(datos.nom_rec_prof)
    tabla_recursos = []
    for r in activos:
        uso_actual = uso_actual_por_recurso[r]
        uso_adicional = sum(consumo[r][j] * valores[j] for j in range(n_programas))
        uso_total = uso_actual + uso_adicional
        capacidad = capacidades[r]
        pct_actual = (uso_actual / capacidad * 100) if capacidad > 0 else 0.0
        pct_adicional = (uso_adicional / capacidad * 100) if capacidad > 0 else 0.0
        pct_total = (uso_total / capacidad * 100) if capacidad > 0 else 0.0
        ok = uso_total <= capacidad + 1e-6
        tipo = "profesional" if r < n_profesionales else "fisico"

        tabla_recursos.append({
            "nombre": nombre_recursos[r],
            "tipo": tipo,
            "capacidad": capacidad,
            "uso_actual": uso_actual,
            "pct_actual": pct_actual,
            "uso_adicional": uso_adicional,
            "pct_adicional": pct_adicional,
            "uso_total": uso_total,
            "pct_total": pct_total,
            "ok": ok,
        })

    return {
        "estado": estado,
        "pacientes_adicionales": valores,
        "nombre_programas": nombre_programas,
        "total_ponderado": total_ponderado,
        "total_pacientes": total_pacientes,
        "recursos_excedidos": recursos_excedidos,
        "tabla_recursos": tabla_recursos,
    }


def verificar_admision(pacientes_actuales: list, solicitudes: dict) -> dict:
    """Verifica si es factible admitir un número específico de pacientes por programa.

    Args:
        pacientes_actuales: Lista con el número de pacientes actuales por programa.
        solicitudes: Diccionario {índice_programa: cantidad_solicitada} con las
                     solicitudes de admisión a verificar.

    Returns:
        Diccionario con:
        - factible: bool indicando si todas las solicitudes son factibles
        - solicitudes_detalle: list[dict] con detalle por solicitud
        - recursos_limitantes: list[dict] con recursos que impiden la admisión
        - impacto_recursos: list[dict] con el impacto en cada recurso
    """
    # Cargar datos
    n_programas = datos.NO_PROGRAMAS
    m_recursos = datos.NO_RECURSOS
    consumo = datos.matriz_consumo_total
    capacidades = datos.cap_rec_total
    nombre_programas = datos.orden_programas
    nombre_recursos = datos.nom_rec_total
    n_profesionales = len(datos.nom_rec_prof)

    # Calcular uso actual por recurso
    uso_actual_por_recurso = []
    for r in range(m_recursos):
        uso_actual = sum(consumo[r][j] * pacientes_actuales[j] for j in range(n_programas))
        uso_actual_por_recurso.append(uso_actual)

    # Calcular capacidad restante por recurso
    cap_restante = [max(capacidades[r] - uso_actual_por_recurso[r], 0.0) for r in range(m_recursos)]

    # Calcular uso adicional requerido por las solicitudes
    uso_adicional_por_recurso = [0.0] * m_recursos
    for programa_idx, cantidad in solicitudes.items():
        for r in range(m_recursos):
            uso_adicional_por_recurso[r] += consumo[r][programa_idx] * cantidad

    # Verificar factibilidad y encontrar recursos limitantes
    recursos_limitantes = []
    impacto_recursos = []
    factible_global = True

    for r in range(m_recursos):
        uso_total_proyectado = uso_actual_por_recurso[r] + uso_adicional_por_recurso[r]
        capacidad = capacidades[r]
        excedente = uso_total_proyectado - capacidad
        es_factible = excedente <= TOL
        tipo = "profesional" if r < n_profesionales else "fisico"

        if not es_factible:
            factible_global = False
            recursos_limitantes.append({
                "nombre": nombre_recursos[r],
                "tipo": tipo,
                "capacidad": capacidad,
                "uso_actual": uso_actual_por_recurso[r],
                "uso_adicional_requerido": uso_adicional_por_recurso[r],
                "uso_total_proyectado": uso_total_proyectado,
                "excedente": excedente,
                "pct_uso_proyectado": (uso_total_proyectado / capacidad * 100) if capacidad > 0 else 0,
            })

        # Registrar impacto en todos los recursos afectados
        if uso_adicional_por_recurso[r] > TOL:
            pct_actual = (uso_actual_por_recurso[r] / capacidad * 100) if capacidad > 0 else 0
            pct_proyectado = (uso_total_proyectado / capacidad * 100) if capacidad > 0 else 0
            impacto_recursos.append({
                "nombre": nombre_recursos[r],
                "tipo": tipo,
                "capacidad": capacidad,
                "uso_actual": uso_actual_por_recurso[r],
                "pct_actual": pct_actual,
                "uso_adicional": uso_adicional_por_recurso[r],
                "uso_proyectado": uso_total_proyectado,
                "pct_proyectado": pct_proyectado,
                "factible": es_factible,
            })

    # Ordenar recursos limitantes por excedente (de mayor a menor)
    recursos_limitantes.sort(key=lambda x: x["excedente"], reverse=True)

    # Ordenar impacto por porcentaje proyectado (de mayor a menor)
    impacto_recursos.sort(key=lambda x: x["pct_proyectado"], reverse=True)

    # Detalle por solicitud: calcular capacidad máxima disponible para cada programa
    solicitudes_detalle = []
    for programa_idx, cantidad_solicitada in solicitudes.items():
        # Calcular máximo admisible para este programa
        max_admisible = float("inf")
        recurso_limitante = None

        for r in range(m_recursos):
            coef = consumo[r][programa_idx]
            if coef > TOL:
                max_por_recurso = cap_restante[r] / coef
                if max_por_recurso < max_admisible:
                    max_admisible = max_por_recurso
                    recurso_limitante = nombre_recursos[r]

        max_admisible = int(max(max_admisible, 0)) if max_admisible != float("inf") else 0
        es_factible_programa = cantidad_solicitada <= max_admisible

        solicitudes_detalle.append({
            "programa": nombre_programas[programa_idx],
            "programa_idx": programa_idx,
            "cantidad_solicitada": cantidad_solicitada,
            "max_admisible": max_admisible,
            "factible": es_factible_programa,
            "recurso_limitante": recurso_limitante if not es_factible_programa else None,
            "deficit": max(cantidad_solicitada - max_admisible, 0),
        })

    return {
        "factible": factible_global,
        "solicitudes_detalle": solicitudes_detalle,
        "recursos_limitantes": recursos_limitantes,
        "impacto_recursos": impacto_recursos,
    }
