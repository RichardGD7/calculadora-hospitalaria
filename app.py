# -*- coding: utf-8 -*-
"""app.py - Interfaz Streamlit para el optimizador de pacientes de Sanoviv."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from optimizador import obtener_datos_base, ejecutar_optimizacion, verificar_admision

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
    page_title="Sanoviv - Optimización de Pacientes",
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

# === HEADER PRINCIPAL ===
st.markdown("""
<div class="main-header">
    <h1>Sanoviv - Optimización de Capacidad</h1>
    <p>Sistema de planificación de pacientes por programa de tratamiento</p>
</div>
""", unsafe_allow_html=True)

# === CARGAR DATOS ===
datos_base = obtener_datos_base()

# Inicializar estado de sesión
if "pacientes_actuales" not in st.session_state:
    st.session_state.pacientes_actuales = datos_base["pacientes_actuales"].copy()

if "resultados" not in st.session_state:
    st.session_state.resultados = None

if "resultado_verificacion" not in st.session_state:
    st.session_state.resultado_verificacion = None

# === SINCRONIZAR DATOS DEL EDITOR (antes de renderizar pestañas) ===
# Esto asegura que los cambios del data_editor se reflejen en todas las pestañas
if "editor_pacientes" in st.session_state:
    editor_data = st.session_state.editor_pacientes
    if "edited_rows" in editor_data and editor_data["edited_rows"]:
        # Aplicar cambios editados
        for row_idx, changes in editor_data["edited_rows"].items():
            if "Pacientes Actuales" in changes:
                st.session_state.pacientes_actuales[int(row_idx)] = changes["Pacientes Actuales"]
        # Limpiar resultados anteriores ya que los datos cambiaron
        st.session_state.resultados = None

# === PESTAÑAS ===
tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumen Ejecutivo", "👥 Pacientes", "📈 Recursos", "🔍 Verificar Admisión"])

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
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card primary">
                <div class="metric-label">Pacientes Actuales</div>
                <div class="metric-value">{total_actuales}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Capacidad Adicional</div>
                <div class="metric-value accent">+{total_adicionales}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card success">
                <div class="metric-label">Total Proyectado</div>
                <div class="metric-value">{total_proyectado}</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Valor Ponderado</div>
                <div class="metric-value">{resultados['total_ponderado']:.1f}</div>
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
                        <strong style="color: #92400E; font-size: 1.1rem;">Advertencia: Resultados con recursos excedidos</strong><br>
                        <span style="color: #78350F; font-size: 0.95rem;">
                            Hay <strong>{num_excedidos} recurso(s)</strong> que ya exceden su capacidad con los pacientes actuales:
                            <em>{nombres_excedidos}</em>.<br>
                            Estos recursos fueron <strong>excluidos del modelo de optimización</strong>.
                            Los pacientes adicionales sugeridos podrían empeorar aún más esta situación.
                            <strong>Se recomienda resolver primero la sobresaturación actual.</strong>
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Gráficos lado a lado
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown('<div class="section-header">Pacientes por Programa</div>', unsafe_allow_html=True)

            # Gráfico de barras comparativo - ordenado por total de mayor a menor
            df_chart = pd.DataFrame({
                "Programa": resultados["nombre_programas"],
                "Actuales": st.session_state.pacientes_actuales,
                "Adicionales": resultados["pacientes_adicionales"],
            })
            df_chart["Total"] = df_chart["Actuales"] + df_chart["Adicionales"]
            df_chart = df_chart.sort_values("Total", ascending=True)  # ascending=True para que el mayor quede arriba en barras horizontales

            fig_bar = go.Figure()

            fig_bar.add_trace(go.Bar(
                name="Actuales",
                y=df_chart["Programa"],
                x=df_chart["Actuales"],
                orientation="h",
                marker_color=COLORS["primary"],
            ))

            fig_bar.add_trace(go.Bar(
                name="Adicionales",
                y=df_chart["Programa"],
                x=df_chart["Adicionales"],
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
                xaxis_title="Pacientes",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(fig_bar, use_container_width=True)

        with col_chart2:
            st.markdown('<div class="section-header">Utilización de Recursos</div>', unsafe_allow_html=True)

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
                        labels=["Bajo (<50%)", "Medio (50-80%)", "Alto (>80%)"],
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
                    st.caption("👤 Recursos Profesionales")

                # Donut de Recursos Físicos
                with col_donut2:
                    bajo_fis = sum(1 for r in rec_fis if r["pct_total"] < 50)
                    medio_fis = sum(1 for r in rec_fis if 50 <= r["pct_total"] < 80)
                    alto_fis = sum(1 for r in rec_fis if r["pct_total"] >= 80)

                    fig_donut_fis = go.Figure(data=[go.Pie(
                        labels=["Bajo (<50%)", "Medio (50-80%)", "Alto (>80%)"],
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
                            text=f"<b>{len(rec_fis)}</b><br>Físicos",
                            x=0.5, y=0.5,
                            font_size=14,
                            showarrow=False,
                            font_color=COLORS["primary"],
                        )],
                    )

                    st.plotly_chart(fig_donut_fis, use_container_width=True)
                    st.caption("🏥 Recursos Físicos")

                # Leyenda compartida
                text_muted = COLORS["text_muted"]
                st.markdown(
                    f"<div style='text-align:center; font-size:0.8rem; color:{text_muted};'>"
                    "🟢 Bajo (&lt;50%) &nbsp; 🟡 Medio (50-80%) &nbsp; 🔴 Alto (&gt;80%)</div>",
                    unsafe_allow_html=True
                )
            else:
                st.info("Ejecuta la optimización para ver la utilización de recursos.")

        # Gráfico de Top 10 Recursos Más Utilizados
        if tabla_recursos:
            st.markdown('<div class="section-header">Top 10 Recursos Más Utilizados</div>', unsafe_allow_html=True)

            # Preparar datos para el gráfico
            tabla_data_top = []
            for rec in tabla_recursos:
                tabla_data_top.append({
                    "Recurso": rec["nombre"],
                    "Uso Actual (%)": rec["pct_actual"],
                    "Uso Total (%)": rec["pct_total"],
                })

            df_top = pd.DataFrame(tabla_data_top).nlargest(10, "Uso Total (%)")
            df_top = df_top.sort_values("Uso Total (%)", ascending=True)  # Para que el mayor quede arriba

            fig_top = go.Figure()

            fig_top.add_trace(go.Bar(
                y=df_top["Recurso"],
                x=df_top["Uso Actual (%)"],
                name="Uso Actual",
                orientation="h",
                marker_color=COLORS["primary"],
            ))

            fig_top.add_trace(go.Bar(
                y=df_top["Recurso"],
                x=df_top["Uso Total (%)"] - df_top["Uso Actual (%)"],
                name="Uso Adicional",
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
                xaxis_title="Utilización (%)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            # Línea de referencia al 100%
            fig_top.add_vline(x=100, line_dash="dash", line_color=COLORS["danger"], annotation_text="Capacidad máxima")

            st.plotly_chart(fig_top, use_container_width=True)

        # Alertas de recursos excedidos
        if resultados["recursos_excedidos"]:
            st.markdown('<div class="section-header">⚠️ Alertas de Capacidad</div>', unsafe_allow_html=True)
            for rec in resultados["recursos_excedidos"]:
                st.markdown(f"""
                <div class="resource-alert">
                    <strong>{rec['nombre']}</strong>: excedido por {rec['excedente']:.1f}h
                    (uso: {rec['uso_actual']:.1f}h / capacidad: {rec['capacidad']:.1f}h)
                </div>
                """, unsafe_allow_html=True)

    else:
        # Estado inicial - sin resultados
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="metric-card primary">
                <div class="metric-label">Pacientes Actuales</div>
                <div class="metric-value">{total_actuales}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Capacidad Adicional</div>
                <div class="metric-value" style="color: #94A3B8;">—</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.info("👆 Ve a la pestaña **Pacientes** para ajustar los valores y ejecutar la optimización.")

# =====================================================
# TAB 2: PACIENTES
# =====================================================
with tab2:
    st.markdown('<div class="section-header">Configuración de Pacientes Actuales</div>', unsafe_allow_html=True)

    # Crear DataFrame para edición
    df_pacientes = pd.DataFrame({
        "Programa": datos_base["nombre_programas"],
        "Pacientes Actuales": st.session_state.pacientes_actuales,
        "Prioridad": datos_base["prioridad_programas"],
    })

    # Editor de datos
    df_editado = st.data_editor(
        df_pacientes,
        column_config={
            "Programa": st.column_config.TextColumn(
                "Programa de Tratamiento",
                disabled=True,
                width="large",
            ),
            "Pacientes Actuales": st.column_config.NumberColumn(
                "Pacientes Actuales",
                min_value=0,
                max_value=100,
                step=1,
                format="%d",
                help="Número de pacientes actualmente en el programa",
            ),
            "Prioridad": st.column_config.NumberColumn(
                "Prioridad",
                disabled=True,
                format="%.2f",
                help="Peso de prioridad del programa (mayor = más importante)",
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_pacientes",
    )

    # Actualizar estado con los valores editados (solo si cambió)
    nuevos_valores = df_editado["Pacientes Actuales"].tolist()
    if nuevos_valores != st.session_state.pacientes_actuales:
        st.session_state.pacientes_actuales = nuevos_valores
        # Limpiar resultados anteriores ya que los datos cambiaron
        st.session_state.resultados = None

    st.markdown("<br>", unsafe_allow_html=True)

    # Botón de cálculo centrado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        calcular = st.button(
            "🔄 Calcular Optimización",
            type="primary",
            use_container_width=True,
        )

    if calcular:
        with st.spinner("Ejecutando modelo de optimización..."):
            try:
                st.session_state.resultados = ejecutar_optimizacion(st.session_state.pacientes_actuales)
                st.success("✅ Optimización completada. Ve a **Resumen Ejecutivo** para ver los resultados.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al ejecutar la optimización: {str(e)}")
                st.session_state.resultados = None

    # Mostrar resultados de pacientes adicionales si existen
    if st.session_state.resultados is not None and st.session_state.resultados["estado"] == "Optimal":
        resultados = st.session_state.resultados

        st.markdown("<br>", unsafe_allow_html=True)

        # Advertencia si hay recursos excedidos (mostrar antes de la tabla)
        if resultados["recursos_excedidos"]:
            num_excedidos = len(resultados["recursos_excedidos"])
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); border: 2px solid #F59E0B; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5rem;">⚠️</span>
                    <span style="color: #78350F;">
                        <strong>Atención:</strong> Hay {num_excedidos} recurso(s) excedido(s) que fueron excluidos del modelo.
                        Los resultados podrían no ser confiables. Ver pestaña <strong>Recursos</strong> para más detalles.
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">Resultados: Pacientes Adicionales</div>', unsafe_allow_html=True)

        df_resultado = pd.DataFrame({
            "Programa": resultados["nombre_programas"],
            "Actuales": st.session_state.pacientes_actuales,
            "Adicionales": resultados["pacientes_adicionales"],
            "Total": [a + b for a, b in zip(st.session_state.pacientes_actuales, resultados["pacientes_adicionales"])],
        })

        st.dataframe(
            df_resultado,
            column_config={
                "Programa": st.column_config.TextColumn("Programa", width="large"),
                "Actuales": st.column_config.NumberColumn("Actuales", format="%d"),
                "Adicionales": st.column_config.NumberColumn("Adicionales", format="%d"),
                "Total": st.column_config.NumberColumn("Total Proyectado", format="%d"),
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
        <div class="metric-label">Total Pacientes Actuales</div>
        <div class="metric-value">{total_pacientes_actuales}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.resultados is not None and st.session_state.resultados["estado"] == "Optimal":
        resultados = st.session_state.resultados

        st.markdown('<div class="section-header">Detalle de Utilización de Recursos</div>', unsafe_allow_html=True)

        if resultados["tabla_recursos"]:
            # Preparar datos para la tabla
            tabla_data = []
            for rec in resultados["tabla_recursos"]:
                estado = "✅ OK" if rec["ok"] else "⛔ Excedido"
                tabla_data.append({
                    "Recurso": rec["nombre"],
                    "Capacidad (h)": rec["capacidad"],
                    "Uso Actual (h)": rec["uso_actual"],
                    "Uso Actual (%)": rec["pct_actual"],
                    "Uso Adicional (h)": rec["uso_adicional"],
                    "Uso Total (h)": rec["uso_total"],
                    "Uso Total (%)": rec["pct_total"],
                    "Estado": estado,
                })

            df_recursos = pd.DataFrame(tabla_data)

            # Filtros
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                filtro_uso = st.selectbox(
                    "Filtrar por nivel de uso:",
                    ["Todos", "Alto (>80%)", "Medio (50-80%)", "Bajo (<50%)"],
                )

            # Aplicar filtro
            if filtro_uso == "Alto (>80%)":
                df_recursos = df_recursos[df_recursos["Uso Total (%)"] >= 80]
            elif filtro_uso == "Medio (50-80%)":
                df_recursos = df_recursos[(df_recursos["Uso Total (%)"] >= 50) & (df_recursos["Uso Total (%)"] < 80)]
            elif filtro_uso == "Bajo (<50%)":
                df_recursos = df_recursos[df_recursos["Uso Total (%)"] < 50]

            st.dataframe(
                df_recursos,
                column_config={
                    "Recurso": st.column_config.TextColumn("Recurso", width="medium"),
                    "Capacidad (h)": st.column_config.NumberColumn("Capacidad", format="%.1f"),
                    "Uso Actual (h)": st.column_config.NumberColumn("Uso Actual", format="%.1f"),
                    "Uso Actual (%)": st.column_config.ProgressColumn(
                        "% Actual",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%",
                    ),
                    "Uso Adicional (h)": st.column_config.NumberColumn("Uso Adic.", format="%.1f"),
                    "Uso Total (h)": st.column_config.NumberColumn("Uso Total", format="%.1f"),
                    "Uso Total (%)": st.column_config.ProgressColumn(
                        "% Total",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%",
                    ),
                    "Estado": st.column_config.TextColumn("Estado", width="small"),
                },
                hide_index=True,
                use_container_width=True,
            )

        # Recursos excedidos
        if resultados["recursos_excedidos"]:
            st.markdown('<div class="section-header">⚠️ Recursos Excedidos (No incluidos en optimización)</div>', unsafe_allow_html=True)

            df_excedidos = pd.DataFrame(resultados["recursos_excedidos"])
            df_excedidos.columns = ["Recurso", "Uso Actual (h)", "Capacidad (h)", "Excedente (h)"]

            st.dataframe(
                df_excedidos,
                column_config={
                    "Recurso": st.column_config.TextColumn("Recurso", width="medium"),
                    "Uso Actual (h)": st.column_config.NumberColumn("Uso Actual", format="%.1f"),
                    "Capacidad (h)": st.column_config.NumberColumn("Capacidad", format="%.1f"),
                    "Excedente (h)": st.column_config.NumberColumn("Excedente", format="%.1f"),
                },
                hide_index=True,
                use_container_width=True,
            )
    else:
        st.info("👆 Ve a la pestaña **Pacientes** para ejecutar la optimización y ver el detalle de recursos.")

# =====================================================
# TAB 4: VERIFICAR ADMISIÓN
# =====================================================
with tab4:
    st.markdown('<div class="section-header">Verificar Factibilidad de Admisión</div>', unsafe_allow_html=True)
    st.markdown(
        "Verifica si es posible admitir un número específico de pacientes nuevos por programa, "
        "considerando la capacidad actual de recursos."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Formulario de solicitudes
    st.markdown("#### Solicitudes de Admisión")

    # Crear columnas para el formulario
    col_form1, col_form2 = st.columns([2, 1])

    with col_form1:
        # Selector de programa
        programa_seleccionado = st.selectbox(
            "Seleccionar programa:",
            options=range(len(datos_base["nombre_programas"])),
            format_func=lambda x: datos_base["nombre_programas"][x],
            key="programa_verificar",
        )

    with col_form2:
        # Cantidad de pacientes
        cantidad_pacientes = st.number_input(
            "Cantidad de pacientes:",
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
        if st.button("➕ Agregar", use_container_width=True):
            st.session_state.solicitudes_admision[programa_seleccionado] = cantidad_pacientes
            st.rerun()

    with col_btn2:
        if st.button("🗑️ Limpiar Todo", use_container_width=True):
            st.session_state.solicitudes_admision = {}
            st.session_state.resultado_verificacion = None
            st.rerun()

    # Mostrar solicitudes actuales
    if st.session_state.solicitudes_admision:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Solicitudes Pendientes de Verificar")

        solicitudes_df = pd.DataFrame([
            {
                "Programa": datos_base["nombre_programas"][idx],
                "Pacientes Solicitados": cant,
            }
            for idx, cant in st.session_state.solicitudes_admision.items()
        ])

        st.dataframe(
            solicitudes_df,
            column_config={
                "Programa": st.column_config.TextColumn("Programa", width="large"),
                "Pacientes Solicitados": st.column_config.NumberColumn("Pacientes", format="%d"),
            },
            hide_index=True,
            use_container_width=True,
        )

        total_solicitados = sum(st.session_state.solicitudes_admision.values())
        st.markdown(f"**Total de pacientes solicitados:** {total_solicitados}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Botón de verificación
        col_ver1, col_ver2, col_ver3 = st.columns([1, 2, 1])
        with col_ver2:
            verificar_btn = st.button(
                "🔍 Verificar Factibilidad",
                type="primary",
                use_container_width=True,
            )

        if verificar_btn:
            with st.spinner("Verificando factibilidad..."):
                try:
                    resultado_verificacion = verificar_admision(
                        st.session_state.pacientes_actuales,
                        st.session_state.solicitudes_admision,
                    )
                    st.session_state.resultado_verificacion = resultado_verificacion
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al verificar factibilidad: {str(e)}")
                    st.session_state.resultado_verificacion = None

    # Mostrar resultados de verificación
    if "resultado_verificacion" in st.session_state and st.session_state.resultado_verificacion:
        resultado = st.session_state.resultado_verificacion

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### Resultado de la Verificación")

        # Mostrar resultado general
        if resultado["factible"]:
            st.success("✅ **FACTIBLE**: Es posible admitir todos los pacientes solicitados.")
        else:
            st.error("❌ **NO FACTIBLE**: No es posible admitir todos los pacientes solicitados con la capacidad actual.")

        # Detalle por solicitud
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Detalle por Programa")

        for detalle in resultado["solicitudes_detalle"]:
            pacientes_actuales_programa = st.session_state.pacientes_actuales[detalle["programa_idx"]]
            if detalle["factible"]:
                st.markdown(f"""
                <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                    <strong>✅ {detalle['programa']}</strong><br>
                    Actuales: {pacientes_actuales_programa} | Solicitados: {detalle['cantidad_solicitada']} | Máximo admisible: {detalle['max_admisible']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                    <strong>❌ {detalle['programa']}</strong><br>
                    Actuales: {pacientes_actuales_programa} | Solicitados: {detalle['cantidad_solicitada']} | Máximo admisible: {detalle['max_admisible']} | Déficit: {detalle['deficit']}<br>
                    <em>Recurso limitante: {detalle['recurso_limitante']}</em>
                </div>
                """, unsafe_allow_html=True)

        # Recursos limitantes (si hay)
        if resultado["recursos_limitantes"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Recursos que Exceden Capacidad")

            df_limitantes = pd.DataFrame(resultado["recursos_limitantes"])
            df_limitantes = df_limitantes.rename(columns={
                "nombre": "Recurso",
                "tipo": "Tipo",
                "capacidad": "Capacidad (h)",
                "uso_actual": "Uso Actual (h)",
                "uso_adicional_requerido": "Uso Adicional (h)",
                "uso_total_proyectado": "Uso Total (h)",
                "excedente": "Excedente (h)",
                "pct_uso_proyectado": "% Proyectado",
            })

            st.dataframe(
                df_limitantes,
                column_config={
                    "Recurso": st.column_config.TextColumn("Recurso", width="medium"),
                    "Tipo": st.column_config.TextColumn("Tipo", width="small"),
                    "Capacidad (h)": st.column_config.NumberColumn("Capacidad", format="%.1f"),
                    "Uso Actual (h)": st.column_config.NumberColumn("Uso Actual", format="%.1f"),
                    "Uso Adicional (h)": st.column_config.NumberColumn("Uso Adic.", format="%.1f"),
                    "Uso Total (h)": st.column_config.NumberColumn("Uso Total", format="%.1f"),
                    "Excedente (h)": st.column_config.NumberColumn("Excedente", format="%.1f"),
                    "% Proyectado": st.column_config.NumberColumn(
                        "% Proyectado",
                        format="%.1f%% ⚠️",
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )

        # Impacto en recursos (top 15)
        if resultado["impacto_recursos"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Impacto en Recursos (Top 15 más afectados)")

            df_impacto = pd.DataFrame(resultado["impacto_recursos"][:15])

            # Crear gráfico de barras de impacto
            fig_impacto = go.Figure()

            df_impacto_sorted = df_impacto.sort_values("pct_proyectado", ascending=True)

            fig_impacto.add_trace(go.Bar(
                y=df_impacto_sorted["nombre"],
                x=df_impacto_sorted["pct_actual"],
                name="Uso Actual",
                orientation="h",
                marker_color=COLORS["primary"],
            ))

            fig_impacto.add_trace(go.Bar(
                y=df_impacto_sorted["nombre"],
                x=df_impacto_sorted["pct_proyectado"] - df_impacto_sorted["pct_actual"],
                name="Uso Adicional",
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
                xaxis_title="Utilización (%)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            # Línea de referencia al 100%
            fig_impacto.add_vline(x=100, line_dash="dash", line_color=COLORS["danger"], annotation_text="Capacidad máxima")

            st.plotly_chart(fig_impacto, use_container_width=True)

    else:
        if not st.session_state.solicitudes_admision:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("👆 Agrega solicitudes de admisión seleccionando un programa y la cantidad de pacientes, luego haz clic en **Agregar**.")

# === FOOTER ===
st.markdown(f"""
<div class="footer">
    <span class="logo">ARK<span class="dot">●</span>DE</span> × Sanoviv Medical Institute<br>
    Sistema de Optimización de Capacidad de Pacientes
</div>
""", unsafe_allow_html=True)
