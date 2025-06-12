# Version con LOGs integrados y visibles en consola WEB

import streamlit as st
import pyodbc
import datetime
import os
import json
import pandas as pd

datetime_format = "%Y-%m-%d %H:%M:%S.%f"
# Ruta del archivo
ruta_log = "log.json"

st.set_page_config(page_title="App SQL Server", layout="wide")
st.title("🔗 Conexión a SQL Server - Entorno TEST")

# Variables de sesión
if "conn" not in st.session_state:
    st.session_state.conn = None
if "cursor" not in st.session_state:
    st.session_state.cursor = None
if "database" not in st.session_state:
    st.session_state.database = None
if "tables" not in st.session_state:
    st.session_state.tables = []
if "connected" not in st.session_state:
    st.session_state.connected = False

def cargar_log(ruta_archivo):
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# Cargar datos del log
log_registros = cargar_log(ruta_log)

def conectar(usuario, password):
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER=172.29.5.6;"
        f"UID={usuario};"
        f"PWD={password};"
    )
    st.session_state.conn = pyodbc.connect(conn_str, autocommit=True)
    st.session_state.cursor = st.session_state.conn.cursor()
    st.session_state.connected = True

def desconectar():
    if st.session_state.conn:
        st.session_state.cursor.close()
        st.session_state.conn.close()
    st.session_state.conn = None
    st.session_state.cursor = None
    st.session_state.connected = False
    st.session_state.database = None
    st.session_state.tables = []

def guardar_log(tabla, columnas, valores):
    log_entry = {
        "timestamp": datetime.datetime.now().strftime(datetime_format)[:-3],
        "tabla": tabla,
        "registro": dict(zip(columnas, valores))
    }

    log_path = "log.json"

    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    data.append(log_entry)

    with open(log_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)    

# Panel de conexión
with st.sidebar:
    st.subheader("🔐 Conexión")
    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Conectar"):
        conectar(usuario, password)
    if st.session_state.connected:
        st.success("✅ Conectado")
        if st.button("Desconectar"):
            desconectar()
            st.warning("🔌 Desconectado")

# Crear las pestañas principales
tab1, tab2 = st.tabs(["📝 Edición de Tablas", "📋 Registro de Logs"])

# Contenido de la primera pestaña (Edición de Tablas)
with tab1:
    if st.session_state.connected:
        st.subheader("📂 Selección de Base de Datos")
        st.session_state.cursor.execute("SELECT name FROM sys.databases")
        bases = [row[0] for row in st.session_state.cursor.fetchall()]
        
        # Establecer 'eCommerce' como predeterminada si existe
        default_db_index = 0
        if 'eCommerce' in bases:
            default_db_index = bases.index('eCommerce')
        
        base_seleccionada = st.selectbox(
            "Elige una base de datos:",
            bases,
            index=default_db_index,
            key="db_select"
        )

        if base_seleccionada:
            st.session_state.database = base_seleccionada
            st.session_state.cursor.execute(f"USE {base_seleccionada}")
            st.session_state.cursor.execute("SELECT table_name FROM INFORMATION_SCHEMA.TABLES")
            tablas = [row[0] for row in st.session_state.cursor.fetchall()]
            tabla_seleccionada = st.selectbox("Elige una tabla:", tablas, key="table_select")

            # Paso 1: identificar columnas tipo datetime en la tabla
            st.session_state.cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{tabla_seleccionada}'
            """)
            column_types = {row[0]: row[1] for row in st.session_state.cursor.fetchall()}
            datetime_columns = [col for col, tipo in column_types.items() if tipo.lower() == "datetime"]

            # Paso 2: botón para cargar fecha actual en un campo datetime
            if st.button("📅 Cargar fecha actual en un campo", key="date_button"):
                if datetime_columns:
                    selected_col = st.selectbox("Seleccioná el campo de tipo fecha:", datetime_columns, key="date_col_select")
                    ahora = datetime.datetime.now().strftime(datetime_format)[:-3]  # Quita microsegundos extra
                    st.session_state[f"{tabla_seleccionada}_{selected_col}"] = ahora
                    st.success(f"Se cargó la fecha actual en el campo '{selected_col}'")
                else:
                    st.warning("Esta tabla no tiene campos de tipo fecha (`datetime`).")

            if tabla_seleccionada:
                st.subheader(f"📝 Insertar en tabla: `{tabla_seleccionada}`")

                # Obtener columnas y metadatos
                st.session_state.cursor.execute(f"SELECT TOP 0 * FROM {tabla_seleccionada}")
                columnas = [column[0] for column in st.session_state.cursor.description]
                col_metadata = [desc for desc in st.session_state.cursor.description]

                # Obtener las columnas que son PRIMARY KEY
                st.session_state.cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE TABLE_NAME = '{tabla_seleccionada}' 
                AND CONSTRAINT_NAME LIKE 'PK%'
                """)
                pk_columns = [row[0] for row in st.session_state.cursor.fetchall()]

                # Obtener el último registro ordenado por PK (si hay PKs)
                ultimo_registro = None
                if pk_columns:
                    order_by = ", ".join(pk_columns)
                    st.session_state.cursor.execute(f"SELECT TOP 1 * FROM {tabla_seleccionada} ORDER BY {order_by} DESC")
                    ultimo_registro = st.session_state.cursor.fetchone()

                # Crear formulario dinámico
                col1, col2 = st.columns([2, 1])

                with col1.form("form_insertar"):
                    valores = []
                    pk_values = {}  # Almacenará los valores de las PKs para validación

                    for i, col in enumerate(columnas):
                        tipo_sql = col_metadata[i][1]
                        field_key = f"{tabla_seleccionada}_{col}"

                        # Sugerir siguiente valor para PKs numéricas (si es el caso)
                        default_value = ""
                        if col in pk_columns and ultimo_registro:
                            last_value = ultimo_registro[i]
                            if isinstance(last_value, (int, float)):
                                default_value = str(last_value + 1)
                            elif isinstance(last_value, str) and last_value.isdigit():
                                default_value = str(int(last_value) + 1)

                        if tipo_sql == 93:  # DATETIME
                            if field_key not in st.session_state:
                                ahora = datetime.datetime.now().strftime(datetime_format)[:-3]
                                st.session_state[field_key] = ahora

                            val = st.text_input(
                                f"{col} (datetime)", 
                                value=st.session_state[field_key], 
                                key=field_key
                            )
                            valores.append(val)
                        else:
                            val = st.text_input(
                                f"{col}", 
                                value=default_value if col in pk_columns else "", 
                                key=field_key
                            )
                            valores.append(val)
                        
                        # Si es una PK, guardamos el valor para validación
                        if col in pk_columns:
                            pk_values[col] = val

                    submitted = st.form_submit_button("Guardar")

                    if submitted:
                        # Validar PKs antes de insertar
                        pk_exists = False
                        error_messages = []
                        
                        for pk_col, pk_val in pk_values.items():
                            if not pk_val:  # Si la PK está vacía
                                error_messages.append(f"⚠️ La clave primaria '{pk_col}' no puede estar vacía")
                                continue
                                
                            # Verificar si el valor ya existe en la tabla
                            query = f"SELECT COUNT(*) FROM {tabla_seleccionada} WHERE {pk_col} = ?"
                            st.session_state.cursor.execute(query, pk_val)
                            count = st.session_state.cursor.fetchone()[0]
                            
                            if count > 0:
                                error_messages.append(f"❌ El valor '{pk_val}' ya existe en la columna PK '{pk_col}'")
                                pk_exists = True
                        
                        if error_messages:
                            for msg in error_messages:
                                st.error(msg)
                        else:
                            # Solo insertar si no hay errores
                            placeholders = ", ".join(["?"] * len(columnas))
                            query = f"INSERT INTO {tabla_seleccionada} ({', '.join(columnas)}) VALUES ({placeholders})"
                            try:
                                st.session_state.cursor.execute(query, valores)
                                st.success("✅ Registro insertado exitosamente")
                                guardar_log(tabla_seleccionada, columnas, valores)
                            except Exception as e:
                                st.error(f"Error al insertar: {str(e)}")

                with col2:
                    # Mostrar último registro (si hay PKs)
                    if pk_columns:
                        try:
                            # Verificar si hay registros y si tenemos la descripción de columnas
                            if ultimo_registro and st.session_state.cursor.description:
                                st.info("📌 Último registro (ordenado por PK):")
                                datos = {}
                                for desc, val in zip(st.session_state.cursor.description, ultimo_registro):
                                    if desc:  # Asegurarse que la descripción no es None
                                        datos[desc[0]] = val
                                st.json(datos)
                                
                                # Mostrar sugerencia para siguiente PK numérica
                                for pk_col in pk_columns:
                                    try:
                                        idx = columnas.index(pk_col)
                                        last_value = ultimo_registro[idx]
                                        if isinstance(last_value, (int, float)):
                                            st.write(f"Siguiente {pk_col}: **{last_value + 1}**")
                                        elif isinstance(last_value, str) and last_value.isdigit():
                                            st.write(f"Siguiente {pk_col}: **{int(last_value) + 1}**")
                                    except (ValueError, IndexError):
                                        st.write(f"No se pudo determinar siguiente valor para {pk_col}")
                            else:
                                st.info("ℹ️ No hay registros en esta tabla todavía")
                                # Sugerir valor inicial para PKs numéricas
                                for pk_col in pk_columns:
                                    st.write(f"Primer {pk_col}: **1**")  # O el valor inicial que prefieras
                        except Exception as e:
                            st.error(f"Error al mostrar último registro: {str(e)}")
                        
                        # Mostrar información sobre las PKs
                        st.info("🔑 Claves primarias:")
                        for pk in pk_columns:
                            st.write(f"- {pk}")
    else:
        st.warning("🔒 Por favor, conéctese a la base de datos primero")

# Contenido de la segunda pestaña (Registro de Logs)
with tab2:
    st.title("📋 Registro de Actividad")
    st.info("🕒 Historial de los últimos registros agregados:")
    
    # Mostrar los últimos 20 registros (los más recientes arriba)
    for entrada in reversed(log_registros[-20:]):
        st.markdown(f"**🗓️ {entrada['timestamp']}** | 🗂️ Tabla: `{entrada['tabla']}`")
        with st.expander("📋 Ver detalle del registro"):
            registro = entrada['registro']
            for campo, valor in registro.items():
                st.write(f"**{campo}**: {valor}")
        st.divider()
    
    if not log_registros:
        st.info("No hay registros en el log todavía.")