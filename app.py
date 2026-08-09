# -*- coding: utf-8 -*-
"""
Created on Sat Aug  8 20:34:36 2026

@author: Edwin
"""

# -*- coding: utf-8 -*-
"""
Sistema Operativo de Banquetes - Medher (Versión Web para iOS / iPad / PC)
"""

import os
import pandas as pd
import streamlit as st

FILE_PATH = "recetas_base.csv"

# --- 1. INICIALIZACIÓN DE BASE DE DATOS ---
if not os.path.exists(FILE_PATH):
  df_inicial = pd.DataFrame(
      columns=[
          "Receta",
          "Platillos_Base",
          "Ingrediente",
          "Cantidad_Base",
          "Unidad",
      ]
  )
  df_inicial.to_csv(FILE_PATH, index=False)


def cargar_recetas():
  return pd.read_csv(FILE_PATH)


def guardar_recetas(df):
  df.to_csv(FILE_PATH, index=False)


# Configuración visual de la página
st.set_page_config(
    page_title="Medher Banquetes y Más", page_icon="🍳", layout="centered"
)

st.title("🍳 Medher Banquetes y Más")
st.caption("Sistema Operativo de Gestión y Escalado de Recetas")

# Pestañas de navegación táctiles ideales para iPad/iPhone
tab1, tab2, tab3 = st.tabs(
    ["📊 Escalar Producción", "➕ Nueva Receta", "🛠️ Modificar / Eliminar"]
)

df_actual = cargar_recetas()
recetas_unicas = (
    sorted(df_actual["Receta"].unique().tolist())
    if not df_actual.empty
    else []
)

# === PESTAÑA 1: ESCALAR PRODUCCIÓN ===
with tab1:
  st.subheader("Cálculo de Insumos por Evento")

  if not recetas_unicas:
    st.info("No hay recetas registradas todavía. Ve a la pestaña 'Nueva Receta'.")
  else:
    col1, col2 = st.columns(2)
    with col1:
      receta_sel = st.selectbox("Seleccionar Receta", recetas_unicas)
    with col2:
      platillos_objetivo = st.number_input(
          "Platillos a preparar", min_value=1.0, value=10.0, step=1.0
      )

    if st.button("Calcular Lista de Producción", type="primary"):
      filtro = df_actual["Receta"].astype(str).str.lower() == receta_sel.lower()
      receta_df = df_actual[filtro].copy()

      if not receta_df.empty:
        platillos_base = receta_df["Platillos_Base"].iloc[0]
        factor = platillos_objetivo / platillos_base
        receta_df["Cantidad_Requerida"] = (
            receta_df["Cantidad_Base"] * factor
        ).round(2)

        st.success(
            f"Lista calculada para {int(platillos_objetivo)} platillos (Base:"
            f" {int(platillos_base)})"
        )

        # Mostrar tabla limpia
        tabla_mostrar = receta_df[
            ["Ingrediente", "Cantidad_Requerida", "Unidad"]
        ].rename(columns={"Cantidad_Requerida": "Cantidad"})
        st.dataframe(tabla_mostrar, use_container_width=True)

        # Generar texto listo para WhatsApp (muy útil en celular)
        texto_wpp = f"--- MEDHER BANQUETES Y MÁS ---\n"
        texto_wpp += f"Receta: {receta_sel.upper()}\n"
        texto_wpp += f"Platillos: {int(platillos_objetivo)}\n"
        texto_wpp +="----------------------\n"
        for _, row in tabla_mostrar.iterrows():
          texto_wpp += (
              f" • {row['Ingrediente']}: {row['Cantidad']} {row['Unidad']}\n"
          )

        st.text_area(
            "Texto formateado para copiar (WhatsApp / Notas):",
            texto_wpp,
            height=150,
        )

# === PESTAÑA 2: NUEVA RECETA ===
with tab2:
  st.subheader("Registrar Nueva Receta")

  nombre_nueva = st.text_input("Nombre de la Receta")
  base_nueva = st.number_input(
      "Platillos Base (Rendimiento original)",
      min_value=1.0,
      value=10.0,
      step=1.0,
  )

  st.markdown("---")
  st.write("Agregando ingredientes a la receta temporal:")

  if "temp_ingredientes" not in st.session_state:
    st.session_state.temp_ingredientes = []

  col_i1, col_i2, col_i3 = st.columns(3)
  with col_i1:
    insumo = st.text_input("Insumo / Ingrediente")
  with col_i2:
    cant_insumo = st.number_input(
        "Cantidad Base", min_value=0.01, value=1.0, step=0.1
    )
  with col_i3:
    unidad_insumo = st.text_input("Unidad (kg, pzas, lt, etc.)")

  if st.button("Añadir Ingrediente a la Lista"):
    if insumo.strip() and unidad_insumo.strip():
      st.session_state.temp_ingredientes.append({
          "Ingrediente": insumo.strip(),
          "Cantidad_Base": cant_insumo,
          "Unidad": unidad_insumo.strip(),
      })
      st.success(f"Agregado: {insumo}")
    else:
      st.warning("Llena el nombre del insumo y la unidad.")

  if st.session_state.temp_ingredientes:
    st.dataframe(
        pd.DataFrame(st.session_state.temp_ingredientes),
        use_container_width=True,
    )

    if st.button("Guardar Receta Definitiva en la Base de Datos"):
      if not nombre_nueva.strip():
        st.error("Asigna un nombre a la receta.")
      else:
        nuevos_datos = [
            {
                "Receta": nombre_nueva.strip(),
                "Platillos_Base": base_nueva,
                **item,
            }
            for item in st.session_state.temp_ingredientes
        ]
        df_actualizado = (
            pd.concat([df_actual, pd.DataFrame(nuevos_datos)], ignore_index=True)
            if not df_actual.empty
            else pd.DataFrame(nuevos_datos)
        )
        guardar_recetas(df_actualizado)
        st.success(f"¡Receta '{nombre_nueva}' guardada con éxito!")
        st.session_state.temp_ingredientes = []
        st.rerun()

# === PESTAÑA 3: MODIFICAR / ELIMINAR ===
with tab3:
  st.subheader("Gestión de Recetas Existentes")
  if recetas_unicas:
    receta_mod = st.selectbox("Selecciona receta a gestionar", recetas_unicas)

    col_m1, col_m2 = st.columns(2)
    with col_m1:
      if st.button("🗑️ Eliminar Receta Completa", type="secondary"):
        df_limpio = df_actual[
            ~(df_actual["Receta"].astype(str).str.lower()
              == receta_mod.lower())
        ].reset_index(drop=True)
        guardar_recetas(df_limpio)
        st.success(f"Receta '{receta_mod}' eliminada.")
        st.rerun()
    # Ejemplo para incluir en tu Streamlit en la Pestaña 3
    if st.button("Guardar Cambios en la Receta"):
        # Filtra el df original eliminando la receta vieja
        df_nuevo = df_actual[df_actual['Receta'] != receta_mod]
        # Crea el nuevo dataframe con los datos editados y concatena
        # Luego guarda:
        guardar_recetas(pd.concat([df_nuevo, datos_editados]))
        st.success("¡Receta actualizada!")
        filtro_m = df_actual["Receta"].astype(str).str.lower() == receta_mod.lower()
        st.dataframe(df_actual[filtro_m], use_container_width=True)
  else:
    st.info("No hay recetas para modificar.")