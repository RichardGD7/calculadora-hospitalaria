# -*- coding: utf-8 -*-
"""app.py - Interfaz Streamlit para el optimizador de pacientes de Sanoviv."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np
from optimizador_v2 import obtener_datos_base, ejecutar_optimizacion, verificar_admision
import BD_sanoviv as datos


# =====================================================
# FUNCIONES DE VALIDACIÓN Y SANITIZACIÓN
# =====================================================

def safe_int(value, default=0, min_val=None, max_val=None):
    """
    Convierte un valor a entero de forma segura.
    Maneja strings, floats, NaN, None, y valores inválidos.
    """
    try:
        if value is None:
            return default
        if isinstance(value, str):
            # Limpiar espacios y caracteres no numéricos
            value = value.strip()
            if value == '' or value == '-':
                return default
            # Intentar convertir (maneja "123", "123.5", etc.)
            value = float(value)
        if isinstance(value, (float, np.floating)):
            if np.isnan(value) or np.isinf(value):
                return default
            value = int(round(value))
        if isinstance(value, (int, np.integer)):
            result = int(value)
        else:
            result = default

        # Aplicar límites
        if min_val is not None:
            result = max(result, min_val)
        if max_val is not None:
            result = min(result, max_val)
        return result
    except (ValueError, TypeError, OverflowError):
        return default


def safe_float(value, default=0.0, min_val=None, max_val=None, decimals=2):
    """
    Convierte un valor a float de forma segura.
    Maneja strings, enteros, NaN, None, y valores inválidos.
    """
    try:
        if value is None:
            return default
        if isinstance(value, str):
            value = value.strip().replace(',', '.')
            if value == '' or value == '-' or value == '.':
                return default
            value = float(value)
        if isinstance(value, (int, np.integer)):
            value = float(value)
        if isinstance(value, (float, np.floating)):
            if np.isnan(value) or np.isinf(value):
                return default
            result = round(float(value), decimals)
        else:
            result = default

        # Aplicar límites
        if min_val is not None:
            result = max(result, min_val)
        if max_val is not None:
            result = min(result, max_val)
        return result
    except (ValueError, TypeError, OverflowError):
        return default


def safe_bool(value, default=False):
    """
    Convierte un valor a booleano de forma segura.
    """
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float, np.integer, np.floating)):
            return bool(value)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'si', 'sí')
        return default
    except (ValueError, TypeError):
        return default


def safe_string(value, default="", max_length=500):
    """
    Convierte y limpia un string de forma segura.
    """
    try:
        if value is None:
            return default
        result = str(value).strip()
        if len(result) > max_length:
            result = result[:max_length]
        # Eliminar caracteres potencialmente problemáticos
        result = result.replace('\x00', '').replace('\r', '')
        return result if result else default
    except (ValueError, TypeError):
        return default


def sanitize_patients_dataframe(df, num_programs):
    """
    Sanitiza el DataFrame de pacientes, asegurando valores válidos.
    Retorna una lista de enteros validados.
    """
    result = []
    for i in range(num_programs):
        try:
            if i < len(df):
                value = df.iloc[i]["Current Patients"] if "Current Patients" in df.columns else 0
                result.append(safe_int(value, default=0, min_val=0, max_val=100))
            else:
                result.append(0)
        except (IndexError, KeyError, TypeError):
            result.append(0)
    return result


def sanitize_programs_dataframe(df, original_names):
    """
    Sanitiza el DataFrame de programas del panel de administración.
    """
    sanitized_data = []
    for i, name in enumerate(original_names):
        try:
            if i < len(df):
                row = df.iloc[i]
                sanitized_data.append({
                    "Program": safe_string(row.get("Program", name), default=name, max_length=200),
                    "Priority": safe_float(row.get("Priority", 1.0), default=1.0, min_val=0.0, max_val=10.0),
                    "Star": safe_bool(row.get("Star", False), default=False),
                })
            else:
                sanitized_data.append({
                    "Program": name,
                    "Priority": 1.0,
                    "Star": False,
                })
        except (IndexError, KeyError, TypeError):
            sanitized_data.append({
                "Program": name,
                "Priority": 1.0,
                "Star": False,
            })
    return pd.DataFrame(sanitized_data)


def sanitize_resources_dataframe(df, original_names, original_capacities):
    """
    Sanitiza el DataFrame de recursos del panel de administración.
    """
    sanitized_data = []
    for i, (name, cap) in enumerate(zip(original_names, original_capacities)):
        try:
            if i < len(df):
                row = df.iloc[i]
                sanitized_data.append({
                    "Resource": safe_string(row.get("Resource", name), default=name, max_length=200),
                    "Capacity (h/week)": safe_float(row.get("Capacity (h/week)", cap), default=cap, min_val=0.0, max_val=10000.0, decimals=1),
                })
            else:
                sanitized_data.append({
                    "Resource": name,
                    "Capacity (h/week)": cap,
                })
        except (IndexError, KeyError, TypeError):
            sanitized_data.append({
                "Resource": name,
                "Capacity (h/week)": cap,
            })
    return pd.DataFrame(sanitized_data)


def validate_before_save(programas_df, recursos_prof_df, recursos_fis_df, multiplicador):
    """
    Valida todos los datos antes de guardar. Retorna (is_valid, error_messages).
    """
    errors = []

    # Validar multiplicador
    if not (1.0 <= multiplicador <= 10.0):
        errors.append(f"Star multiplier must be between 1.0 and 10.0 (got {multiplicador})")

    # Validar programas
    for i, row in programas_df.iterrows():
        prog_name = row.get("Program", f"Program {i+1}")
        priority = row.get("Priority", 0)
        if not isinstance(priority, (int, float)) or priority < 0 or priority > 10:
            errors.append(f"Invalid priority for '{prog_name}': must be 0-10")

    # Validar recursos profesionales
    for i, row in recursos_prof_df.iterrows():
        res_name = row.get("Resource", f"Resource {i+1}")
        cap = row.get("Capacity (h/week)", 0)
        if not isinstance(cap, (int, float)) or cap < 0:
            errors.append(f"Invalid capacity for '{res_name}': must be >= 0")

    # Validar recursos físicos
    for i, row in recursos_fis_df.iterrows():
        res_name = row.get("Resource", f"Resource {i+1}")
        cap = row.get("Capacity (h/week)", 0)
        if not isinstance(cap, (int, float)) or cap < 0:
            errors.append(f"Invalid capacity for '{res_name}': must be >= 0")

    return len(errors) == 0, errors


def guardar_datos_sanoviv(programas_data, recursos_prof_data, recursos_fis_data):
    """Guarda los datos editados en el archivo BD_sanoviv.py.

    Args:
        programas_data: dict con la estructura completa de programas
        recursos_prof_data: list[dict] con recursos profesionales
        recursos_fis_data: list[dict] con recursos físicos
    """
    archivo_path = os.path.join(os.path.dirname(__file__), "BD_sanoviv.py")

    # Construir el contenido del archivo
    contenido = '''"""
datos_sanoviv.py — Fuente única de verdad para la Calculadora de Capacidad Sanoviv

ESTRUCTURA DE DATOS
===================
programas : dict[str, dict]
    Cada programa tiene:
        duracion_dias   : int
        prioridad       : int   (1 = más alta)
        tipo            : str   ("programa" | "extension")
        programa_base   : str   (solo en extensiones — nombre del programa base)
        actividades     : list[dict]
            nombre          : str
            tipo            : str   (Consulta / Terapia / Estudio / Otro)
            cantidad        : int   (ocurrencias por estancia completa)
            duracion_min    : int   (minutos por sesión)
            recursos_prof   : list[str]   (nombres exactos de recursos profesionales)
            recurso_fis     : str | None  (nombre exacto de recurso físico, o None)

recursos_profesionales : list[dict]
    departamento, nombre, num_personas,
    cap_semanal_por_persona (h), cap_semanal_total (h)

recursos_fisicos : list[dict]
    departamento, nombre, num_unidades,
    cap_semanal_por_unidad (h), cap_semanal_total (h)

CÁLCULO DE CONSUMO SEMANAL (aplicado en optimizador.py)
=========================================================
consumo_semanal_h = (cantidad * duracion_min / 60) / (duracion_dias / 7)
"""


'''

    # Escribir programas
    contenido += "programas = {\n"
    for prog_name, prog_data in programas_data.items():
        contenido += f"    {repr(prog_name)}: {{\n"
        contenido += f'        "duracion_dias": {prog_data["duracion_dias"]},\n'
        contenido += f'        "prioridad": {prog_data["prioridad"]},\n'
        contenido += f'        "tipo":          {repr(prog_data.get("tipo", "programa"))},\n'
        if prog_data.get("programa_base"):
            contenido += f'        "programa_base": {repr(prog_data["programa_base"])},\n'
        contenido += '        "actividades": [\n'

        for act in prog_data["actividades"]:
            contenido += '            {\n'
            contenido += f'                "nombre":        {repr(act["nombre"])},\n'
            contenido += f'                "tipo":          {repr(act["tipo"])},\n'
            contenido += f'                "cantidad":      {act["cantidad"]},\n'
            contenido += f'                "duracion_min":  {act["duracion_min"]},\n'
            contenido += f'                "recursos_prof": {repr(act["recursos_prof"])},\n'
            rec_fis = repr(act["recurso_fis"]) if act["recurso_fis"] else "None"
            contenido += f'                "recurso_fis":   {rec_fis},\n'
            contenido += '            },\n'

        contenido += '        ],\n'
        contenido += '    },\n'
    contenido += '}\n\n\n'

    # Escribir recursos profesionales
    contenido += "recursos_profesionales = [\n"
    for rec in recursos_prof_data:
        contenido += '    {\n'
        contenido += f'        "departamento":            {repr(rec["departamento"])},\n'
        contenido += f'        "nombre":                  {repr(rec["nombre"])},\n'
        contenido += f'        "num_personas":            {rec["num_personas"]},\n'
        contenido += f'        "cap_semanal_por_persona": {rec["cap_semanal_por_persona"]},\n'
        contenido += f'        "cap_semanal_total":       {rec["cap_semanal_total"]},\n'
        contenido += '    },\n'
    contenido += ']\n\n\n'

    # Escribir recursos físicos
    contenido += "recursos_fisicos = [\n"
    for rec in recursos_fis_data:
        contenido += '    {\n'
        contenido += f'        "departamento":            {repr(rec["departamento"])},\n'
        contenido += f'        "nombre":                  {repr(rec["nombre"])},\n'
        contenido += f'        "num_unidades":            {rec["num_unidades"]},\n'
        contenido += f'        "cap_semanal_por_unidad":  {rec["cap_semanal_por_unidad"]},\n'
        contenido += f'        "cap_semanal_total":       {rec["cap_semanal_total"]},\n'
        contenido += '    },\n'
    contenido += ']\n\n\n'

    # Escribir helpers derivados
    contenido += '''# ── Lookup helpers (derivados de las listas; NO editar manualmente) ──────────
cap_rec_prof = {r["nombre"]: r["cap_semanal_total"] for r in recursos_profesionales}
cap_rec_fis  = {r["nombre"]: r["cap_semanal_total"] for r in recursos_fisicos}

nombres_programas = list(programas.keys())
duraciones_dias   = {k: v["duracion_dias"] for k, v in programas.items()}
prioridades       = {k: v["prioridad"]     for k, v in programas.items()}
'''

    # Guardar el archivo
    with open(archivo_path, "w", encoding="utf-8") as f:
        f.write(contenido)

    return True

# === CONFIGURACIÓN DE COLORES ARKODE ===
COLORS = {
    "primary": "#0F1C2E",      # Azul marino oscuro
    "secondary": "#1E3A5F",    # Azul marino medio
    "accent": "#FF6B5B",       # Coral/salmón
    "success": "#10B981",      # Verde
    "warning": "#F59E0B",      # Amarillo
    "danger": "#EF4444",       # Rojo
    "light": "#F8FAFC",        # Gris muy claro
    "text": "#0F1C2E",         # Texto principal
    "text_muted": "#64748B",   # Texto secundario
}

# Configuración de la página
st.set_page_config(
    page_title="Sanoviv - Patient Optimization",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# === ESTILOS CSS PERSONALIZADOS ===
st.markdown(f"""
<style>
    /* Fuente general */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* Header principal */
    .main-header {{
        background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
    }}

    .main-header h1 {{
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
    }}

    .main-header p {{
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
    }}

    /* Tarjetas de métricas */
    .metric-card {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 4px solid {COLORS["accent"]};
        height: 100%;
    }}

    .metric-card.primary {{
        border-left-color: {COLORS["primary"]};
    }}

    .metric-card.success {{
        border-left-color: {COLORS["success"]};
    }}

    .metric-label {{
        font-size: 0.875rem;
        color: {COLORS["text_muted"]};
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }}

    .metric-value {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {COLORS["primary"]};
        line-height: 1;
    }}

    .metric-value.accent {{
        color: {COLORS["accent"]};
    }}

    /* Pestañas personalizadas */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {COLORS["light"]};
        padding: 0.5rem;
        border-radius: 12px;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 900 !important;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLORS["primary"]} !important;
        color: white !important;
    }}

    /* Botón principal */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORS["accent"]} 0%, #FF8577 100%);
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }}

    .stButton > button[kind="primary"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 107, 91, 0.4);
    }}

    /* Tablas */
    .stDataFrame {{
        border-radius: 12px;
        overflow: hidden;
    }}

    /* Sección */
    .section-header {{
        font-size: 1.25rem;
        font-weight: 600;
        color: {COLORS["primary"]};
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid {COLORS["light"]};
    }}

    /* Alerta de recurso excedido */
    .resource-alert {{
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}

    /* Footer */
    .footer {{
        text-align: center;
        color: {COLORS["text_muted"]};
        padding: 2rem;
        margin-top: 2rem;
        border-top: 1px solid {COLORS["light"]};
        font-size: 0.875rem;
    }}

    .footer .logo {{
        font-weight: 700;
        color: {COLORS["primary"]};
    }}

    .footer .dot {{
        color: {COLORS["accent"]};
    }}
</style>
""", unsafe_allow_html=True)

# === MAIN HEADER ===
st.markdown("""
<div class="main-header">
    <h1>Sanoviv - Capacity Optimization</h1>
    <p>Patient planning system by treatment program</p>
</div>
""", unsafe_allow_html=True)

# === CARGAR DATOS ===
datos_base = obtener_datos_base()

# === ÍNDICES POR TIPO (programa base vs extensión) ===
_programas_dict = datos_base["programas"]
_nombres = datos_base["nombre_programas"]
indices_base = [i for i, n in enumerate(_nombres) if _programas_dict[n].get("tipo") == "programa"]
indices_ext = [i for i, n in enumerate(_nombres) if _programas_dict[n].get("tipo") == "extension"]

# Contraseña de administrador
ADMIN_PASSWORD = "AdminSanoviv2026"

# Inicializar estado de sesión
if "pacientes_actuales" not in st.session_state:
    st.session_state.pacientes_actuales = datos_base["pacientes_actuales"].copy()

if "resultados" not in st.session_state:
    st.session_state.resultados = None

if "resultado_verificacion" not in st.session_state:
    st.session_state.resultado_verificacion = None

if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False

# === SIDEBAR - MODO ADMINISTRADOR ===
with st.sidebar:
    st.markdown("### Access Mode")

    if st.session_state.admin_mode:
        st.success("Administrator Mode Active")
        if st.button("Logout", use_container_width=True):
            st.session_state.admin_mode = False
            st.rerun()
    else:
        st.info("Viewer Mode")
        with st.expander("Administrator Login"):
            password = st.text_input("Password:", type="password", key="admin_password")
            if st.button("Login", use_container_width=True):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_mode = True
                    st.rerun()
                else:
                    st.error("Incorrect password")

# === SINCRONIZAR DATOS DEL EDITOR (antes de renderizar pestañas) ===
# Esto asegura que los cambios del data_editor se reflejen en todas las pestañas
# Con validación robusta para evitar errores por caracteres inválidos
for editor_key, idx_map in [("editor_pacientes_base", indices_base), ("editor_pacientes_ext", indices_ext)]:
    if editor_key in st.session_state:
        editor_data = st.session_state[editor_key]
        if "edited_rows" in editor_data and editor_data["edited_rows"]:
            for row_idx, changes in editor_data["edited_rows"].items():
                if "Current Patients" in changes:
                    try:
                        local_idx = safe_int(row_idx, default=0, min_val=0, max_val=len(idx_map)-1)
                        global_idx = idx_map[local_idx]
                        new_value = safe_int(changes["Current Patients"], default=0, min_val=0, max_val=100)
                        st.session_state.pacientes_actuales[global_idx] = new_value
                    except (IndexError, TypeError, ValueError):
                        pass
            st.session_state.resultados = None

# === PESTAÑAS ===
if st.session_state.admin_mode:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Executive Summary", "👥 Patients", "📈 Resources", "🔍 Verify Admission", "⚙️ Administration"])
else:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive Summary", "👥 Patients", "📈 Resources", "🔍 Verify Admission"])

# =====================================================
# TAB 1: RESUMEN EJECUTIVO
# =====================================================
with tab1:
    # Métricas principales en la parte superior
    total_actuales = sum(st.session_state.pacientes_actuales)

    if st.session_state.resultados is not None and st.session_state.resultados["estado"] == "Optimal":
        resultados = st.session_state.resultados
        total_adicionales = resultados["total_pacientes"]
        total_proyectado = total_actuales + total_adicionales

        # Métricas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="metric-card primary">
                <div class="metric-label">Current Patients</div>
                <div class="metric-value">{total_actuales}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Additional Capacity</div>
                <div class="metric-value accent">+{total_adicionales}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card success">
                <div class="metric-label">Projected Total</div>
                <div class="metric-value">{total_proyectado}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Advertencia prominente si hay recursos excedidos
        if resultados["recursos_excedidos"]:
            num_excedidos = len(resultados["recursos_excedidos"])
            nombres_excedidos = ", ".join([r["nombre"] for r in resultados["recursos_excedidos"][:3]])
            if num_excedidos > 3:
                nombres_excedidos += f" y {num_excedidos - 3} más"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); border: 2px solid #F59E0B; border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem;">
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <span style="font-size: 1.75rem;">⚠️</span>
                    <div>
                        <strong style="color: #92400E; font-size: 1.1rem;">Warning: Results with exceeded resources</strong><br>
                        <span style="color: #78350F; font-size: 0.95rem;">
                            There are <strong>{num_excedidos} resource(s)</strong> already exceeding their capacity with current patients:
                            <em>{nombres_excedidos}</em>.<br>
                            These resources were <strong>excluded from the optimization model</strong>.
                            The suggested additional patients could worsen this situation further.
                            <strong>It is recommended to resolve the current oversaturation first.</strong>
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Gráficos lado a lado
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown('<div class="section-header">Patients by Program</div>', unsafe_allow_html=True)

            # Gráfico de barras comparativo - ordenado por total de mayor a menor
            df_chart = pd.DataFrame({
                "Program": resultados["nombre_programas"],
                "Current": st.session_state.pacientes_actuales,
                "Additional": resultados["pacientes_adicionales"],
            })
            df_chart["Total"] = df_chart["Current"] + df_chart["Additional"]
            df_chart = df_chart.sort_values("Total", ascending=True)  # ascending=True para que el mayor quede arriba en barras horizontales

            fig_bar = go.Figure()

            fig_bar.add_trace(go.Bar(
                name="Current",
                y=df_chart["Program"],
                x=df_chart["Current"],
                orientation="h",
                marker_color=COLORS["primary"],
            ))

            fig_bar.add_trace(go.Bar(
                name="Additional",
                y=df_chart["Program"],
                x=df_chart["Additional"],
                orientation="h",
                marker_color=COLORS["accent"],
            ))

            fig_bar.update_layout(
                barmode="stack",
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis_title="Patients",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(fig_bar, use_container_width=True)

        with col_chart2:
            st.markdown('<div class="section-header">Resource Utilization</div>', unsafe_allow_html=True)

            # Calcular categorías de utilización por tipo de recurso
            tabla_recursos = resultados["tabla_recursos"]
            if tabla_recursos:
                # Separar recursos por tipo
                rec_prof = [r for r in tabla_recursos if r["tipo"] == "profesional"]
                rec_fis = [r for r in tabla_recursos if r["tipo"] == "fisico"]

                col_donut1, col_donut2 = st.columns(2)

                # Donut de Recursos Profesionales
                with col_donut1:
                    bajo_prof = sum(1 for r in rec_prof if r["pct_total"] < 50)
                    medio_prof = sum(1 for r in rec_prof if 50 <= r["pct_total"] < 80)
                    alto_prof = sum(1 for r in rec_prof if r["pct_total"] >= 80)

                    fig_donut_prof = go.Figure(data=[go.Pie(
                        labels=["Low (<50%)", "Medium (50-80%)", "High (>80%)"],
                        values=[bajo_prof, medio_prof, alto_prof],
                        hole=0.65,
                        marker_colors=[COLORS["success"], COLORS["warning"], COLORS["accent"]],
                        textinfo="value",
                        textposition="outside",
                    )])

                    fig_donut_prof.update_layout(
                        height=280,
                        margin=dict(l=10, r=10, t=30, b=10),
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        annotations=[dict(
                            text=f"<b>{len(rec_prof)}</b><br>Prof.",
                            x=0.5, y=0.5,
                            font_size=14,
                            showarrow=False,
                            font_color=COLORS["primary"],
                        )],
                    )

                    st.plotly_chart(fig_donut_prof, use_container_width=True)
                    st.caption("👤 Professional Resources")

                # Donut de Recursos Físicos
                with col_donut2:
                    bajo_fis = sum(1 for r in rec_fis if r["pct_total"] < 50)
                    medio_fis = sum(1 for r in rec_fis if 50 <= r["pct_total"] < 80)
                    alto_fis = sum(1 for r in rec_fis if r["pct_total"] >= 80)

                    fig_donut_fis = go.Figure(data=[go.Pie(
                        labels=["Low (<50%)", "Medium (50-80%)", "High (>80%)"],
                        values=[bajo_fis, medio_fis, alto_fis],
                        hole=0.65,
                        marker_colors=[COLORS["success"], COLORS["warning"], COLORS["accent"]],
                        textinfo="value",
                        textposition="outside",
                    )])

                    fig_donut_fis.update_layout(
                        height=280,
                        margin=dict(l=10, r=10, t=30, b=10),
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        annotations=[dict(
                            text=f"<b>{len(rec_fis)}</b><br>Physical",
                            x=0.5, y=0.5,
                            font_size=14,
                            showarrow=False,
                            font_color=COLORS["primary"],
                        )],
                    )

                    st.plotly_chart(fig_donut_fis, use_container_width=True)
                    st.caption("🏥 Physical Resources")

                # Leyenda compartida
                text_muted = COLORS["text_muted"]
                st.markdown(
                    f"<div style='text-align:center; font-size:0.8rem; color:{text_muted};'>"
                    "🟢 Low (&lt;50%) &nbsp; 🟡 Medium (50-80%) &nbsp; 🔴 High (&gt;80%)</div>",
                    unsafe_allow_html=True
                )
            else:
                st.info("Run the optimization to see resource utilization.")

        # Gráfico de Top 10 Recursos Más Utilizados
        if tabla_recursos:
            st.markdown('<div class="section-header">Top 10 Most Utilized Resources</div>', unsafe_allow_html=True)

            # Preparar datos para el gráfico
            tabla_data_top = []
            for rec in tabla_recursos:
                tabla_data_top.append({
                    "Resource": rec["nombre"],
                    "Current Usage (%)": rec["pct_actual"],
                    "Total Usage (%)": rec["pct_total"],
                })

            df_top = pd.DataFrame(tabla_data_top).nlargest(10, "Total Usage (%)")
            df_top = df_top.sort_values("Total Usage (%)", ascending=True)  # Para que el mayor quede arriba

            fig_top = go.Figure()

            fig_top.add_trace(go.Bar(
                y=df_top["Resource"],
                x=df_top["Current Usage (%)"],
                name="Current Usage",
                orientation="h",
                marker_color=COLORS["primary"],
            ))

            fig_top.add_trace(go.Bar(
                y=df_top["Resource"],
                x=df_top["Total Usage (%)"] - df_top["Current Usage (%)"],
                name="Additional Usage",
                orientation="h",
                marker_color=COLORS["accent"],
            ))

            fig_top.update_layout(
                barmode="stack",
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis_title="Utilization (%)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            # Línea de referencia al 100%
            fig_top.add_vline(x=100, line_dash="dash", line_color=COLORS["danger"], annotation_text="Maximum capacity")

            st.plotly_chart(fig_top, use_container_width=True)

        # Alertas de recursos excedidos
        if resultados["recursos_excedidos"]:
            st.markdown('<div class="section-header">⚠️ Capacity Alerts</div>', unsafe_allow_html=True)
            for rec in resultados["recursos_excedidos"]:
                st.markdown(f"""
                <div class="resource-alert">
                    <strong>{rec['nombre']}</strong>: exceeded by {rec['excedente']:.1f}h
                    (usage: {rec['uso_actual']:.1f}h / capacity: {rec['capacidad']:.1f}h)
                </div>
                """, unsafe_allow_html=True)

    else:
        # Estado inicial - sin resultados
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="metric-card primary">
                <div class="metric-label">Current Patients</div>
                <div class="metric-value">{total_actuales}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Additional Capacity</div>
                <div class="metric-value" style="color: #94A3B8;">—</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.info("👆 Go to the **Patients** tab to adjust values and run the optimization.")

# =====================================================
# TAB 2: PACIENTES
# =====================================================
with tab2:
    st.markdown('<div class="section-header">Current Patients Configuration</div>', unsafe_allow_html=True)

    # ── Sección: Programas Base ──────────────────────────────────────────────
    st.markdown("#### Base Programs")

    df_base = pd.DataFrame({
        "Program": [_nombres[i] for i in indices_base],
        "Current Patients": [st.session_state.pacientes_actuales[i] for i in indices_base],
        "Priority": [datos_base["prioridad_programas"][i] for i in indices_base],
    })

    df_base_editado = st.data_editor(
        df_base,
        column_config={
            "Program": st.column_config.TextColumn(
                "Treatment Program",
                disabled=True,
                width="large",
            ),
            "Current Patients": st.column_config.NumberColumn(
                "Current Patients",
                min_value=0,
                max_value=100,
                step=1,
                format="%d",
                help="Number of patients currently in the program",
            ),
            "Priority": st.column_config.NumberColumn(
                "Priority",
                disabled=True,
                format="%.2f",
                help="Program priority weight (higher = more important)",
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_pacientes_base",
    )

    # Sync base programs back
    try:
        for local_idx, global_idx in enumerate(indices_base):
            if local_idx < len(df_base_editado):
                val = safe_int(df_base_editado.iloc[local_idx]["Current Patients"], default=0, min_val=0, max_val=100)
                if val != st.session_state.pacientes_actuales[global_idx]:
                    st.session_state.pacientes_actuales[global_idx] = val
                    st.session_state.resultados = None
    except Exception:
        st.warning("Some values could not be processed. Please enter valid numbers (0-100).")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Sección: Extensiones ─────────────────────────────────────────────────
    st.markdown("#### Extensions")
    st.caption("Extensions belong to a base program and represent additional weeks or treatments.")

    df_ext = pd.DataFrame({
        "Extension": [_nombres[i] for i in indices_ext],
        "Base Program": [_programas_dict[_nombres[i]].get("programa_base", "") for i in indices_ext],
        "Current Patients": [st.session_state.pacientes_actuales[i] for i in indices_ext],
        "Priority": [datos_base["prioridad_programas"][i] for i in indices_ext],
    })

    df_ext_editado = st.data_editor(
        df_ext,
        column_config={
            "Extension": st.column_config.TextColumn(
                "Extension",
                disabled=True,
                width="large",
            ),
            "Base Program": st.column_config.TextColumn(
                "Base Program",
                disabled=True,
                width="medium",
            ),
            "Current Patients": st.column_config.NumberColumn(
                "Current Patients",
                min_value=0,
                max_value=100,
                step=1,
                format="%d",
                help="Number of patients currently in this extension",
            ),
            "Priority": st.column_config.NumberColumn(
                "Priority",
                disabled=True,
                format="%.2f",
                help="Program priority weight (higher = more important)",
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_pacientes_ext",
    )

    # Sync extensions back
    try:
        for local_idx, global_idx in enumerate(indices_ext):
            if local_idx < len(df_ext_editado):
                val = safe_int(df_ext_editado.iloc[local_idx]["Current Patients"], default=0, min_val=0, max_val=100)
                if val != st.session_state.pacientes_actuales[global_idx]:
                    st.session_state.pacientes_actuales[global_idx] = val
                    st.session_state.resultados = None
    except Exception:
        st.warning("Some values could not be processed. Please enter valid numbers (0-100).")

    st.markdown("<br>", unsafe_allow_html=True)

    # Botones de acción centrados
    col1, col2, col3, col4 = st.columns([1, 1.2, 1.2, 1])
    with col2:
        calcular = st.button(
            "🔄 Calculate Optimization",
            type="primary",
            use_container_width=True,
        )
    with col3:
        limpiar = st.button(
            "🗑️ Clear All Patients",
            type="secondary",
            use_container_width=True,
        )

    # Acción de limpiar pacientes
    if limpiar:
        st.session_state.pacientes_actuales = [0] * len(datos_base["nombre_programas"])
        st.session_state.resultados = None
        st.rerun()

    if calcular:
        with st.spinner("Running optimization model..."):
            try:
                st.session_state.resultados = ejecutar_optimizacion(st.session_state.pacientes_actuales)
                st.session_state.optimization_just_completed = True
                st.rerun()
            except Exception as e:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%); border: 2px solid #EF4444; border-radius: 12px; padding: 1rem; margin: 1rem 0;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.5rem;">❌</span>
                        <span style="color: #7F1D1D;">
                            <strong>Optimization Error:</strong> {str(e)}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.session_state.resultados = None

    # Mostrar resultados de pacientes adicionales si existen
    if st.session_state.resultados is not None and st.session_state.resultados["estado"] == "Optimal":
        resultados = st.session_state.resultados

        st.markdown("<br>", unsafe_allow_html=True)

        # Banner de éxito solo cuando la optimización se completó SIN recursos excedidos
        # (Si hay bypass de recursos, no mostramos éxito para evitar mensajes contradictorios)
        if st.session_state.get("optimization_just_completed", False):
            if not resultados["recursos_excedidos"]:
                total_adicionales = sum(resultados["pacientes_adicionales"])
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); border: 2px solid #10B981; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2);">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.5rem;">✅</span>
                        <span style="color: #065F46;">
                            <strong>Optimization Completed Successfully!</strong> The model found an optimal solution.
                            You can admit up to <strong>{total_adicionales}</strong> additional patients.
                            Go to <strong>Executive Summary</strong> to see the full results.
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            # Siempre resetear el flag, independientemente de si se mostró o no el banner
            st.session_state.optimization_just_completed = False

        # Advertencia si hay recursos excedidos (mostrar antes de la tabla)
        if resultados["recursos_excedidos"]:
            num_excedidos = len(resultados["recursos_excedidos"])
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); border: 2px solid #F59E0B; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5rem;">⚠️</span>
                    <span style="color: #78350F;">
                        <strong>Attention:</strong> There are {num_excedidos} exceeded resource(s) that were excluded from the model.
                        Results may not be reliable. See the <strong>Resources</strong> tab for more details.
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">Results: Additional Patients</div>', unsafe_allow_html=True)

        df_resultado = pd.DataFrame({
            "Program": resultados["nombre_programas"],
            "Current": st.session_state.pacientes_actuales,
            "Additional": resultados["pacientes_adicionales"],
            "Total": [a + b for a, b in zip(st.session_state.pacientes_actuales, resultados["pacientes_adicionales"])],
        })

        st.dataframe(
            df_resultado,
            column_config={
                "Program": st.column_config.TextColumn("Program", width="large"),
                "Current": st.column_config.NumberColumn("Current", format="%d"),
                "Additional": st.column_config.NumberColumn("Additional", format="%d"),
                "Total": st.column_config.NumberColumn("Projected Total", format="%d"),
            },
            hide_index=True,
            use_container_width=True,
        )

# =====================================================
# TAB 3: RECURSOS
# =====================================================
with tab3:
    # Mostrar total de pacientes actuales
    total_pacientes_actuales = sum(st.session_state.pacientes_actuales)
    st.markdown(f"""
    <div class="metric-card primary" style="margin-bottom: 1.5rem;">
        <div class="metric-label">Total Current Patients</div>
        <div class="metric-value">{total_pacientes_actuales}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.resultados is not None and st.session_state.resultados["estado"] == "Optimal":
        resultados = st.session_state.resultados

        st.markdown('<div class="section-header">Resource Utilization Detail</div>', unsafe_allow_html=True)

        if resultados["tabla_recursos"]:
            # Preparar datos para la tabla
            tabla_data = []
            for rec in resultados["tabla_recursos"]:
                estado = "✅ OK" if rec["ok"] else "⛔ Exceeded"
                tabla_data.append({
                    "Resource": rec["nombre"],
                    "Capacity (h)": rec["capacidad"],
                    "Current Usage (h)": rec["uso_actual"],
                    "Current Usage (%)": rec["pct_actual"],
                    "Additional Usage (h)": rec["uso_adicional"],
                    "Total Usage (h)": rec["uso_total"],
                    "Total Usage (%)": rec["pct_total"],
                    "Status": estado,
                })

            df_recursos = pd.DataFrame(tabla_data)

            # Filtros
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                filtro_uso = st.selectbox(
                    "Filter by usage level:",
                    ["All", "High (>80%)", "Medium (50-80%)", "Low (<50%)"],
                )

            # Aplicar filtro
            if filtro_uso == "High (>80%)":
                df_recursos = df_recursos[df_recursos["Total Usage (%)"] >= 80]
            elif filtro_uso == "Medium (50-80%)":
                df_recursos = df_recursos[(df_recursos["Total Usage (%)"] >= 50) & (df_recursos["Total Usage (%)"] < 80)]
            elif filtro_uso == "Low (<50%)":
                df_recursos = df_recursos[df_recursos["Total Usage (%)"] < 50]

            st.dataframe(
                df_recursos,
                column_config={
                    "Resource": st.column_config.TextColumn("Resource", width="medium"),
                    "Capacity (h)": st.column_config.NumberColumn("Capacity", format="%.1f"),
                    "Current Usage (h)": st.column_config.NumberColumn("Current Usage", format="%.1f"),
                    "Current Usage (%)": st.column_config.ProgressColumn(
                        "% Current",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%",
                    ),
                    "Additional Usage (h)": st.column_config.NumberColumn("Add. Usage", format="%.1f"),
                    "Total Usage (h)": st.column_config.NumberColumn("Total Usage", format="%.1f"),
                    "Total Usage (%)": st.column_config.ProgressColumn(
                        "% Total",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%",
                    ),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                },
                hide_index=True,
                use_container_width=True,
            )

        # Recursos excedidos
        if resultados["recursos_excedidos"]:
            st.markdown('<div class="section-header">⚠️ Exceeded Resources (Not included in optimization)</div>', unsafe_allow_html=True)

            df_excedidos = pd.DataFrame(resultados["recursos_excedidos"])
            df_excedidos.columns = ["Resource", "Current Usage (h)", "Capacity (h)", "Excess (h)"]

            st.dataframe(
                df_excedidos,
                column_config={
                    "Resource": st.column_config.TextColumn("Resource", width="medium"),
                    "Current Usage (h)": st.column_config.NumberColumn("Current Usage", format="%.1f"),
                    "Capacity (h)": st.column_config.NumberColumn("Capacity", format="%.1f"),
                    "Excess (h)": st.column_config.NumberColumn("Excess", format="%.1f"),
                },
                hide_index=True,
                use_container_width=True,
            )
    else:
        st.info("👆 Go to the **Patients** tab to run the optimization and see resource details.")

# =====================================================
# TAB 4: VERIFICAR ADMISIÓN
# =====================================================
with tab4:
    st.markdown('<div class="section-header">Verify Admission Feasibility</div>', unsafe_allow_html=True)
    st.markdown(
        "Verify if it is possible to admit a specific number of new patients per program, "
        "considering the current resource capacity."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Formulario de solicitudes
    st.markdown("#### Admission Requests")

    # Crear columnas para el formulario
    col_form1, col_form2 = st.columns([2, 1])

    with col_form1:
        # Selector de programa (agrupado: base programs primero, luego extensions con prefijo)
        _opciones_verificar = indices_base + indices_ext

        def _fmt_programa_verificar(idx):
            name = datos_base["nombre_programas"][idx]
            prog = _programas_dict[name]
            if prog.get("tipo") == "extension":
                return f"  \u21b3 {name}  ({prog.get('programa_base', '')})"
            return name

        programa_seleccionado = st.selectbox(
            "Select program:",
            options=_opciones_verificar,
            format_func=_fmt_programa_verificar,
            key="programa_verificar",
        )

    with col_form2:
        # Cantidad de pacientes
        cantidad_pacientes = st.number_input(
            "Number of patients:",
            min_value=1,
            max_value=50,
            value=1,
            step=1,
            key="cantidad_verificar",
        )

    # Inicializar lista de solicitudes en session state
    if "solicitudes_admision" not in st.session_state:
        st.session_state.solicitudes_admision = {}

    # Botones para agregar/limpiar solicitudes
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

    with col_btn1:
        if st.button("➕ Add", use_container_width=True):
            # Validar cantidad antes de agregar
            cantidad_validada = safe_int(cantidad_pacientes, default=1, min_val=1, max_val=50)
            programa_validado = safe_int(programa_seleccionado, default=0, min_val=0, max_val=len(datos_base["nombre_programas"])-1)
            st.session_state.solicitudes_admision[programa_validado] = cantidad_validada
            st.rerun()

    with col_btn2:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.solicitudes_admision = {}
            st.session_state.resultado_verificacion = None
            st.rerun()

    # Mostrar solicitudes actuales
    if st.session_state.solicitudes_admision:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Pending Requests to Verify")

        solicitudes_df = pd.DataFrame([
            {
                "Program": datos_base["nombre_programas"][idx],
                "Requested Patients": cant,
            }
            for idx, cant in st.session_state.solicitudes_admision.items()
        ])

        st.dataframe(
            solicitudes_df,
            column_config={
                "Program": st.column_config.TextColumn("Program", width="large"),
                "Requested Patients": st.column_config.NumberColumn("Patients", format="%d"),
            },
            hide_index=True,
            use_container_width=True,
        )

        total_solicitados = sum(st.session_state.solicitudes_admision.values())
        st.markdown(f"**Total requested patients:** {total_solicitados}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Botón de verificación
        col_ver1, col_ver2, col_ver3 = st.columns([1, 2, 1])
        with col_ver2:
            verificar_btn = st.button(
                "🔍 Verify Feasibility",
                type="primary",
                use_container_width=True,
            )

        if verificar_btn:
            with st.spinner("Verifying feasibility..."):
                try:
                    resultado_verificacion = verificar_admision(
                        st.session_state.pacientes_actuales,
                        st.session_state.solicitudes_admision,
                    )
                    st.session_state.resultado_verificacion = resultado_verificacion
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error verifying feasibility: {str(e)}")
                    st.session_state.resultado_verificacion = None

    # Mostrar resultados de verificación
    if "resultado_verificacion" in st.session_state and st.session_state.resultado_verificacion:
        resultado = st.session_state.resultado_verificacion

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### Verification Result")

        # Mostrar resultado general con banners estilizados
        if resultado["factible"]:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); border: 2px solid #10B981; border-radius: 12px; padding: 1rem; margin: 1rem 0; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2);">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5rem;">✅</span>
                    <span style="color: #065F46;">
                        <strong>FEASIBLE:</strong> It is possible to admit all requested patients with current capacity.
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%); border: 2px solid #EF4444; border-radius: 12px; padding: 1rem; margin: 1rem 0; box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.2);">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5rem;">❌</span>
                    <span style="color: #7F1D1D;">
                        <strong>NOT FEASIBLE:</strong> It is not possible to admit all requested patients with current capacity.
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Detalle por solicitud
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Detail by Program")

        for detalle in resultado["solicitudes_detalle"]:
            pacientes_actuales_programa = st.session_state.pacientes_actuales[detalle["programa_idx"]]
            if detalle["factible"]:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #D1FAE5 0%, #ECFDF5 100%); border: 1px solid #10B981; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.1);">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.2rem;">✅</span>
                        <strong style="color: #065F46;">{detalle['programa']}</strong>
                    </div>
                    <div style="color: #047857; font-size: 0.9rem;">
                        Current: <strong>{pacientes_actuales_programa}</strong> | Requested: <strong>{detalle['cantidad_solicitada']}</strong> | Maximum admissible: <strong>{detalle['max_admisible']}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #FEE2E2 0%, #FEF2F2 100%); border: 1px solid #EF4444; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; box-shadow: 0 2px 4px rgba(239, 68, 68, 0.1);">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.2rem;">❌</span>
                        <strong style="color: #7F1D1D;">{detalle['programa']}</strong>
                    </div>
                    <div style="color: #991B1B; font-size: 0.9rem;">
                        Current: <strong>{pacientes_actuales_programa}</strong> | Requested: <strong>{detalle['cantidad_solicitada']}</strong> | Maximum admissible: <strong>{detalle['max_admisible']}</strong> | Deficit: <strong>{detalle['deficit']}</strong>
                    </div>
                    <div style="color: #B91C1C; font-size: 0.85rem; font-style: italic; margin-top: 0.3rem;">
                        Limiting resource: {detalle['recurso_limitante']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Recursos limitantes (si hay)
        if resultado["recursos_limitantes"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Resources Exceeding Capacity")

            df_limitantes = pd.DataFrame(resultado["recursos_limitantes"])
            df_limitantes = df_limitantes.rename(columns={
                "nombre": "Resource",
                "tipo": "Type",
                "capacidad": "Capacity (h)",
                "uso_actual": "Current Usage (h)",
                "uso_adicional_requerido": "Additional Usage (h)",
                "uso_total_proyectado": "Total Usage (h)",
                "excedente": "Excess (h)",
                "pct_uso_proyectado": "% Projected",
            })

            st.dataframe(
                df_limitantes,
                column_config={
                    "Resource": st.column_config.TextColumn("Resource", width="medium"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "Capacity (h)": st.column_config.NumberColumn("Capacity", format="%.1f"),
                    "Current Usage (h)": st.column_config.NumberColumn("Current Usage", format="%.1f"),
                    "Additional Usage (h)": st.column_config.NumberColumn("Add. Usage", format="%.1f"),
                    "Total Usage (h)": st.column_config.NumberColumn("Total Usage", format="%.1f"),
                    "Excess (h)": st.column_config.NumberColumn("Excess", format="%.1f"),
                    "% Projected": st.column_config.NumberColumn(
                        "% Projected",
                        format="%.1f%% ⚠️",
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )

        # Impacto en recursos (top 15)
        if resultado["impacto_recursos"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Resource Impact (Top 15 most affected)")

            df_impacto = pd.DataFrame(resultado["impacto_recursos"][:15])

            # Crear gráfico de barras de impacto
            fig_impacto = go.Figure()

            df_impacto_sorted = df_impacto.sort_values("pct_proyectado", ascending=True)

            fig_impacto.add_trace(go.Bar(
                y=df_impacto_sorted["nombre"],
                x=df_impacto_sorted["pct_actual"],
                name="Current Usage",
                orientation="h",
                marker_color=COLORS["primary"],
            ))

            fig_impacto.add_trace(go.Bar(
                y=df_impacto_sorted["nombre"],
                x=df_impacto_sorted["pct_proyectado"] - df_impacto_sorted["pct_actual"],
                name="Additional Usage",
                orientation="h",
                marker_color=COLORS["accent"],
            ))

            fig_impacto.update_layout(
                barmode="stack",
                height=450,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis_title="Utilization (%)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            # Línea de referencia al 100%
            fig_impacto.add_vline(x=100, line_dash="dash", line_color=COLORS["danger"], annotation_text="Maximum capacity")

            st.plotly_chart(fig_impacto, use_container_width=True)

    else:
        if not st.session_state.solicitudes_admision:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("👆 Add admission requests by selecting a program and the number of patients, then click **Add**.")

# =====================================================
# TAB 5: ADMINISTRACIÓN (solo visible para admin)
# =====================================================
if st.session_state.admin_mode:
    with tab5:
        st.markdown('<div class="section-header">System Configuration</div>', unsafe_allow_html=True)
        st.markdown(
            "Edit treatment programs, professional resources, and physical resources. "
            "Changes will be saved permanently to the system."
        )

        # Inicializar datos editables en session_state si no existen
        if "admin_programas" not in st.session_state:
            import copy
            st.session_state.admin_programas = copy.deepcopy(datos_base["programas"])
        if "admin_recursos_prof" not in st.session_state:
            import copy
            st.session_state.admin_recursos_prof = copy.deepcopy(datos_base["recursos_profesionales"])
        if "admin_recursos_fis" not in st.session_state:
            import copy
            st.session_state.admin_recursos_fis = copy.deepcopy(datos_base["recursos_fisicos"])

        st.markdown("<br>", unsafe_allow_html=True)

        # === SECCIÓN 1: RECURSOS PROFESIONALES ===
        st.markdown("#### Professional Resources")
        st.caption("Edit number of people and capacity per person. Total capacity is calculated automatically.")

        # Crear DataFrame para edición de recursos profesionales
        df_rec_prof = pd.DataFrame([
            {
                "Department": rec["departamento"],
                "Role": rec["nombre"],
                "People": rec["num_personas"],
                "Capacity/Person (h/week)": rec["cap_semanal_por_persona"],
                "Total Capacity (h/week)": rec["num_personas"] * rec["cap_semanal_por_persona"],
            }
            for rec in st.session_state.admin_recursos_prof
        ])

        df_rec_prof_editado = st.data_editor(
            df_rec_prof,
            column_config={
                "Department": st.column_config.TextColumn(
                    "Department",
                    disabled=True,
                    width="medium",
                ),
                "Role": st.column_config.TextColumn(
                    "Role",
                    disabled=True,
                    width="large",
                ),
                "People": st.column_config.NumberColumn(
                    "# People",
                    min_value=1,
                    max_value=100,
                    step=1,
                    format="%d",
                    help="Number of people in this role",
                ),
                "Capacity/Person (h/week)": st.column_config.NumberColumn(
                    "Cap/Person (h/week)",
                    min_value=0.0,
                    max_value=200.0,
                    step=0.5,
                    format="%.2f",
                    help="Weekly capacity per person in hours",
                ),
                "Total Capacity (h/week)": st.column_config.NumberColumn(
                    "Total Cap (h/week)",
                    disabled=True,
                    format="%.1f",
                    help="Total = People × Capacity/Person (auto-calculated)",
                ),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key="editor_rec_prof_admin",
        )

        # Actualizar session_state con cambios
        for i, row in df_rec_prof_editado.iterrows():
            st.session_state.admin_recursos_prof[i]["num_personas"] = safe_int(row["People"], default=1, min_val=1)
            st.session_state.admin_recursos_prof[i]["cap_semanal_por_persona"] = safe_float(row["Capacity/Person (h/week)"], default=40.0, min_val=0.0)
            st.session_state.admin_recursos_prof[i]["cap_semanal_total"] = (
                st.session_state.admin_recursos_prof[i]["num_personas"] *
                st.session_state.admin_recursos_prof[i]["cap_semanal_por_persona"]
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # === SECCIÓN 2: RECURSOS FÍSICOS ===
        st.markdown("#### Physical Resources")
        st.caption("Edit number of units and capacity per unit. Total capacity is calculated automatically.")

        # Crear DataFrame para edición de recursos físicos
        df_rec_fis = pd.DataFrame([
            {
                "Department": rec["departamento"],
                "Resource": rec["nombre"],
                "Units": rec["num_unidades"],
                "Capacity/Unit (h/week)": rec["cap_semanal_por_unidad"],
                "Total Capacity (h/week)": rec["num_unidades"] * rec["cap_semanal_por_unidad"],
            }
            for rec in st.session_state.admin_recursos_fis
        ])

        df_rec_fis_editado = st.data_editor(
            df_rec_fis,
            column_config={
                "Department": st.column_config.TextColumn(
                    "Department",
                    disabled=True,
                    width="medium",
                ),
                "Resource": st.column_config.TextColumn(
                    "Resource",
                    disabled=True,
                    width="large",
                ),
                "Units": st.column_config.NumberColumn(
                    "# Units",
                    min_value=1,
                    max_value=100,
                    step=1,
                    format="%d",
                    help="Number of units available",
                ),
                "Capacity/Unit (h/week)": st.column_config.NumberColumn(
                    "Cap/Unit (h/week)",
                    min_value=0.0,
                    max_value=500.0,
                    step=0.5,
                    format="%.2f",
                    help="Weekly capacity per unit in hours",
                ),
                "Total Capacity (h/week)": st.column_config.NumberColumn(
                    "Total Cap (h/week)",
                    disabled=True,
                    format="%.1f",
                    help="Total = Units × Capacity/Unit (auto-calculated)",
                ),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key="editor_rec_fis_admin",
        )

        # Actualizar session_state con cambios
        for i, row in df_rec_fis_editado.iterrows():
            st.session_state.admin_recursos_fis[i]["num_unidades"] = safe_int(row["Units"], default=1, min_val=1)
            st.session_state.admin_recursos_fis[i]["cap_semanal_por_unidad"] = safe_float(row["Capacity/Unit (h/week)"], default=40.0, min_val=0.0)
            st.session_state.admin_recursos_fis[i]["cap_semanal_total"] = (
                st.session_state.admin_recursos_fis[i]["num_unidades"] *
                st.session_state.admin_recursos_fis[i]["cap_semanal_por_unidad"]
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # === SECCIÓN 3: PROGRAMAS Y ACTIVIDADES ===
        st.markdown("#### Programs and Activities")
        st.caption("Select a program to edit its duration and activities")

        # Selector de programa (agrupado: base programs primero, luego extensions)
        programa_nombres = list(st.session_state.admin_programas.keys())
        _admin_base = [n for n in programa_nombres if st.session_state.admin_programas[n].get("tipo") == "programa"]
        _admin_ext = [n for n in programa_nombres if st.session_state.admin_programas[n].get("tipo") == "extension"]
        _admin_opciones = _admin_base + _admin_ext

        def _fmt_admin_programa(name):
            prog = st.session_state.admin_programas[name]
            if prog.get("tipo") == "extension":
                return f"  \u21b3 {name}  ({prog.get('programa_base', '')})"
            return name

        programa_seleccionado = st.selectbox(
            "Select Program:",
            options=_admin_opciones,
            format_func=_fmt_admin_programa,
            key="admin_programa_selector",
        )

        if programa_seleccionado:
            prog_data = st.session_state.admin_programas[programa_seleccionado]

            # Editar duración del programa
            col_dur1, col_dur2 = st.columns([2, 1])
            with col_dur1:
                st.markdown(f"**Program Duration**")
                st.caption("Number of days for the treatment program")
            with col_dur2:
                nueva_duracion = st.number_input(
                    "Duration (days)",
                    min_value=1,
                    max_value=90,
                    value=prog_data["duracion_dias"],
                    step=1,
                    key=f"duracion_{programa_seleccionado}",
                    label_visibility="collapsed",
                )
                st.session_state.admin_programas[programa_seleccionado]["duracion_dias"] = nueva_duracion

            st.markdown("<br>", unsafe_allow_html=True)

            # Tabla de actividades
            st.markdown(f"**Activities for {programa_seleccionado}**")
            st.caption("Edit quantity, duration and resources for each activity.")

            # Obtener listas de recursos válidos
            recursos_prof_validos = [r["nombre"] for r in st.session_state.admin_recursos_prof]
            recursos_fis_validos = [r["nombre"] for r in st.session_state.admin_recursos_fis]

            # Crear DataFrame de actividades (recursos prof como read-only para mostrar)
            df_actividades = pd.DataFrame([
                {
                    "Activity": act["nombre"],
                    "Type": act["tipo"],
                    "Quantity": act["cantidad"],
                    "Duration (min)": act["duracion_min"],
                    "Physical Resource": act["recurso_fis"] if act["recurso_fis"] else "",
                }
                for act in prog_data["actividades"]
            ])

            df_actividades_editado = st.data_editor(
                df_actividades,
                column_config={
                    "Activity": st.column_config.TextColumn(
                        "Activity",
                        disabled=True,
                        width="large",
                    ),
                    "Type": st.column_config.TextColumn(
                        "Type",
                        disabled=True,
                        width="small",
                    ),
                    "Quantity": st.column_config.NumberColumn(
                        "Qty/Program",
                        min_value=0,
                        max_value=100,
                        step=1,
                        format="%d",
                        help="Number of times this activity occurs during the entire program stay",
                    ),
                    "Duration (min)": st.column_config.NumberColumn(
                        "Duration (min)",
                        min_value=1,
                        max_value=1440,
                        step=5,
                        format="%d",
                        help="Duration of each session in minutes",
                    ),
                    "Physical Resource": st.column_config.SelectboxColumn(
                        "Physical Resource",
                        options=[""] + recursos_fis_validos,
                        help="Select a physical resource or leave empty for None",
                        width="medium",
                    ),
                },
                hide_index=True,
                use_container_width=True,
                num_rows="fixed",
                key=f"editor_actividades_{programa_seleccionado}",
            )

            # Actualizar session_state con cambios de la tabla
            for i, row in df_actividades_editado.iterrows():
                st.session_state.admin_programas[programa_seleccionado]["actividades"][i]["cantidad"] = safe_int(row["Quantity"], default=1, min_val=0)
                st.session_state.admin_programas[programa_seleccionado]["actividades"][i]["duracion_min"] = safe_int(row["Duration (min)"], default=30, min_val=1)
                phys_resource = safe_string(row["Physical Resource"], default="")
                st.session_state.admin_programas[programa_seleccionado]["actividades"][i]["recurso_fis"] = phys_resource if phys_resource else None

            st.markdown("<br>", unsafe_allow_html=True)

            # Editor de recursos profesionales por actividad
            st.markdown("**Edit Professional Resources per Activity**")
            st.caption("Select an activity to assign professional resources using the multi-select below.")

            # Selector de actividad
            actividad_nombres = [act["nombre"] for act in prog_data["actividades"]]
            actividad_seleccionada = st.selectbox(
                "Select Activity:",
                options=range(len(actividad_nombres)),
                format_func=lambda x: actividad_nombres[x],
                key=f"admin_actividad_selector_{programa_seleccionado}",
            )

            if actividad_seleccionada is not None:
                act_actual = st.session_state.admin_programas[programa_seleccionado]["actividades"][actividad_seleccionada]

                # Multiselect para recursos profesionales
                recursos_actuales = act_actual.get("recursos_prof", [])
                # Asegurar que los recursos actuales existan en la lista válida
                recursos_actuales_validos = [r for r in recursos_actuales if r in recursos_prof_validos]

                nuevos_recursos = st.multiselect(
                    "Professional Resources:",
                    options=recursos_prof_validos,
                    default=recursos_actuales_validos,
                    key=f"multiselect_prof_{programa_seleccionado}_{actividad_seleccionada}",
                    help="Select one or more professional resources required for this activity",
                )

                # Actualizar los recursos profesionales en session_state
                st.session_state.admin_programas[programa_seleccionado]["actividades"][actividad_seleccionada]["recursos_prof"] = nuevos_recursos

                # Mostrar resumen de la actividad seleccionada
                st.info(f"**{act_actual['nombre']}**: {len(nuevos_recursos)} professional resource(s) assigned")

        st.markdown("<br>", unsafe_allow_html=True)

        # === BOTÓN GUARDAR CON CONFIRMACIÓN ===
        if "confirmar_guardado" not in st.session_state:
            st.session_state.confirmar_guardado = False

        col_save1, col_save2, col_save3 = st.columns([1, 2, 1])

        if not st.session_state.confirmar_guardado:
            with col_save2:
                guardar_btn = st.button(
                    "💾 Save All Changes",
                    type="primary",
                    use_container_width=True,
                )
            if guardar_btn:
                st.session_state.confirmar_guardado = True
                st.rerun()
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); border: 2px solid #F59E0B; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem;">
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <span style="font-size: 1.75rem;">⚠️</span>
                    <div>
                        <strong style="color: #92400E; font-size: 1.1rem;">Confirm Save</strong><br>
                        <span style="color: #78350F; font-size: 0.95rem;">
                            You are about to permanently save changes to treatment programs,
                            professional resources, and physical resources.<br>
                            <strong>This action cannot be undone.</strong> Are you sure you want to continue?
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_confirm, col_cancel = st.columns(2)

            with col_confirm:
                confirmar_btn = st.button(
                    "✅ Yes, Save Changes",
                    type="primary",
                    use_container_width=True,
                )

            with col_cancel:
                cancelar_btn = st.button(
                    "❌ Cancel",
                    use_container_width=True,
                )

            if confirmar_btn:
                with st.spinner("Saving changes..."):
                    try:
                        guardar_datos_sanoviv(
                            st.session_state.admin_programas,
                            st.session_state.admin_recursos_prof,
                            st.session_state.admin_recursos_fis,
                        )
                        st.session_state.confirmar_guardado = False
                        # Limpiar datos de admin para recargar desde archivo
                        del st.session_state.admin_programas
                        del st.session_state.admin_recursos_prof
                        del st.session_state.admin_recursos_fis
                        st.success("✅ Changes saved successfully. Restart the application to see the updated data.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error saving changes: {str(e)}")
                        st.session_state.confirmar_guardado = False

            if cancelar_btn:
                st.session_state.confirmar_guardado = False
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.warning(
            "**Important:** After saving changes, you need to restart the application "
            "(refresh the page) for the new data to take effect."
        )

# === FOOTER ===
st.markdown(f"""
<div class="footer">
    <span class="logo">ARK<span class="dot">●</span>DE</span> × Sanoviv Medical Institute<br>
    Patient Capacity Optimization System
</div>
""", unsafe_allow_html=True)
