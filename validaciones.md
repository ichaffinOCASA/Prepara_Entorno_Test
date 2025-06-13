# Documentación de Validaciones Disponibles
# 
# Estructura básica:
# validaciones:
#   - base: nombre_base_datos    # (Requerido) Nombre de la base de datos
#     tabla: nombre_tabla        # (Requerido) Nombre de la tabla
#     campo: nombre_campo        # (Requerido) Nombre del campo/columna
#
# Validaciones disponibles:
#
# 1. Validación de campo requerido:
#    requerido: true|false       # Si es true, el campo no puede estar vacío
#
# 2. Validación de tipo de dato:
#    tipo: string|int|decimal    # Valida el tipo de dato del campo
#      - string: texto cualquiera
#      - int: número entero
#      - decimal: número con decimales
#
# 3. Validación de formato:
#    formato: email|numerico|alfanumerico  # Valida el formato del campo
#      - email: valida formato de email
#      - numerico: solo dígitos (0-9)
#      - alfanumerico: letras y números
#
# 4. Validación de longitud:
#    max_caracteres: X           # Longitud máxima en caracteres
#               # Longitud mínima en caracteres
#    max_digitos: X              # Máximo dígitos para números (incluye decimales)
#
# 5. Validación de rango numérico:
#    min_valor: X                # Valor mínimo para números
#    max_valor: X                # Valor máximo para números
#
# 6. Validación de valores específicos:
#    valores_permitidos: [X, Y, Z] # Lista de valores aceptados
#
# Ejemplos completos:
validaciones:
  # Ejemplo 1: Campo numérico requerido con máximo 10 caracteres
  - base: eCommerce
    tabla: Usuario
    campo: Clave
    tipo: int
    max_caracteres: 10
    requerido: true
    formato: numerico

  # Ejemplo 2: Email válido entre 5 y 100 caracteres
  - base: eCommerce
    tabla: Usuario
    campo: Email
    tipo: string
    formato: email
    min_caracteres: 5
    max_caracteres: 100
    requerido: true

  # Ejemplo 3: Número decimal entre 0 y 9999.99
  - base: Ventas
    tabla: Productos
    campo: Precio
    tipo: decimal
    min_valor: 0
    max_valor: 9999.99
    max_digitos: 6  # Incluye 2 decimales (9999.99)

  # Ejemplo 4: Selección entre valores específicos
  - base: RRHH
    tabla: Empleados
    campo: Departamento
    valores_permitidos: [Ventas, IT, Administración, Logística]
    requerido: true