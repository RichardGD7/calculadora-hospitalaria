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
        col1, col2, col3, col4 = st.columns(4)

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

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Weighted Value</div>
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

    # Crear DataFrame para edición
    df_pacientes = pd.DataFrame({
        "Program": datos_base["nombre_programas"],
        "Current Patients": st.session_state.pacientes_actuales,
        "Priority": datos_base["prioridad_programas"],
    })

    # Editor de datos
    df_editado = st.data_editor(
        df_pacientes,
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
        key="editor_pacientes",
    )

    # Actualizar estado con los valores editados (solo si cambió)
    nuevos_valores = df_editado["Current Patients"].tolist()
    if nuevos_valores != st.session_state.pacientes_actuales:
        st.session_state.pacientes_actuales = nuevos_valores
        # Limpiar resultados anteriores ya que los datos cambiaron
        st.session_state.resultados = None

    st.markdown("<br>", unsafe_allow_html=True)

    # Botón de cálculo centrado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        calcular = st.button(
            "🔄 Calculate Optimization",
            type="primary",
            use_container_width=True,
        )

    if calcular:
        with st.spinner("Running optimization model..."):
            try:
                st.session_state.resultados = ejecutar_optimizacion(st.session_state.pacientes_actuales)
                st.success("✅ Optimization completed. Go to **Executive Summary** to see the results.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error running the optimization: {str(e)}")
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
        # Selector de programa
        programa_seleccionado = st.selectbox(
            "Select program:",
            options=range(len(datos_base["nombre_programas"])),
            format_func=lambda x: datos_base["nombre_programas"][x],
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
            st.session_state.solicitudes_admision[programa_seleccionado] = cantidad_pacientes
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

        # Mostrar resultado general
        if resultado["factible"]:
            st.success("✅ **FEASIBLE**: It is possible to admit all requested patients.")
        else:
            st.error("❌ **NOT FEASIBLE**: It is not possible to admit all requested patients with current capacity.")

        # Detalle por solicitud
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Detail by Program")

        for detalle in resultado["solicitudes_detalle"]:
            pacientes_actuales_programa = st.session_state.pacientes_actuales[detalle["programa_idx"]]
            if detalle["factible"]:
                st.markdown(f"""
                <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                    <strong>✅ {detalle['programa']}</strong><br>
                    Current: {pacientes_actuales_programa} | Requested: {detalle['cantidad_solicitada']} | Maximum admissible: {detalle['max_admisible']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                    <strong>❌ {detalle['programa']}</strong><br>
                    Current: {pacientes_actuales_programa} | Requested: {detalle['cantidad_solicitada']} | Maximum admissible: {detalle['max_admisible']} | Deficit: {detalle['deficit']}<br>
                    <em>Limiting resource: {detalle['recurso_limitante']}</em>
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

# === FOOTER ===
st.markdown(f"""
<div class="footer">
    <span class="logo">ARK<span class="dot">●</span>DE</span> × Sanoviv Medical Institute<br>
    Patient Capacity Optimization System
</div>
""", unsafe_allow_html=True)
