# -*- coding: utf-8 -*-
"""
Sistema Operativo de Banquetes - Medher (Persistencia en GitHub)
"""

import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import io

FILE_PATH = "recetas_base.csv"

# --- 1. INICIALIZACIÓN DE BASE DE DATOS ---
if not os.path.exists(FILE_PATH):
  df_inicial = pd.DataFrame(
      columns=["Receta", "Platillos_Base", "Ingrediente", "Cantidad_Base", "Unidad"]
  )
  df_inicial.to_csv(FILE_PATH, index=False)


def cargar_recetas():
  return pd.read_csv(FILE_PATH)


def guardar_recetas(df):
  # 1. Guardar localmente en el servidor temporal
  df.to_csv(FILE_PATH, index=False)
  
  # 2. Sincronizar permanentemente con GitHub si la llave existe
  if "GITHUB_TOKEN" in st.secrets:
    try:
      from github import Github
      # Conectar a GitHub usando la llave secreta
      g = Github(st.secrets["GITHUB_TOKEN"])
      # Entrar a tu repositorio exacto
      repo = g.get_repo("Edchvz/Medher-Banquetes")
      
      # Obtener el archivo viejo de la nube
      contents = repo.get_contents(FILE_PATH, ref="main")
      
      # Convertir la nueva tabla a formato de texto CSV
      csv_data = df.to_csv(index=False)
      
      # Sobrescribir el archivo en la nube
      repo.update_file(
          contents.path,
          "Sincronización automática desde la App Web",
          csv_data,
          contents.sha,
          branch="main"
      )
    except Exception as e:
      st.error(f"Error al sincronizar con la nube maestra: {e}")


# --- CONFIGURACIÓN DE PÁGINA E ICONOS ---
st.set_page_config(
    page_title="Medher Banquetes y Más", 
    page_icon="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/icono_medher.png", 
    layout="centered"
)

st.markdown(
    """
    <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/icono_medher.png">
    <link rel="shortcut icon" href="https://raw.githubusercontent.com/Edchvz/Medher-Banquetes/main/icono_medher.png">
    """,
    unsafe_allow_html=True
)

st.title("🍳 Medher Banquetes y Más")
st.caption("Sistema Operativo de Gestión y Escalado de Recetas")

# Pestañas de navegación
tab1, tab2, tab3 = st.tabs(["📊 Escalar Producción", "➕ Nueva Receta", "🛠️ Modificar / Eliminar"])

df_actual = cargar_recetas()
recetas_unicas = sorted(df_actual["Receta"].unique().tolist()) if not df_actual.empty else []

# === PESTAÑA 1: CÁLCULO Y EXPORTAR A JPG ===
with tab1:
  st.subheader("Cálculo de Insumos por Evento")

  if not recetas_unicas:
    st.info("No hay recetas registradas todavía. Ve a la pestaña 'Nueva Receta'.")
  else:
    col1, col2 = st.columns(2)
    with col1:
      receta_sel = st.selectbox("Seleccionar Receta", recetas_unicas, key="calc_receta")
    with col2:
      platillos_objetivo = st.number_input("Platillos a preparar", min_value=1.0, value=10.0, step=1.0, key="calc_platillos")

    if st.button("Calcular Lista de Producción", type="primary"):
      filtro = df_actual["Receta"].astype(str).str.lower() == receta_sel.lower()
      receta_df = df_actual[filtro].copy()

      if not receta_df.empty:
        platillos_base = receta_df["Platillos_Base"].iloc[0]
        factor = platillos_objetivo / platillos_base
        receta_df["Cantidad_Requerida"] = (receta_df["Cantidad_Base"] * factor).round(2)

        st.success(f"Lista calculada para {int(platillos_objetivo)} platillos (Base: {int(platillos_base)})")

        st.session_state.tabla_calculada = receta_df[["Ingrediente", "Cantidad_Requerida", "Unidad"]].rename(columns={"Cantidad_Requerida": "Cantidad"})
        st.session_state.receta_activa = receta_sel
        st.session_state.platillos_activos = int(platillos_objetivo)

    if "tabla_calculada" in st.session_state and not st.session_state.tabla_calculada.empty:
      st.dataframe(st.session_state.tabla_calculada, use_container_width=True)

      st.markdown("---")
      st.write("### Opciones de Exportación")

      texto_wpp = f"--- MEDHER BANQUETES Y MÁS ---\n"
      texto_wpp += f"Receta: {st.session_state.receta_activa.upper()}\n"
      texto_wpp += f"Platillos a preparar: {st.session_state.platillos_activos}\n"
      texto_wpp += f"----------------------\n"
      texto_wpp += f"LISTA DE INGREDIENTES:\n"
      for _, row in st.session_state.tabla_calculada.iterrows():
        texto_wpp += f" • {row['Ingrediente']}: {row['Cantidad']} {row['Unidad']}\n"

      st.text_area("Texto formateado (para WhatsApp o Notas):", texto_wpp, height=150)

      def generar_jpg():
        df_t = st.session_state.tabla_calculada
        fig, ax = plt.subplots(figsize=(8, max(4, len(df_t) * 0.4 + 2)))
        ax.axis('off')
        ax.axis('tight')

        ax.set_title(
            f"MEDHER BANQUETES Y MÁS\nOrden de Producción: {st.session_state.receta_activa.upper()}\nPlatillos: {st.session_state.platillos_activos}\n",
            fontsize=12, fontweight='bold', color='#2c3e50', pad=20
        )

        table_data = [[row['Ingrediente'], str(row['Cantidad']), str(row['Unidad'])] for _, row in df_t.iterrows()]
        col_labels = ["Ingrediente", "Cantidad", "Unidad"]

        table = ax.table(
            cellText=table_data,
            colLabels=col_labels,
            loc='center',
            cellLoc='center',
            colColours=['#2c3e50', '#2c3e50', '#2c3e50']
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)

        for key, cell in table.get_celld().items():
          cell.set_edgecolor('#bdc3c7')
          if key[0] == 0:
            cell.set_text_props(color='white', fontweight='bold')
            cell.set_facecolor('#2c3e50')
          else:
            cell.set_facecolor('#ecf0f1' if key[0] % 2 == 0 else 'white')

        buf = io.BytesIO()
        plt.savefig(buf, format='jpg', bbox_inches='tight', dpi=300)
        plt.close(fig)
        buf.seek(0)
        return buf

      st.download_button(
          label="📥 Guardar Reporte en Imagen (JPG)",
          data=generar_jpg(),
          file_name=f"Produccion_{st.session_state.receta_activa}_{st.session_state.platillos_activos}pax.jpg",
          mime="image/jpeg"
      )

# === PESTAÑA 2: NUEVA RECETA ===
with tab2:
  st.subheader("Registrar Nueva Receta")
  nombre_nueva = st.text_input("Nombre de la Receta", key="nombre_nueva_receta")
  base_nueva = st.number_input("Platillos Base (Rendimiento)", min_value=1.0, value=10.0, step=1.0, key="base_nueva_receta")

  st.markdown("---")
  st.write("Añadir Insumos:")

  if "temp_ingredientes" not in st.session_state:
    st.session_state.temp_ingredientes = []

  col_i1, col_i2, col_i3 = st.columns(3)
  with col_i1:
    insumo = st.text_input("Insumo", key="input_insumo")
  with col_i2:
    cant_insumo = st.number_input("Cantidad", min_value=0.01, value=1.0, step=0.1, key="input_cant")
  with col_i3:
    unidad_insumo = st.text_input("Unidad", key="input_uni")

  if st.button("+ Agregar Insumo a la Lista"):
    if insumo.strip() and unidad_insumo.strip():
      st.session_state.temp_ingredientes.append({
          "Ingrediente": insumo.strip(), "Cantidad_Base": cant_insumo, "Unidad": unidad_insumo.strip(),
      })
      st.success(f"Insumo agregado: {insumo}")
    else:
      st.warning("Completa el nombre del insumo y la unidad.")

  if st.session_state.temp_ingredientes:
    st.dataframe(pd.DataFrame(st.session_state.temp_ingredientes), use_container_width=True)

    if st.button("Guardar Receta en Base de Datos"):
      if not nombre_nueva.strip():
        st.error("Asigna un nombre a la receta.")
      else:
        df_verificar = cargar_recetas()
        if not df_verificar.empty and (df_verificar['Receta'].astype(str).str.lower() == nombre_nueva.strip().lower()).any():
          st.error("La receta ya existe en la base de datos.")
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
    with col_m1:
      cargar_edicion = st.button("Cargar para Editar")
    with col_m2:
      eliminar_completa = st.button("🗑️ ELIMINAR RECETA COMPLETA")

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
        st.session_state.edit_ingredientes = df_receta_edit[['Ingrediente', 'Cantidad_Base', 'Unidad']].to_dict('records')
        st.session_state.current_receta_loaded = receta_mod

      st.write("Ingredientes actuales:")
      st.dataframe(pd.DataFrame(st.session_state.edit_ingredientes), use_container_width=True)

      col_e1, col_e2, col_e3 = st.columns(3)
      with col_e1:
        e_ing = st.text_input("Nuevo/Editar Insumo", key="e_ing")
      with col_e2:
        e_cant = st.number_input("Cantidad Base", min_value=0.01, value=1.0, step=0.1, key="e_cant")
      with col_e3:
        e_uni = st.text_input("Unidad", key="e_uni")

      col_btn1, col_btn2 = st.columns(2)
      with col_btn1:
        if st.button("➕ Agregar Insumo a la Edición"):
          if e_ing.strip() and e_uni.strip():
            st.session_state.edit_ingredientes.append({"Ingrediente": e_ing.strip(), "Cantidad_Base": e_cant, "Unidad": e_uni.strip()})
            st.rerun()
          else:
            st.warning("Completa los datos del insumo.")
      with col_btn2:
        ing_a_quitar = st.selectbox("Selecciona ingrediente a quitar", [item['Ingrediente'] for item in st.session_state.edit_ingredientes] if st.session_state.edit_ingredientes else ["Ninguno"])
        if st.button("➖ Quitar Insumo Seleccionado") and ing_a_quitar != "Ninguno":
          st.session_state.edit_ingredientes = [item for item in st.session_state.edit_ingredientes if item['Ingrediente'] != ing_a_quitar]
          st.rerun()

      if st.button("💾 Sobrescribir y Guardar Cambios Definitivos", type="primary"):
        if not nuevo_nombre_receta.strip():
          st.error("El nombre de la receta no puede estar vacío.")
        elif not st.session_state.edit_ingredientes:
          st.error("La receta debe tener al menos un ingrediente.")
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