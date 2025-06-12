import streamlit as st
import pyodbc

st.set_page_config(page_title="App SQL Server", layout="wide")
st.title("🔗 Conexión a SQL Server - App Básica")

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

        if tabla_seleccionada:
            st.subheader(f"📝 Insertar en tabla: `{tabla_seleccionada}`")

            # Obtener columnas
            st.session_state.cursor.execute(f"SELECT TOP 0 * FROM {tabla_seleccionada}")
            columnas = [column[0] for column in st.session_state.cursor.description]

            # Crear formulario dinámico
            with st.form("form_insertar"):
                valores = []
                for col in columnas:
                    val = st.text_input(f"{col}")
                    valores.append(val)
                submitted = st.form_submit_button("Guardar")

                if submitted:
                    placeholders = ", ".join(["?"] * len(columnas))
                    query = f"INSERT INTO {tabla_seleccionada} ({', '.join(columnas)}) VALUES ({placeholders})"
                    st.session_state.cursor.execute(query, valores)
                    st.success("✅ Registro insertado exitosamente")
