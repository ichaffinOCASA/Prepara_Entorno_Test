import streamlit as st
import pyodbc
import datetime

datetime_format = "%Y-%m-%d %H:%M:%S.%f"

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

# Si está conectado, mostrar bases de datos
if st.session_state.connected:
    st.subheader("📂 Selección de Base de Datos")
    st.session_state.cursor.execute("SELECT name FROM sys.databases")
    bases = [row[0] for row in st.session_state.cursor.fetchall()]
    base_seleccionada = st.selectbox("Elige una base de datos:", bases)

    if base_seleccionada:
        st.session_state.database = base_seleccionada
        st.session_state.cursor.execute(f"USE {base_seleccionada}")
        st.session_state.cursor.execute("SELECT table_name FROM INFORMATION_SCHEMA.TABLES")
        tablas = [row[0] for row in st.session_state.cursor.fetchall()]
        tabla_seleccionada = st.selectbox("Elige una tabla:", tablas)

        # Paso 1: identificar columnas tipo datetime en la tabla
        st.session_state.cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{tabla_seleccionada}'
        """)
        column_types = {row[0]: row[1] for row in st.session_state.cursor.fetchall()}
        datetime_columns = [col for col, tipo in column_types.items() if tipo.lower() == "datetime"]

        # Paso 2: botón para cargar fecha actual en un campo datetime
        if st.button("📅 Cargar fecha actual en un campo"):
            if datetime_columns:
                selected_col = st.selectbox("Seleccioná el campo de tipo fecha:", datetime_columns)
                ahora = datetime.datetime.now().strftime(datetime_format)[:-3]  # Quita microsegundos extra
                st.session_state[f"{tabla_seleccionada}_{selected_col}"] = ahora
                st.success(f"Se cargó la fecha actual en el campo '{selected_col}'")
            else:
                st.warning("Esta tabla no tiene campos de tipo fecha (`datetime`).")


        if tabla_seleccionada:
            st.subheader(f"📝 Insertar en tabla: `{tabla_seleccionada}`")

            # Obtener columnas
            st.session_state.cursor.execute(f"SELECT TOP 0 * FROM {tabla_seleccionada}")
            columnas = [column[0] for column in st.session_state.cursor.description]

            # Crear formulario dinámico
            col1, col2 = st.columns([2, 1])

            with col1.form("form_insertar"):
                valores = []
                col_metadata = [desc for desc in st.session_state.cursor.description]

                for i, col in enumerate(columnas):
                    tipo_sql = col_metadata[i][1]
                    field_key = f"{tabla_seleccionada}_{col}"

                    if tipo_sql == 93:  # DATETIME
                        # Solo setear la fecha actual si no existe todavía
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
                        val = st.text_input(f"{col}", key=field_key)
                        valores.append(val)

                submitted = st.form_submit_button("Guardar")

                if submitted:
                    placeholders = ", ".join(["?"] * len(columnas))
                    query = f"INSERT INTO {tabla_seleccionada} ({', '.join(columnas)}) VALUES ({placeholders})"
                    st.session_state.cursor.execute(query, valores)
                    st.success("✅ Registro insertado exitosamente")

            with col2:
                if st.button("🎲 Ver ejemplo aleatorio"):
                    st.session_state.cursor.execute(f"SELECT TOP 1 * FROM {tabla_seleccionada} ORDER BY NEWID()")
                    resultado = st.session_state.cursor.fetchone()
                    if resultado:
                        st.info("🧾 Registro ejemplo:")
                        datos = {desc[0]: val for desc, val in zip(st.session_state.cursor.description, resultado)}
                        st.json(datos)
