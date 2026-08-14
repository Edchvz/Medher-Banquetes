# -*- coding: utf-8 -*-
"""
Sistema Operativo de Banquetes - Medher (Gestor de Catálogo, Listas de Tienda y Edición Dinámica)
"""

import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import io

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
      except: # Si el archivo no existe en GitHub todavía
          repo.create_file(FILE_LISTAS, "Creación lista de compras", csv_data, branch="main")
    except Exception as e:
      st.error(f"Error al sincronizar listas con GitHub: {e}")

def obtener_catalogo_insumos(df):
    if df.empty: return {}
    catalogo = {}
    for _, row in df.iterrows():
        catalogo[row['Ingrediente']] = {"Unidad": row['Unidad'], "Categoria": row['Categoria']}
    return catalogo

# --- CONFIGURACIÓN DE PÁGINA E ICONOS ---
st.set_page_config(
    page_title="Medher Banquetes y Más", 
    page_icon="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/icono_medher.png", 
    layout="wide" 
)

st.markdown(
    """
    <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/icono_medher.png">
    <link rel="shortcut icon" href="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/icono_medher.png">
    """,
    unsafe_allow_html=True
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
st.caption("Sistema Operativo de Gestión y Escalado de Recetas")

# Cargar datos
df_actual = cargar_recetas()
recetas_unicas = sorted(df_actual["Receta"].unique().tolist()) if not df_actual.empty else []
catalogo_maestro = obtener_catalogo_insumos(df_actual)
lista_opciones_insumos = ["➕ Crear Nuevo Insumo..."] + sorted(list(catalogo_maestro.keys()))

# Pestañas de navegación
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Escalar Producción", "➕ Nueva Receta", "🛠️ Modificar / Eliminar", "🍎 Catálogo Maestro", "🛒 Compras por Tienda"])

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
        fig, ax = plt.subplots(figsize=(10, max(4, len(df_t) * 0.4 + 2))) 
        ax.axis('off'); ax.axis('tight')
        ax.set_title(f"MEDHER BANQUETES Y MÁS\nOrden de Producción: {st.session_state.receta_activa.upper()}\nPlatillos: {st.session_state.platillos_activos}\n", fontsize=12, fontweight='bold', color='#2c3e50', pad=20)
        table_data = [[row['Categoria'], row['Ingrediente'], str(row['Cantidad']), str(row['Unidad'])] for _, row in df_t.iterrows()]
        table = ax.table(cellText=table_data, colLabels=["Categoría", "Ingrediente", "Cantidad", "Unidad"], loc='center', cellLoc='center', colColours=['#2c3e50']*4)
        table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1.2, 1.5)
        for key, cell in table.get_celld().items():
          cell.set_edgecolor('#bdc3c7')
          if key[0] == 0: cell.set_text_props(color='white', fontweight='bold'); cell.set_facecolor('#2c3e50')
          else: cell.set_facecolor('#ecf0f1' if key[0] % 2 == 0 else 'white')
        buf = io.BytesIO()
        plt.savefig(buf, format='jpg', bbox_inches='tight', dpi=300); plt.close(fig); buf.seek(0)
        return buf

      st.download_button("📥 Guardar Reporte en Imagen (JPG)", data=generar_jpg(), file_name=f"Produccion_{st.session_state.receta_activa}_{st.session_state.platillos_activos}pax.jpg", mime="image/jpeg")

# === PESTAÑA 2: NUEVA RECETA ===
with tab2:
  st.subheader("Registrar Nueva Receta")
  nombre_nueva = st.text_input("Nombre de la Receta", key="nombre_nueva_receta")
  base_nueva = st.number_input("Platillos Base (Rendimiento)", min_value=1.0, value=10.0, step=1.0, key="base_nueva_receta")

  st.markdown("---")
  st.write("Añadir Insumos (Catálogo Inteligente):")
  if "temp_ingredientes" not in st.session_state: st.session_state.temp_ingredientes = []

  modo_insumo = st.selectbox("🔍 Buscar en historial o crear nuevo:", lista_opciones_insumos, key="sel_cat_nuevo")
  col_i1, col_i2, col_i3, col_i4 = st.columns([3, 2, 2, 3])
  
  if modo_insumo == "➕ Crear Nuevo Insumo...":
      with col_i1: insumo = st.text_input("Nombre del Insumo", key="input_insumo")
      with col_i2: cant_insumo = st.number_input("Cantidad", min_value=0.01, value=1.0, step=0.1, key="input_cant")
      with col_i3: unidad_insumo = st.text_input("Unidad", key="input_uni")
      with col_i4: cat_insumo = st.selectbox("Categoría", CATEGORIAS, key="input_cat")
  else:
      datos_insumo = catalogo_maestro[modo_insumo]
      try: idx_cat = CATEGORIAS.index(datos_insumo["Categoria"])
      except ValueError: idx_cat = CATEGORIAS.index("General")
      with col_i1: insumo = st.text_input("Nombre del Insumo", value=modo_insumo, disabled=True, key="input_insumo")
      with col_i2: cant_insumo = st.number_input("Cantidad", min_value=0.01, value=1.0, step=0.1, key="input_cant")
      with col_i3: unidad_insumo = st.text_input("Unidad", value=datos_insumo["Unidad"], key="input_uni")
      with col_i4: cat_insumo = st.selectbox("Categoría", CATEGORIAS, index=idx_cat, key="input_cat")

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

# === PESTAÑA 3: MODIFICAR / ELIMINAR ===
with tab3:
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
          with col_e1: e_ing = st.text_input("Nombre del Insumo", key="e_ing")
          with col_e2: e_cant = st.number_input("Cantidad Base", min_value=0.01, value=1.0, step=0.1, key="e_cant")
          with col_e3: e_uni = st.text_input("Unidad", key="e_uni")
          with col_e4: e_cat = st.selectbox("Categoría", CATEGORIAS, key="e_cat")
      else:
          datos_insumo_ed = catalogo_maestro[modo_insumo_ed]
          try: idx_cat_ed = CATEGORIAS.index(datos_insumo_ed["Categoria"])
          except ValueError: idx_cat_ed = CATEGORIAS.index("General")
          with col_e1: e_ing = st.text_input("Nombre del Insumo", value=modo_insumo_ed, disabled=True, key="e_ing")
          with col_e2: e_cant = st.number_input("Cantidad Base", min_value=0.01, value=1.0, step=0.1, key="e_cant")
          with col_e3: e_uni = st.text_input("Unidad", value=datos_insumo_ed["Unidad"], key="e_uni")
          with col_e4: e_cat = st.selectbox("Categoría", CATEGORIAS, index=idx_cat_ed, key="e_cat")

      st.markdown("<br>", unsafe_allow_html=True)
      col_btn1, col_btn2 = st.columns(2)
      
      with col_btn1:
          if st.button("➕ Agregar / Actualizar Insumo", use_container_width=True):
              if e_ing.strip() and e_uni.strip():
                  insumo_nombre = e_ing.strip()
                  encontrado = False
                  for item in st.session_state.edit_ingredientes:
                      if item['Ingrediente'].lower() == insumo_nombre.lower():
                          item['Cantidad_Base'] = e_cant
                          item['Unidad'] = e_uni.strip()
                          item['Categoria'] = e_cat
                          encontrado = True
                          break
                  if not encontrado:
                      st.session_state.edit_ingredientes.append({"Categoria": e_cat, "Ingrediente": insumo_nombre, "Cantidad_Base": e_cant, "Unidad": e_uni.strip()})
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

# === PESTAÑA 4: CATÁLOGO DE INSUMOS ===
with tab4:
    st.subheader("🍎 Gestor del Catálogo Maestro")
    st.info("Al modificar un insumo aquí, se actualizará automáticamente en **todas las recetas** donde haya sido utilizado históricamente.")
    
    if not catalogo_maestro:
        st.write("El catálogo está vacío. Agrega recetas primero.")
    else:
        insumo_a_editar = st.selectbox("Seleccionar Insumo para Editar", sorted(list(catalogo_maestro.keys())), key="cat_edit_sel")
        
        if insumo_a_editar:
            datos_actuales = catalogo_maestro[insumo_a_editar]
            
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1: nuevo_nombre_insumo = st.text_input("Nombre del Insumo", value=insumo_a_editar, key="cat_nom")
            with col_c2: nueva_unidad_insumo = st.text_input("Unidad Predeterminada", value=datos_actuales["Unidad"], key="cat_uni")
            with col_c3:
                try: idx_cat_cat = CATEGORIAS.index(datos_actuales["Categoria"])
                except ValueError: idx_cat_cat = CATEGORIAS.index("General")
                nueva_cat_insumo = st.selectbox("Categoría", CATEGORIAS, index=idx_cat_cat, key="cat_cat")
                
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

# === PESTAÑA 5: COMPRAS POR TIENDA ===
with tab5:
    st.subheader("🛒 Listas de Compras por Tienda")
    st.write("Crea listas permanentes para compras de insumos generales o mayoreo (ej. Sam's USA, HEB, Central de Abastos).")
    
    df_listas = cargar_listas()
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tiendas_existentes = sorted(df_listas['Tienda'].unique().tolist()) if not df_listas.empty else []
        tienda_sel = st.selectbox("Seleccionar Tienda", ["➕ Nueva Tienda..."] + tiendas_existentes)
    with col_t2:
        if tienda_sel == "➕ Nueva Tienda...":
            tienda_activa = st.text_input("Nombre de la nueva tienda (ej. Sam's USA)")
        else:
            tienda_activa = tienda_sel

    if tienda_activa:
        st.markdown(f"### Lista de: **{tienda_activa}**")
        df_tienda = df_listas[df_listas['Tienda'] == tienda_activa].copy()

        st.write("Añadir un insumo a la lista de esta tienda:")
        col_ti1, col_ti2 = st.columns([3, 1])
        with col_ti1:
            insumo_agregar = st.selectbox("Buscar insumo del catálogo", lista_opciones_insumos, key="tienda_insumo")
        with col_ti2:
            cant_agregar = st.number_input("Cantidad a agregar", min_value=0.01, value=1.0, step=1.0, key="tienda_cant")

        if st.button("➕ Agregar a la tienda"):
            if insumo_agregar != "➕ Crear Nuevo Insumo...":
                datos_insumo = catalogo_maestro[insumo_agregar]
                if insumo_agregar in df_tienda['Ingrediente'].values:
                    idx = df_listas[(df_listas['Tienda'] == tienda_activa) & (df_listas['Ingrediente'] == insumo_agregar)].index
                    df_listas.loc[idx, 'Cantidad'] += cant_agregar
                else:
                    nuevo_item = pd.DataFrame([{
                        "Tienda": tienda_activa,
                        "Ingrediente": insumo_agregar,
                        "Cantidad": cant_agregar,
                        "Unidad": datos_insumo["Unidad"],
                        "Categoria": datos_insumo["Categoria"]
                    }])
                    df_listas = pd.concat([df_listas, nuevo_item], ignore_index=True)
                
                guardar_listas(df_listas)
                st.success(f"{insumo_agregar} añadido a la lista.")
                st.rerun()
            else:
                st.warning("Selecciona un insumo existente. Si necesitas uno nuevo, agrégalo en la pestaña 'Nueva Receta'.")

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
                df_listas = df_listas[df_listas['Tienda'] != tienda_activa]
                edited_tienda['Tienda'] = tienda_activa
                df_listas = pd.concat([df_listas, edited_tienda], ignore_index=True)
                guardar_listas(df_listas)
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
                fig, ax = plt.subplots(figsize=(10, max(4, len(edited_tienda) * 0.4 + 2))) 
                ax.axis('off'); ax.axis('tight')
                ax.set_title(f"MEDHER BANQUETES Y MÁS\nLista de Compras: {tienda_activa.upper()}\n", fontsize=12, fontweight='bold', color='#2c3e50', pad=20)
                
                edited_sorted = edited_tienda.sort_values(by="Categoria")
                table_data = [[row['Categoria'], row['Ingrediente'], str(row['Cantidad']), str(row['Unidad'])] for _, row in edited_sorted.iterrows()]
                
                table = ax.table(cellText=table_data, colLabels=["Categoría", "Ingrediente", "Cantidad", "Unidad"], loc='center', cellLoc='center', colColours=['#2c3e50']*4)
                table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1.2, 1.5)
                for key, cell in table.get_celld().items():
                    cell.set_edgecolor('#bdc3c7')
                    if key[0] == 0: cell.set_text_props(color='white', fontweight='bold'); cell.set_facecolor('#2c3e50')
                    else: cell.set_facecolor('#ecf0f1' if key[0] % 2 == 0 else 'white')
                buf = io.BytesIO()
                plt.savefig(buf, format='jpg', bbox_inches='tight', dpi=300); plt.close(fig); buf.seek(0)
                return buf

            st.download_button("📥 Guardar Lista en Imagen (JPG)", data=generar_jpg_tienda(), file_name=f"Compras_{tienda_activa}.jpg", mime="image/jpeg")