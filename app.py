# -*- coding: utf-8 -*-
"""
Sistema Operativo de Banquetes - Medher (Ajuste de Texto y Nuevo Logo)
"""

import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import io
import urllib.request
from PIL import Image
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

FILE_PATH = "recetas_base.csv"
FILE_LISTAS = "listas_compras.csv"
CATEGORIAS = ["Abarrotes", "Carnicería", "Frutas y Verduras", "Lácteos y Refrigerados", "Desechables", "Bebidas", "Limpieza", "General"]

# --- 1. INICIALIZACIÓN Y BASE DE DATOS ---
if not os.path.exists(FILE_PATH):
  df_inicial = pd.DataFrame(columns=["Receta", "Platillos_Base", "Ingrediente", "Cantidad_Base", "Unidad", "Categoria"])
  df_inicial.to_csv(FILE_PATH, index=False)

if not os.path.exists(FILE_LISTAS):
  df_listas_inicial = pd.DataFrame(columns=["Tienda", "Ingrediente", "Cantidad", "Unidad", "Categoria"])
  df_listas_inicial.to_csv(FILE_LISTAS, index=False)

def cargar_recetas():
  df = pd.read_csv(FILE_PATH)
  if "Categoria" not in df.columns:
      df["Categoria"] = "General"
      guardar_recetas_local(df)
  return df

def guardar_recetas_local(df):
    df.to_csv(FILE_PATH, index=False)

def guardar_recetas(df):
  guardar_recetas_local(df)
  if "GITHUB_TOKEN" in st.secrets:
    try:
      from github import Github
      g = Github(st.secrets["GITHUB_TOKEN"])
      repo = g.get_repo("Edchvz/Medher-Banquetes")
      contents = repo.get_contents(FILE_PATH, ref="main")
      csv_data = df.to_csv(index=False)
      repo.update_file(contents.path, "Sincronización de recetas", csv_data, contents.sha, branch="main")
    except Exception as e:
      st.error(f"Error al sincronizar con GitHub: {e}")

def cargar_listas():
  return pd.read_csv(FILE_LISTAS)

def guardar_listas(df):
  df.to_csv(FILE_LISTAS, index=False)
  if "GITHUB_TOKEN" in st.secrets:
    try:
      from github import Github
      g = Github(st.secrets["GITHUB_TOKEN"])
      repo = g.get_repo("Edchvz/Medher-Banquetes")
      csv_data = df.to_csv(index=False)
      try:
          contents = repo.get_contents(FILE_LISTAS, ref="main")
          repo.update_file(contents.path, "Actualización lista de compras", csv_data, contents.sha, branch="main")
      except: 
          repo.create_file(FILE_LISTAS, "Creación lista de compras", csv_data, branch="main")
    except Exception as e:
      st.error(f"Error al sincronizar listas con GitHub: {e}")

def obtener_catalogo_insumos(df_recetas, df_listas):
    if df_recetas.empty and df_listas.empty: return {}
    catalogo = {}
    if not df_recetas.empty:
        for _, row in df_recetas.iterrows():
            catalogo[row['Ingrediente']] = {"Unidad": row['Unidad'], "Categoria": row['Categoria']}
    if not df_listas.empty:
        for _, row in df_listas.iterrows():
            catalogo[row['Ingrediente']] = {"Unidad": row['Unidad'], "Categoria": row['Categoria']}
    return catalogo

# --- CONFIGURACIÓN DE PÁGINA E ICONOS ---
st.set_page_config(
    page_title="Medher Banquetes y Más", 
    page_icon="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/IC_MED.jpeg", 
    layout="wide" 
)

st.markdown(
    """
    <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/IC_MED.jpeg">
    <link rel="shortcut icon" href="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/IC_MED.jpeg">
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <img src="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/IC_MED.jpeg" width="55" style="border-radius: 12px; margin-right: 15px;">
        <h1 style="margin: 0;">Medher Banquetes y Más</h1>
    </div>
    """, 
    unsafe_allow_html=True
)
st.caption("Sistema Operativo de Gestión y Escalado de Recetas")

# Cargar datos globales
df_actual = cargar_recetas()
df_listas_global = cargar_listas()
recetas_unicas = sorted(df_actual["Receta"].unique().tolist()) if not df_actual.empty else []
catalogo_maestro = obtener_catalogo_insumos(df_actual, df_listas_global)
lista_opciones_insumos = ["➕ Crear Nuevo Insumo..."] + sorted(list(catalogo_maestro.keys()))

# Pestañas de navegación
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Escalar Producción", 
    "🛒 Compras por Tienda", 
    "➕ Nueva Receta", 
    "🛠️ Modificar / Eliminar", 
    "🍎 Catálogo Maestro"
])

# === PESTAÑA 1: CÁLCULO, EXTRAS Y EXPORTACIÓN ===
with tab1:
  st.subheader("Cálculo de Insumos por Evento")

  if not recetas_unicas:
    st.info("No hay recetas registradas todavía. Ve a la pestaña 'Nueva Receta'.")
  else:
    col1, col2 = st.columns(2)
    with col1: receta_sel = st.selectbox("Seleccionar Receta", recetas_unicas, key="calc_receta")
    with col2: platillos_objetivo = st.number_input("Platillos a preparar", min_value=1.0, value=10.0, step=1.0, key="calc_platillos")

    if st.button("Calcular Lista de Producción", type="primary"):
      filtro = df_actual["Receta"].astype(str).str.lower() == receta_sel.lower()
      receta_df = df_actual[filtro].copy()

      if not receta_df.empty:
        platillos_base = receta_df["Platillos_Base"].iloc[0]
        factor = platillos_objetivo / platillos_base
        receta_df["Cantidad_Requerida"] = (receta_df["Cantidad_Base"] * factor).round(2)

        st.success(f"Lista calculada para {int(platillos_objetivo)} platillos (Base: {int(platillos_base)})")

        receta_df = receta_df.sort_values(by="Categoria")
        st.session_state.tabla_calculada = receta_df[["Categoria", "Ingrediente", "Cantidad_Requerida", "Unidad"]].rename(columns={"Cantidad_Requerida": "Cantidad"})
        st.session_state.receta_activa = receta_sel
        st.session_state.platillos_activos = int(platillos_objetivo)

    if "tabla_calculada" in st.session_state and not st.session_state.tabla_calculada.empty:
      st.dataframe(st.session_state.tabla_calculada, use_container_width=True)

      st.markdown("### 🛒 Extras para el mandado")
      col_ex1, col_ex2, col_ex3, col_ex4 = st.columns([3, 2, 2, 3])
      with col_ex1: extra_insumo = st.text_input("Artículo extra", key="extra_insumo")
      with col_ex2: extra_cant = st.number_input("Cantidad", min_value=0.01, value=1.0, step=0.1, key="extra_cant")
      with col_ex3: extra_uni = st.text_input("Unidad", key="extra_uni")
      with col_ex4: extra_cat = st.selectbox("Categoría", CATEGORIAS, key="extra_cat")
          
      if st.button("➕ Agregar Extra a la Lista"):
          if extra_insumo.strip() and extra_uni.strip():
              nuevo_extra = pd.DataFrame([{"Categoria": extra_cat, "Ingrediente": extra_insumo.strip() + " (Extra)", "Cantidad": extra_cant, "Unidad": extra_uni.strip()}])
              st.session_state.tabla_calculada = pd.concat([st.session_state.tabla_calculada, nuevo_extra], ignore_index=True)
              st.session_state.tabla_calculada = st.session_state.tabla_calculada.sort_values(by="Categoria").reset_index(drop=True)
              st.rerun()
          else:
              st.warning("Completa el nombre del artículo y la unidad.")

      st.markdown("---")
      st.write("### Opciones de Exportación")

      texto_wpp = f"--- MEDHER BANQUETES Y MÁS ---\nReceta: {st.session_state.receta_activa.upper()}\nPlatillos a preparar: {st.session_state.platillos_activos}\n----------------------\n"
      df_agrupado = st.session_state.tabla_calculada.groupby("Categoria")
      for cat, grupo in df_agrupado:
          texto_wpp += f"\n🛒 {cat.upper()}:\n"
          for _, row in grupo.iterrows(): texto_wpp += f" • {row['Ingrediente']}: {row['Cantidad']} {row['Unidad']}\n"

      st.text_area("Texto formateado (agrupado por pasillos para WhatsApp):", texto_wpp, height=250)

      def generar_jpg():
        df_t = st.session_state.tabla_calculada
        num_rows = len(df_t)
        
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
        x_split = 0.45 # <-- Ajustado para darle más espacio al texto de la izquierda
        row_h = (y_top - y_bottom) / 3
        
        # --- TABLA SUPERIOR DIBUJADA MANUALMENTE CON COLORES EXACTOS ---
        # Fila 1: Nombre de empresa (Rosa Fuerte)
        ax.add_patch(plt.Rectangle((0, y_top - row_h), x_logo, row_h, fill=True, facecolor=c_header, edgecolor=c_edge, lw=1.5))
        # Fila 2: Orden de Produccion (Rosa Claro)
        ax.add_patch(plt.Rectangle((0, y_top - 2*row_h), x_split, row_h, fill=True, facecolor=c_row1, edgecolor=c_edge, lw=1.5))
        # Fila 2: Valor del Platillo (Blanco)
        ax.add_patch(plt.Rectangle((x_split, y_top - 2*row_h), x_logo - x_split, row_h, fill=True, facecolor='white', edgecolor=c_edge, lw=1.5))
        # Fila 3: Platillos (Rosa Claro)
        ax.add_patch(plt.Rectangle((0, y_bottom), x_split, row_h, fill=True, facecolor=c_row1, edgecolor=c_edge, lw=1.5))
        # Fila 3: Valor de Cantidad (Blanco)
        ax.add_patch(plt.Rectangle((x_split, y_bottom), x_logo - x_split, row_h, fill=True, facecolor='white', edgecolor=c_edge, lw=1.5))
        # Caja del Logo (Blanco para que empate con la imagen)
        ax.add_patch(plt.Rectangle((x_logo, y_bottom), 1 - x_logo, y_top - y_bottom, fill=True, facecolor='white', edgecolor=c_edge, lw=1.5))
        
        # Textos en Negritas
        pad = 0.02
        ax.text(pad, y_top - row_h/2, "MEDHER BANQUETES Y MAS", ha='left', va='center', fontsize=12, fontweight='bold', color='black')
        ax.text(pad, y_top - 1.5*row_h, "ORDEN DE PRODUCCION", ha='left', va='center', fontsize=11, fontweight='bold', color='black')
        ax.text(x_split + pad, y_top - 1.5*row_h, st.session_state.receta_activa.upper(), ha='left', va='center', fontsize=11, fontweight='bold', color='black')
        ax.text(pad, y_top - 2.5*row_h, "PLATILLOS", ha='left', va='center', fontsize=11, fontweight='bold', color='black')
        ax.text(x_split + pad, y_top - 2.5*row_h, str(st.session_state.platillos_activos), ha='left', va='center', fontsize=11, fontweight='bold', color='black')
        
        # Insertar Nuevo Logo
        try:
            url_logo = "https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/IC_MED.jpeg"
            logo_img = Image.open(urllib.request.urlopen(url_logo))
            logo_img.thumbnail((85, 85)) 
            imagebox = OffsetImage(logo_img, zoom=1)
            ab = AnnotationBbox(imagebox, (x_logo + (1-x_logo)/2, y_bottom + (y_top-y_bottom)/2), xycoords='axes fraction', frameon=False, box_alignment=(0.5, 0.5))
            ax.add_artist(ab)
        except:
            pass

        # --- TABLA INFERIOR DE INSUMOS ---
        data_bbox = [0, 0, 1, y_bottom - 0.02]
        table_data = [[row['Categoria'], row['Ingrediente'], str(row['Cantidad']), str(row['Unidad'])] for _, row in df_t.iterrows()]
        table = ax.table(cellText=table_data, colLabels=["Categoría", "Ingrediente", "Cantidad", "Unidad"], cellLoc='center', bbox=data_bbox)
        
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        
        for key, cell in table.get_celld().items():
            cell.set_edgecolor(c_edge) # Bordes negros
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

      st.download_button("📥 Guardar Reporte en Imagen (JPG)", data=generar_jpg(), file_name=f"Produccion_{st.session_state.receta_activa}_{st.session_state.platillos_activos}pax.jpg", mime="image/jpeg")

# === PESTAÑA 2: COMPRAS POR TIENDA ===
with tab2:
    st.subheader("🛒 Listas de Compras por Tienda")
    st.write("Crea listas permanentes para compras de insumos generales o mayoreo (ej. Sam's USA, HEB, Central de Abastos).")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tiendas_existentes = sorted(df_listas_global['Tienda'].unique().tolist()) if not df_listas_global.empty else []
        tienda_sel = st.selectbox("Seleccionar Tienda", ["➕ Nueva Tienda..."] + tiendas_existentes)
    with col_t2:
        if tienda_sel == "➕ Nueva Tienda...":
            tienda_activa = st.text_input("Nombre de la nueva tienda (ej. Sam's USA)")
        else:
            tienda_activa = tienda_sel

    if tienda_activa:
        st.markdown(f"### Lista de: **{tienda_activa}**")
        df_tienda = df_listas_global[df_listas_global['Tienda'] == tienda_activa].copy()

        st.write("Añadir un insumo a la lista de esta tienda:")
        
        insumo_agregar = st.selectbox("🔍 Buscar en historial o crear nuevo:", lista_opciones_insumos, key="tienda_insumo")

        col_ti1, col_ti2, col_ti3, col_ti4 = st.columns([3, 2, 2, 3])
        
        if insumo_agregar == "➕ Crear Nuevo Insumo...":
            with col_ti1: t_nuevo_nom = st.text_input("Nombre del Insumo", key="t_nuevo_nom")
            with col_ti2: t_cant = st.number_input("Cantidad", min_value=0.01, value=1.0, step=1.0, key="t_cant_nuevo")
            with col_ti3: t_nuevo_uni = st.text_input("Unidad", key="t_nuevo_uni")
            with col_ti4: t_nuevo_cat = st.selectbox("Categoría", CATEGORIAS, key="t_nuevo_cat")
        else:
            datos_insumo = catalogo_maestro[insumo_agregar]
            with col_ti1: st.text_input("Nombre del Insumo", value=insumo_agregar, disabled=True, key=f"t_nom_dis_{insumo_agregar}")
            with col_ti2: t_cant = st.number_input("Cantidad", min_value=0.01, value=1.0, step=1.0, key=f"t_cant_exist_{insumo_agregar}")
            with col_ti3: st.text_input("Unidad", value=datos_insumo["Unidad"], disabled=True, key=f"t_uni_dis_{insumo_agregar}")
            with col_ti4: st.text_input("Categoría", value=datos_insumo["Categoria"], disabled=True, key=f"t_cat_dis_{insumo_agregar}")

        if st.button("➕ Agregar a la tienda"):
            if insumo_agregar == "➕ Crear Nuevo Insumo...":
                if t_nuevo_nom.strip() and t_nuevo_uni.strip():
                    insumo_final = t_nuevo_nom.strip()
                    uni_final = t_nuevo_uni.strip()
                    cat_final = t_nuevo_cat
                else:
                    st.warning("Completa el nombre y la unidad del nuevo insumo.")
                    st.stop()
            else:
                insumo_final = insumo_agregar
                uni_final = datos_insumo["Unidad"]
                cat_final = datos_insumo["Categoria"]

            if insumo_final in df_tienda['Ingrediente'].values:
                idx = df_listas_global[(df_listas_global['Tienda'] == tienda_activa) & (df_listas_global['Ingrediente'] == insumo_final)].index
                df_listas_global.loc[idx, 'Cantidad'] += t_cant
            else:
                nuevo_item = pd.DataFrame([{
                    "Tienda": tienda_activa,
                    "Ingrediente": insumo_final,
                    "Cantidad": t_cant,
                    "Unidad": uni_final,
                    "Categoria": cat_final
                }])
                df_listas_global = pd.concat([df_listas_global, nuevo_item], ignore_index=True)
            
            guardar_listas(df_listas_global)
            st.success(f"{insumo_final} añadido a la lista.")
            st.rerun()

        if not df_tienda.empty:
            st.markdown("---")
            st.write("Lista actual (**Puedes editar las cantidades o marcar la casilla izquierda para eliminar**):")
            
            edited_tienda = st.data_editor(
                df_tienda,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=False,
                column_config={
                    "Tienda": None, 
                    "Ingrediente": st.column_config.TextColumn("Ingrediente", disabled=True),
                    "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.00),
                    "Unidad": st.column_config.TextColumn("Unidad", disabled=True),
                    "Categoria": st.column_config.TextColumn("Categoría", disabled=True)
                },
                key=f"editor_tienda_{tienda_activa}"
            )

            if st.button("💾 Guardar Cambios de la Lista", type="primary"):
                df_listas_global = df_listas_global[df_listas_global['Tienda'] != tienda_activa]
                edited_tienda['Tienda'] = tienda_activa
                df_listas_global = pd.concat([df_listas_global, edited_tienda], ignore_index=True)
                guardar_listas(df_listas_global)
                st.success("¡Lista actualizada con éxito!")
                st.rerun()

            st.markdown("---")
            st.write("### Opciones de Exportación")
            
            texto_tienda = f"--- COMPRAS: {tienda_activa.upper()} ---\n"
            for cat, grupo in edited_tienda.groupby("Categoria"):
                texto_tienda += f"\n🛒 {cat.upper()}:\n"
                for _, row in grupo.iterrows():
                    texto_tienda += f" • {row['Ingrediente']}: {row['Cantidad']} {row['Unidad']}\n"
            st.text_area("Texto formateado para WhatsApp:", texto_tienda, height=200)

            def generar_jpg_tienda():
                edited_sorted = edited_tienda.sort_values(by="Categoria")
                num_rows = len(edited_sorted)
                
                row_height = 0.35
                header_height = 1.3
                fig_height = max(5, header_height + (num_rows + 1) * row_height)
                
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
                x_split = 0.45 # <-- Ajustado igual que en el otro reporte
                row_h = (y_top - y_bottom) / 2 
                
                # Fila 1: Nombre de empresa (Rosa Fuerte)
                ax.add_patch(plt.Rectangle((0, y_top - row_h), x_logo, row_h, fill=True, facecolor=c_header, edgecolor=c_edge, lw=1.5))
                # Fila 2: Lista de Compras (Rosa Claro)
                ax.add_patch(plt.Rectangle((0, y_bottom), x_split, row_h, fill=True, facecolor=c_row1, edgecolor=c_edge, lw=1.5))
                # Fila 2: Nombre de Tienda (Blanco)
                ax.add_patch(plt.Rectangle((x_split, y_bottom), x_logo - x_split, row_h, fill=True, facecolor='white', edgecolor=c_edge, lw=1.5))
                # Caja del Logo
                ax.add_patch(plt.Rectangle((x_logo, y_bottom), 1 - x_logo, y_top - y_bottom, fill=True, facecolor='white', edgecolor=c_edge, lw=1.5))
                
                pad = 0.02
                ax.text(pad, y_top - row_h/2, "MEDHER BANQUETES Y MAS", ha='left', va='center', fontsize=12, fontweight='bold', color='black')
                ax.text(pad, y_top - 1.5*row_h, "LISTA DE COMPRAS", ha='left', va='center', fontsize=11, fontweight='bold', color='black')
                ax.text(x_split + pad, y_top - 1.5*row_h, tienda_activa.upper(), ha='left', va='center', fontsize=11, fontweight='bold', color='black')
                
                try:
                    url_logo = "https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/IC_MED.jpeg"
                    logo_img = Image.open(urllib.request.urlopen(url_logo))
                    logo_img.thumbnail((85, 85))
                    imagebox = OffsetImage(logo_img, zoom=1)
                    ab = AnnotationBbox(imagebox, (x_logo + (1-x_logo)/2, y_bottom + (y_top-y_bottom)/2), xycoords='axes fraction', frameon=False, box_alignment=(0.5, 0.5))
                    ax.add_artist(ab)
                except:
                    pass

                # --- TABLA DE DATOS ---
                data_bbox = [0, 0, 1, y_bottom - 0.02]
                table_data = [[row['Categoria'], row['Ingrediente'], str(row['Cantidad']), str(row['Unidad'])] for _, row in edited_sorted.iterrows()]
                table = ax.table(cellText=table_data, colLabels=["Categoría", "Ingrediente", "Cantidad", "Unidad"], loc='center', cellLoc='center', bbox=data_bbox)
                
                table.auto_set_font_size(False)
                table.set_fontsize(11)
                
                for key, cell in table.get_celld().items():
                    cell.set_edgecolor(c_edge)
                    cell.set_text_props(color='black')
                    if key[0] == 0: 
                        cell.set_text_props(fontweight='bold')
                        cell.set_facecolor(c_header)
                    else: 
                        cell.set_facecolor(c_row1 if key[0] % 2 == 0 else c_row2)
                        
                buf = io.BytesIO()
                plt.savefig(buf, format='jpg', bbox_inches='tight', dpi=300); plt.close(fig); buf.seek(0)
                return buf

            st.download_button("📥 Guardar Lista en Imagen (JPG)", data=generar_jpg_tienda(), file_name=f"Compras_{tienda_activa}.jpg", mime="image/jpeg")

# === PESTAÑA 3: NUEVA RECETA ===
with tab3:
  st.subheader("Registrar Nueva Receta")
  nombre_nueva = st.text_input("Nombre de la Receta", key="nombre_nueva_receta")
  base_nueva = st.number_input("Platillos Base (Rendimiento)", min_value=1.0, value=10.0, step=1.0, key="base_nueva_receta")

  st.markdown("---")
  st.write("Añadir Insumos (Catálogo Inteligente):")
  if "temp_ingredientes" not in st.session_state: st.session_state.temp_ingredientes = []

  modo_insumo = st.selectbox("🔍 Buscar en historial o crear nuevo:", lista_opciones_insumos, key="sel_cat_nuevo")
  col_i1, col_i2, col_i3, col_i4 = st.columns([3, 2, 2, 3])
  
  if modo_insumo == "➕ Crear Nuevo Insumo...":
      with col_i1: insumo = st.text_input("Nombre del Insumo", key="n_insumo")
      with col_i2: cant_insumo = st.number_input("Cantidad", min_value=0.01, value=1.0, step=0.1, key="n_cant")
      with col_i3: unidad_insumo = st.text_input("Unidad", key="n_uni")
      with col_i4: cat_insumo = st.selectbox("Categoría", CATEGORIAS, key="n_cat")
  else:
      datos_insumo = catalogo_maestro[modo_insumo]
      insumo = modo_insumo
      unidad_insumo = datos_insumo["Unidad"]
      cat_insumo = datos_insumo["Categoria"]
      
      with col_i1: st.text_input("Nombre del Insumo", value=insumo, disabled=True, key=f"e_insumo_dis_{modo_insumo}")
      with col_i2: cant_insumo = st.number_input("Cantidad", min_value=0.01, value=1.0, step=0.1, key=f"e_cant_{modo_insumo}")
      with col_i3: st.text_input("Unidad", value=unidad_insumo, disabled=True, key=f"e_uni_dis_{modo_insumo}")
      with col_i4: st.text_input("Categoría", value=cat_insumo, disabled=True, key=f"e_cat_dis_{modo_insumo}")

  if st.button("+ Agregar Insumo a la Lista"):
    if insumo.strip() and unidad_insumo.strip():
      st.session_state.temp_ingredientes.append({"Categoria": cat_insumo, "Ingrediente": insumo.strip(), "Cantidad_Base": cant_insumo, "Unidad": unidad_insumo.strip()})
      st.success(f"Insumo agregado: {insumo} ({cat_insumo})")
    else:
      st.warning("Completa el nombre del insumo y la unidad.")

  if st.session_state.temp_ingredientes:
    st.dataframe(pd.DataFrame(st.session_state.temp_ingredientes), use_container_width=True)
    if st.button("Guardar Receta en Base de Datos"):
      if not nombre_nueva.strip(): st.error("Asigna un nombre a la receta.")
      else:
        df_verificar = cargar_recetas()
        if not df_verificar.empty and (df_verificar['Receta'].astype(str).str.lower() == nombre_nueva.strip().lower()).any(): st.error("La receta ya existe en la base de datos.")
        else:
          nuevos_datos = [{'Receta': nombre_nueva.strip(), 'Platillos_Base': base_nueva, **item} for item in st.session_state.temp_ingredientes]
          df_actualizado = pd.concat([df_verificar, pd.DataFrame(nuevos_datos)], ignore_index=True) if not df_verificar.empty else pd.DataFrame(nuevos_datos)
          guardar_recetas(df_actualizado)
          st.success(f"¡Receta '{nombre_nueva}' guardada permanentemente en la nube!")
          st.session_state.temp_ingredientes.clear()
          st.rerun()

# === PESTAÑA 4: MODIFICAR / ELIMINAR ===
with tab4:
  st.subheader("Modificar o Eliminar Recetas")

  if not recetas_unicas:
    st.info("No hay recetas disponibles para modificar.")
  else:
    receta_mod = st.selectbox("Seleccionar Receta", recetas_unicas, key="select_modificar")

    col_m1, col_m2 = st.columns(2)
    with col_m1: cargar_edicion = st.button("Cargar para Editar")
    with col_m2: eliminar_completa = st.button("🗑️ ELIMINAR RECETA COMPLETA")

    if eliminar_completa:
      df_limpio = df_actual[~(df_actual['Receta'].astype(str).str.lower() == receta_mod.lower())].reset_index(drop=True)
      guardar_recetas(df_limpio)
      st.success(f"Receta '{receta_mod}' eliminada definitivamente.")
      st.rerun()

    if cargar_edicion or ("receta_en_edicion" in st.session_state and st.session_state.receta_en_edicion == receta_mod):
      st.session_state.receta_en_edicion = receta_mod
      filtro_ed = df_actual['Receta'].astype(str).str.lower() == receta_mod.lower()
      df_receta_edit = df_actual[filtro_ed]

      st.markdown(f"### Modificando: {receta_mod}")
      nuevo_nombre_receta = st.text_input("Nombre de la Receta", value=receta_mod, key="edit_nombre_receta")
      nuevo_base_mod = st.number_input("Platillos Base", value=float(df_receta_edit['Platillos_Base'].iloc[0]), step=1.0, key="edit_base")

      if "edit_ingredientes" not in st.session_state or st.session_state.get("current_receta_loaded") != receta_mod:
        st.session_state.edit_ingredientes = df_receta_edit[['Categoria', 'Ingrediente', 'Cantidad_Base', 'Unidad']].to_dict('records')
        st.session_state.current_receta_loaded = receta_mod

      st.write("Ingredientes actuales (**Haz doble clic** en cualquier celda para editarla o marca la casilla de la izquierda para borrar con 'Suprimir'):")
      
      edited_df = st.data_editor(
          pd.DataFrame(st.session_state.edit_ingredientes),
          num_rows="dynamic",
          use_container_width=True,
          hide_index=False,
          column_config={
              "Categoria": st.column_config.SelectboxColumn("Categoría", options=CATEGORIAS, required=True),
              "Ingrediente": st.column_config.TextColumn("Ingrediente", required=True),
              "Cantidad_Base": st.column_config.NumberColumn("Cantidad Base", min_value=0.01, required=True),
              "Unidad": st.column_config.TextColumn("Unidad", required=True)
          },
          key="data_editor_receta"
      )
      
      st.session_state.edit_ingredientes = edited_df.to_dict('records')

      st.markdown("---")
      st.write("Buscador de insumos (para agregar nuevos desde el catálogo):")
      modo_insumo_ed = st.selectbox("🔍 Buscar en historial o crear nuevo:", lista_opciones_insumos, key="sel_cat_ed")

      col_e1, col_e2, col_e3, col_e4 = st.columns([3, 2, 2, 3])
      if modo_insumo_ed == "➕ Crear Nuevo Insumo...":
          with col_e1: ed_ing = st.text_input("Nombre del Insumo", key="ed_n_ing")
          with col_e2: ed_cant = st.number_input("Cantidad Base", min_value=0.01, value=1.0, step=0.1, key="ed_n_cant")
          with col_e3: ed_uni = st.text_input("Unidad", key="ed_n_uni")
          with col_e4: ed_cat = st.selectbox("Categoría", CATEGORIAS, key="ed_n_cat")
      else:
          datos_insumo_ed = catalogo_maestro[modo_insumo_ed]
          ed_ing = modo_insumo_ed
          ed_uni = datos_insumo_ed["Unidad"]
          ed_cat = datos_insumo_ed["Categoria"]
          
          with col_e1: st.text_input("Nombre del Insumo", value=ed_ing, disabled=True, key=f"ed_e_ing_dis_{modo_insumo_ed}")
          with col_e2: ed_cant = st.number_input("Cantidad Base", min_value=0.01, value=1.0, step=0.1, key=f"ed_e_cant_{modo_insumo_ed}")
          with col_e3: st.text_input("Unidad", value=ed_uni, disabled=True, key=f"ed_e_uni_dis_{modo_insumo_ed}")
          with col_e4: st.text_input("Categoría", value=ed_cat, disabled=True, key=f"ed_e_cat_dis_{modo_insumo_ed}")

      st.markdown("<br>", unsafe_allow_html=True)
      col_btn1, col_btn2 = st.columns(2)
      
      with col_btn1:
          if st.button("➕ Agregar / Actualizar Insumo", use_container_width=True):
              if ed_ing.strip() and ed_uni.strip():
                  insumo_nombre = ed_ing.strip()
                  encontrado = False
                  for item in st.session_state.edit_ingredientes:
                      if item['Ingrediente'].lower() == insumo_nombre.lower():
                          item['Cantidad_Base'] = ed_cant
                          item['Unidad'] = ed_uni.strip()
                          item['Categoria'] = ed_cat
                          encontrado = True
                          break
                  if not encontrado:
                      st.session_state.edit_ingredientes.append({"Categoria": ed_cat, "Ingrediente": insumo_nombre, "Cantidad_Base": ed_cant, "Unidad": ed_uni.strip()})
                  st.rerun()
              else:
                  st.warning("Completa los datos del insumo.")
                  
      with col_btn2:
          col_sel, col_del = st.columns([3, 2])
          with col_sel:
              ing_a_quitar = st.selectbox("Eliminar insumo:", [item['Ingrediente'] for item in st.session_state.edit_ingredientes] if st.session_state.edit_ingredientes else ["Ninguno"], label_visibility="collapsed", key="quitar_ing")
          with col_del:
              if st.button("🗑️ Quitar Insumo", use_container_width=True) and ing_a_quitar != "Ninguno":
                  st.session_state.edit_ingredientes = [item for item in st.session_state.edit_ingredientes if item['Ingrediente'] != ing_a_quitar]
                  st.rerun()

      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("💾 Sobrescribir y Guardar Cambios Definitivos de la Receta", type="primary"):
        if not nuevo_nombre_receta.strip(): st.error("El nombre de la receta no puede estar vacío.")
        elif not st.session_state.edit_ingredientes: st.error("La receta debe tener al menos un ingrediente.")
        else:
          df_base = cargar_recetas()
          df_base = df_base[~(df_base['Receta'].astype(str).str.lower() == receta_mod.lower())].reset_index(drop=True)
          nuevos_cambios = [{'Receta': nuevo_nombre_receta.strip(), 'Platillos_Base': nuevo_base_mod, **item} for item in st.session_state.edit_ingredientes]
          df_final_mod = pd.concat([df_base, pd.DataFrame(nuevos_cambios)], ignore_index=True) if not df_base.empty else pd.DataFrame(nuevos_cambios)
          guardar_recetas(df_final_mod)
          st.success("¡Cambios guardados con éxito permanentemente!")
          del st.session_state.receta_en_edicion
          del st.session_state.edit_ingredientes
          st.rerun()

# === PESTAÑA 5: CATÁLOGO DE INSUMOS ===
with tab5:
    st.subheader("🍎 Gestor del Catálogo Maestro")
    st.info("Al modificar un insumo aquí, se actualizará automáticamente en **todas las recetas** donde haya sido utilizado históricamente.")
    
    if not catalogo_maestro:
        st.write("El catálogo está vacío. Agrega recetas primero.")
    else:
        insumo_a_editar = st.selectbox("Seleccionar Insumo para Editar", sorted(list(catalogo_maestro.keys())), key="cat_edit_sel")
        
        if insumo_a_editar:
            datos_actuales = catalogo_maestro[insumo_a_editar]
            
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1: nuevo_nombre_insumo = st.text_input("Nombre del Insumo", value=insumo_a_editar, key=f"cat_nom_{insumo_a_editar}")
            with col_c2: nueva_unidad_insumo = st.text_input("Unidad Predeterminada", value=datos_actuales["Unidad"], key=f"cat_uni_{insumo_a_editar}")
            with col_c3:
                try: idx_cat_cat = CATEGORIAS.index(datos_actuales["Categoria"])
                except ValueError: idx_cat_cat = CATEGORIAS.index("General")
                nueva_cat_insumo = st.selectbox("Categoría", CATEGORIAS, index=idx_cat_cat, key=f"cat_cat_{insumo_a_editar}")
                
            if st.button("💾 Guardar Cambios en Todo el Sistema", type="primary"):
                if not nuevo_nombre_insumo.strip():
                    st.error("El nombre no puede estar vacío.")
                else:
                    df_base = cargar_recetas()
                    mask = df_base['Ingrediente'] == insumo_a_editar
                    df_base.loc[mask, 'Ingrediente'] = nuevo_nombre_insumo.strip()
                    df_base.loc[mask, 'Unidad'] = nueva_unidad_insumo.strip()
                    df_base.loc[mask, 'Categoria'] = nueva_cat_insumo
                    guardar_recetas(df_base)
                    
                    df_compras = cargar_listas()
                    mask_compras = df_compras['Ingrediente'] == insumo_a_editar
                    if mask_compras.any():
                        df_compras.loc[mask_compras, 'Ingrediente'] = nuevo_nombre_insumo.strip()
                        df_compras.loc[mask_compras, 'Unidad'] = nueva_unidad_insumo.strip()
                        df_compras.loc[mask_compras, 'Categoria'] = nueva_cat_insumo
                        guardar_listas(df_compras)
                        
                    st.success(f"¡El insumo '{nuevo_nombre_insumo}' fue actualizado con éxito en toda la base de datos!")
                    st.rerun()