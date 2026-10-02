# -*- coding: utf-8 -*-
"""
Created on Fri Oct  2 16:15:02 2026

@author: Edwin
"""

# -*- coding: utf-8 -*-
"""
Sistema de Control de Notas de Compra y Cortes - Medher Banquetes y Más
"""

import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import io
import urllib.request
from datetime import datetime
from PIL import Image
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# Archivos de Base de Datos
FILE_NOTAS = "notas_compras.csv"
FILE_CORTES = "cortes_gastos.csv"

CATEGORIAS = ["Abarrotes", "Carnicería", "Frutas y Verduras", "Lácteos y Refrigerados", "Desechables", "Bebidas", "Limpieza", "General", "Especies"]
METODOS_PAGO = ["Efectivo", "Transferencia", "Tarjeta de Débito/Crédito", "Caja Chica", "Otro"]

# --- 1. INICIALIZACIÓN Y MANEJO DE BASE DE DATOS ---
if not os.path.exists(FILE_NOTAS):
    df_notas_init = pd.DataFrame(columns=[
        "ID_Nota", "Fecha_Compra", "Tienda_Proveedor", "Folio_Nota", 
        "Concepto", "Monto", "Categoria", "Metodo_Pago", "Estado", "ID_Corte"
    ])
    df_notas_init.to_csv(FILE_NOTAS, index=False)

if not os.path.exists(FILE_CORTES):
    df_cortes_init = pd.DataFrame(columns=[
        "ID_Corte", "Fecha_Corte", "Periodo_Inicio", "Periodo_Fin", 
        "Cantidad_Notas", "Total_Monto", "Observaciones"
    ])
    df_cortes_init.to_csv(FILE_CORTES, index=False)

def cargar_notas():
    df = pd.read_csv(FILE_NOTAS)
    if not df.empty:
        df["Fecha_Compra"] = pd.to_datetime(df["Fecha_Compra"]).dt.date
    return df

def cargar_cortes():
    df = pd.read_csv(FILE_CORTES)
    if not df.empty:
        df["Fecha_Corte"] = pd.to_datetime(df["Fecha_Corte"])
    return df

def guardar_base_datos(df_notas, df_cortes=None):
    df_notas.to_csv(FILE_NOTAS, index=False)
    if df_cortes is not None:
        df_cortes.to_csv(FILE_CORTES, index=False)

    if "GITHUB_TOKEN" in st.secrets:
        try:
            from github import Github
            g = Github(st.secrets["GITHUB_TOKEN"])
            repo = g.get_repo("Edchvz/Medher-Banquetes")
            
            # Sync Notas
            csv_notas = df_notas.to_csv(index=False)
            try:
                c_notas = repo.get_contents(FILE_NOTAS, ref="main")
                repo.update_file(c_notas.path, "Actualización notas de compra", csv_notas, c_notas.sha, branch="main")
            except:
                repo.create_file(FILE_NOTAS, "Creación notas de compra", csv_notas, branch="main")

            # Sync Cortes
            if df_cortes is not None:
                csv_cortes = df_cortes.to_csv(index=False)
                try:
                    c_cortes = repo.get_contents(FILE_CORTES, ref="main")
                    repo.update_file(c_cortes.path, "Actualización cortes de gastos", csv_cortes, c_cortes.sha, branch="main")
                except:
                    repo.create_file(FILE_CORTES, "Creación cortes de gastos", csv_cortes, branch="main")
        except Exception as e:
            st.error(f"Error al sincronizar con GitHub: {e}")

# --- CONFIGURACIÓN DE PÁGINA E ICONOS ---
st.set_page_config(
    page_title="Control de Notas y Cortes - Medher", 
    page_icon="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/icono_medher.png", 
    layout="wide" 
)

st.markdown(
    """
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <img src="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/icono_medher.png" width="55" style="border-radius: 12px; margin-right: 15px;">
        <h1 style="margin: 0;">Medher Banquetes y Más</h1>
    </div>
    """, 
    unsafe_allow_html=True
)
st.caption("Sistema de Registro de Notas de Compra, Sumas Periódicas y Cortes de Caja")

# Cargar Datos
df_notas_global = cargar_notas()
df_cortes_global = cargar_cortes()

# Pestañas Principales
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Registrar Nota", 
    "📊 Sumas y Análisis", 
    "✂️ Realizar Corte", 
    "📜 Historial de Cortes / BD"
])

# ==========================================
# === PESTAÑA 1: REGISTRAR NOTA DE COMPRA ===
# ==========================================
with tab1:
    st.subheader("📝 Registrar Nueva Nota de Compra")
    
    with st.form("form_nueva_nota", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            fecha_nota = st.date_input("Fecha de Compra", value=datetime.now().date())
            tienda_nota = st.text_input("Tienda / Proveedor (ej. HEB, Sam's, Abastos)")
        with col2:
            folio_nota = st.text_input("Folio / N° Nota (Opcional)")
            monto_nota = st.number_input("Monto Total ($ MXN)", min_value=0.01, value=100.0, step=10.0)
        with col3:
            cat_nota = st.selectbox("Categoría", CATEGORIAS)
            metodo_pago = st.selectbox("Método de Pago", METODOS_PAGO)
            
        concepto_nota = st.text_input("Concepto / Descripción breve (ej. Compra de verdura y limones)")
        
        btn_guardar = st.form_submit_button("💾 Registrar Nota de Compra", type="primary")

        if btn_guardar:
            if not tienda_nota.strip() or not concepto_nota.strip():
                st.error("Por favor completa el Proveedor y el Concepto.")
            else:
                id_nota_nueva = f"N-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                nueva_row = pd.DataFrame([{
                    "ID_Nota": id_nota_nueva,
                    "Fecha_Compra": fecha_nota,
                    "Tienda_Proveedor": tienda_nota.strip(),
                    "Folio_Nota": folio_nota.strip() if folio_nota.strip() else "S/N",
                    "Concepto": concepto_nota.strip(),
                    "Monto": round(monto_nota, 2),
                    "Categoria": cat_nota,
                    "Metodo_Pago": metodo_pago,
                    "Estado": "Pendiente",
                    "ID_Corte": "Sin Corte"
                }])
                
                df_notas_global = pd.concat([df_notas_global, nueva_row], ignore_index=True)
                guardar_base_datos(df_notas_global, df_cortes_global)
                st.success(f"¡Nota registrada exitosamente por ${monto_nota:,.2f} MXN!")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Notas Pendientes de Corte (Período Actual)")
    
    df_pendientes = df_notas_global[df_notas_global["Estado"] == "Pendiente"].copy()
    
    if df_pendientes.empty:
        st.info("No hay notas pendientes de corte en este momento.")
    else:
        st.write(f"**Total acumulado pendiente:** ${df_pendientes['Monto'].sum():,.2f} MXN ({len(df_pendientes)} notas)")
        
        editor_notas = st.data_editor(
            df_pendientes[["ID_Nota", "Fecha_Compra", "Tienda_Proveedor", "Folio_Nota", "Concepto", "Monto", "Categoria", "Metodo_Pago"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Monto": st.column_config.NumberColumn("Monto ($)", format="$%.2f"),
                "Fecha_Compra": st.column_config.DateColumn("Fecha")
            },
            key="editor_notas_pendientes"
        )


# ==========================================
# === PESTAÑA 2: SUMAS Y ANÁLISIS POR TIEMPO ===
# ==========================================
with tab2:
    st.subheader("📊 Cálculo de Sumas y Gastos Acumulados")
    
    if df_notas_global.empty:
        st.info("Aún no existen notas registradas en la base de datos.")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_tiempo = st.selectbox("Seleccionar Rango de Tiempo", [
                "Todas las Notas", "Día de Hoy", "Esta Semana", "Este Mes", "Rango Personalizado"
            ])
        
        fecha_min = pd.to_datetime(df_notas_global["Fecha_Compra"]).min().date()
        fecha_max = pd.to_datetime(df_notas_global["Fecha_Compra"]).max().date()
        
        with col_f2:
            if filtro_tiempo == "Rango Personalizado":
                rango_fechas = st.date_input("Seleccionar Periodo", value=(fecha_min, fecha_max))
            else:
                rango_fechas = None

        # Filtrar datos según periodo
        df_filtrado = df_notas_global.copy()
        df_filtrado["Fecha_Dt"] = pd.to_datetime(df_filtrado["Fecha_Compra"]).dt.date
        hoy = datetime.now().date()

        if filtro_tiempo == "Día de Hoy":
            df_filtrado = df_filtrado[df_filtrado["Fecha_Dt"] == hoy]
        elif filtro_tiempo == "Esta Semana":
            inicio_semana = hoy - pd.Timedelta(days=hoy.weekday())
            df_filtrado = df_filtrado[df_filtrado["Fecha_Dt"] >= inicio_semana]
        elif filtro_tiempo == "Este Mes":
            df_filtrado = df_filtrado[pd.to_datetime(df_filtrado["Fecha_Dt"]).dt.month == hoy.month]
        elif filtro_tiempo == "Rango Personalizado" and isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
            df_filtrado = df_filtrado[(df_filtrado["Fecha_Dt"] >= rango_fechas[0]) & (df_filtrado["Fecha_Dt"] <= rango_fechas[1])]

        st.markdown("---")
        # Tarjetas Métricas
        m1, m2, m3 = st.columns(3)
        total_suma = df_filtrado["Monto"].sum()
        cant_notas = len(df_filtrado)
        promedio = total_suma / cant_notas if cant_notas > 0 else 0.0

        m1.metric("💰 Total Gastado", f"${total_suma:,.2f} MXN")
        m2.metric("🧾 Notas Registradas", f"{cant_notas}")
        m3.metric("📈 Promedio por Nota", f"${promedio:,.2f} MXN")

        if not df_filtrado.empty:
            st.markdown("### 🛒 Desglose de Gastos por Categoría")
            df_cat = df_filtrado.groupby("Categoria")["Monto"].sum().reset_index().sort_values(by="Monto", ascending=False)
            
            col_graph1, col_graph2 = st.columns([1, 1])
            with col_graph1:
                st.dataframe(df_cat, use_container_width=True, hide_index=True)
            with col_graph2:
                st.bar_chart(df_cat.set_index("Categoria"))

            st.markdown("### 📄 Registro Detallado del Periodo")
            st.dataframe(df_filtrado[["Fecha_Compra", "Tienda_Proveedor", "Folio_Nota", "Concepto", "Categoria", "Metodo_Pago", "Monto", "Estado"]], use_container_width=True, hide_index=True)


# ==========================================
# === PESTAÑA 3: REALIZAR CORTE DE CAJA ===
# ==========================================
with tab3:
    st.subheader("✂️ Generar Corte de Gastos y Cierre de Caja")
    st.write("Agrupa todas las **notas pendientes acumuladas** para realizar un corte oficial de período y archivarlas.")

    df_a_cortar = df_notas_global[df_notas_global["Estado"] == "Pendiente"].copy()

    if df_a_cortar.empty:
        st.success("🎉 ¡Excelente! No hay notas pendientes de corte en este momento.")
    else:
        total_a_cortar = df_a_cortar["Monto"].sum()
        f_min = df_a_cortar["Fecha_Compra"].min()
        f_max = df_a_cortar["Fecha_Compra"].max()

        st.warning(f"⚠️ **Notas por cortar:** {len(df_a_cortar)} | **Suma Total a cerrar:** ${total_a_cortar:,.2f} MXN")
        st.write(f"**Periodo abarcado:** Del {f_min} al {f_max}")

        obs_corte = st.text_input("Observaciones o notas del corte (ej. Corte Semana 38 - Evento Quinceañera)", key="obs_corte_input")

        if st.button("✂️ EFECTUAR CORTE DEFINITIVO", type="primary"):
            id_corte_nuevo = f"CORTE-{datetime.now().strftime('%Y%m%d-%H%M')}"
            fecha_corte_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 1. Registrar Corte
            nuevo_corte_df = pd.DataFrame([{
                "ID_Corte": id_corte_nuevo,
                "Fecha_Corte": fecha_corte_actual,
                "Periodo_Inicio": str(f_min),
                "Periodo_Fin": str(f_max),
                "Cantidad_Notas": len(df_a_cortar),
                "Total_Monto": round(total_a_cortar, 2),
                "Observaciones": obs_corte.strip() if obs_corte.strip() else "Corte regular"
            }])

            df_cortes_global = pd.concat([df_cortes_global, nuevo_corte_df], ignore_index=True)

            # 2. Actualizar Estado de Notas
            idx_pendientes = df_notas_global[df_notas_global["Estado"] == "Pendiente"].index
            df_notas_global.loc[idx_pendientes, "Estado"] = "Cortado"
            df_notas_global.loc[idx_pendientes, "ID_Corte"] = id_corte_nuevo

            guardar_base_datos(df_notas_global, df_cortes_global)
            st.session_state["ultimo_corte_realizado"] = id_corte_nuevo
            st.success(f"¡Corte {id_corte_nuevo} realizado con éxito!")
            st.rerun()

    if "ultimo_corte_realizado" in st.session_state:
        corte_id = st.session_state["ultimo_corte_realizado"]
        st.markdown("---")
        st.subheader(f"🖼️ Reporte Exportable del {corte_id}")

        df_notas_corte = df_notas_global[df_notas_global["ID_Corte"] == corte_id]
        
        texto_wpp_corte = f"--- MEDHER BANQUETES Y MÁS ---\nREPORTES DE CORTE: {corte_id}\nTotal Notas: {len(df_notas_corte)}\nSUMA TOTAL: ${df_notas_corte['Monto'].sum():,.2f} MXN\n----------------------\n"
        for _, r in df_notas_corte.iterrows():
            texto_wpp_corte += f" • {r['Fecha_Compra']} | {r['Tienda_Proveedor']} ({r['Concepto']}): ${r['Monto']:,.2f}\n"

        st.text_area("Texto para WhatsApp del Corte:", texto_wpp_corte, height=200)

        def generar_jpg_corte():
            num_rows = len(df_notas_corte)
            row_height = 0.35
            header_height = 1.8
            fig_height = max(6, header_height + (num_rows + 1) * row_height)

            fig, ax = plt.subplots(figsize=(8, fig_height))
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')

            header_frac = header_height / fig_height
            y_top = 1 - 0.02
            y_bottom = 1 - header_frac + 0.03

            c_header = '#F48FB1'
            c_row1 = '#FCE4EC'
            c_row2 = '#FFFFFF'
            c_edge = 'black'

            x_logo = 0.75
            x_split = 0.35
            row_h = (y_top - y_bottom) / 3

            ax.add_patch(plt.Rectangle((0, y_top - row_h), x_logo, row_h, fill=True, facecolor=c_header, edgecolor=c_edge, lw=1.5))
            ax.add_patch(plt.Rectangle((0, y_top - 2*row_h), x_split, row_h, fill=True, facecolor=c_row1, edgecolor=c_edge, lw=1.5))
            ax.add_patch(plt.Rectangle((x_split, y_top - 2*row_h), x_logo - x_split, row_h, fill=True, facecolor='white', edgecolor=c_edge, lw=1.5))
            ax.add_patch(plt.Rectangle((0, y_bottom), x_split, row_h, fill=True, facecolor=c_row1, edgecolor=c_edge, lw=1.5))
            ax.add_patch(plt.Rectangle((x_split, y_bottom), x_logo - x_split, row_h, fill=True, facecolor='white', edgecolor=c_edge, lw=1.5))
            ax.add_patch(plt.Rectangle((x_logo, y_bottom), 1 - x_logo, y_top - y_bottom, fill=True, facecolor='white', edgecolor=c_edge, lw=1.5))

            pad = 0.02
            ax.text(pad, y_top - row_h/2, "MEDHER BANQUETES Y MAS", ha='left', va='center', fontsize=12, fontweight='bold', color='black')
            ax.text(pad, y_top - 1.5*row_h, "CORTE DE GASTOS", ha='left', va='center', fontsize=10, fontweight='bold', color='black')
            ax.text(x_split + pad, y_top - 1.5*row_h, corte_id, ha='left', va='center', fontsize=10, fontweight='bold', color='black')
            ax.text(pad, y_top - 2.5*row_h, "SUMA TOTAL", ha='left', va='center', fontsize=10, fontweight='bold', color='black')
            ax.text(x_split + pad, y_top - 2.5*row_h, f"${df_notas_corte['Monto'].sum():,.2f} MXN", ha='left', va='center', fontsize=11, fontweight='bold', color='black')

            try:
                url_logo = "https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/IC_MED.png"
                logo_img = Image.open(urllib.request.urlopen(url_logo))
                logo_img.thumbnail((85, 85))
                imagebox = OffsetImage(logo_img, zoom=1)
                ab = AnnotationBbox(imagebox, (x_logo + (1-x_logo)/2, y_bottom + (y_top-y_bottom)/2), xycoords='axes fraction', frameon=False, box_alignment=(0.5, 0.5))
                ax.add_artist(ab)
            except:
                pass

            data_bbox = [0, 0, 1, y_bottom - 0.02]
            table_data = [[str(r['Fecha_Compra']), str(r['Tienda_Proveedor']), str(r['Concepto']), f"${r['Monto']:,.2f}"] for _, r in df_notas_corte.iterrows()]
            table = ax.table(cellText=table_data, colLabels=["Fecha", "Proveedor", "Concepto", "Monto"], cellLoc='center', bbox=data_bbox)

            table.auto_set_font_size(False)
            table.set_fontsize(10)

            for key, cell in table.get_celld().items():
                cell.set_edgecolor(c_edge)
                cell.set_text_props(color='black')
                if key[0] == 0:
                    cell.set_text_props(fontweight='bold')
                    cell.set_facecolor(c_header)
                else:
                    cell.set_facecolor(c_row1 if key[0] % 2 == 0 else c_row2)

            buf = io.BytesIO()
            plt.savefig(buf, format='jpg', bbox_inches='tight', dpi=300)
            plt.close(fig)
            buf.seek(0)
            return buf

        st.download_button("📥 Descargar Reporte de Corte en Imagen (JPG)", data=generar_jpg_corte(), file_name=f"{corte_id}.jpg", mime="image/jpeg")


# ==========================================
# === PESTAÑA 4: HISTORIAL DE CORTES Y BD ===
# ==========================================
with tab4:
    st.subheader("📜 Historial de Cortes Registrados")

    if df_cortes_global.empty:
        st.info("Aún no se han realizado cortes de caja en el sistema.")
    else:
        st.dataframe(df_cortes_global, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🔍 Ver Desglose de un Corte Anterior")
        corte_sel = st.selectbox("Seleccionar Folio de Corte:", df_cortes_global["ID_Corte"].unique())

        if corte_sel:
            df_detalle_corte = df_notas_global[df_notas_global["ID_Corte"] == corte_sel]
            st.write(f"**Notas incluidas en {corte_sel}:**")
            st.dataframe(df_detalle_corte[["Fecha_Compra", "Tienda_Proveedor", "Folio_Nota", "Concepto", "Categoria", "Metodo_Pago", "Monto"]], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🗄️ Base de Datos Completa de Notas")
    st.dataframe(df_notas_global, use_container_width=True, hide_index=True)