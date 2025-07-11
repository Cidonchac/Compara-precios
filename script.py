import pandas as pd
from datetime import datetime
import os
archivo = input("Introduce la ruta al archivo Excel: ").strip()

# Cargar archivo
if not os.path.exists(archivo):
    print("No se encuentra el archivo.")
    exit()

df = pd.read_excel(archivo)
df["Unidad"] = df["Unidad"].astype(str).str.strip().str.lower()

# Introducir detalles clave
while True:
    producto = None
    local = None
    marca = None
    cantidad = None
    unidad = None
    envase = None
    idx = None
    print("\n¿Quieres introducir un nuevo precio? (s/n)")
    introducir_precio = input().strip().lower() == 's'
    if not introducir_precio:
        break

    if introducir_precio:
        print("\nIntroduce los datos del nuevo precio:")
        producto = input("Producto: ").strip()
        local = input("Local: ").strip()
        marca = input("Marca: ").strip()
        cantidad = input("Cantidad: ").strip()
        unidad = input("Unidad: ").strip().lower()
        envase = input("Envase: ").strip()

    cantidad = str(cantidad).strip()

    # Buscar fila existente
    filtro = (
        (df["Producto"].str.strip() == producto) &
        (df["Local"].str.strip() == local) &
        (df["Marca"].str.strip() == marca) &
        (df["Cantidad"].astype(str).str.strip() == cantidad) &
        (df["Unidad"].astype(str).str.strip() == unidad) &
        (df["Envase"].astype(str).str.strip() == envase)
    )

    if not df[filtro].empty:
        idx = df[filtro].index[0]
    else:
        print("No se ha encontrado ese producto registrado. ¿Quieres añadirlo como nueva fila? (s/n)")
        if input().lower() != "s":
            print("Proceso cancelado.")
        else:
            nueva_fila = {
                "Producto": producto,
                "Local": local,
                "Marca": marca,
                "Enlace": "",
                "Cantidad": cantidad,
                "Unidad": unidad,
                "Envase": envase,
                "Categoría": "",
            }
            df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
            idx = df.index[-1]

        # Pedir precio y fecha
        while True:
            precio_input = input("Precio (sin €): ")
            try:
                precio = float(precio_input)
                break
            except ValueError:
                print("Precio no válido.")
                if input("¿Intentar de nuevo? (s/n): ").lower() != "s":
                    print("Proceso cancelado.")
                    exit()

        fecha_input = input("Fecha (dd/mm/yyyy) [vacío = hoy]: ").strip()
        if not fecha_input:
            fecha_input = datetime.today().strftime("%d/%m/%Y")

        try:
            fecha_dt = datetime.strptime(fecha_input, "%d/%m/%Y")
        except ValueError:
            print("Fecha no válida.")
            exit()

        columna_precio = f"Precio {fecha_dt.strftime('%m/%Y')}"

        if columna_precio in df.columns:
            if pd.isna(df.at[idx, columna_precio]):
                # Celda vacía: asigna el precio sin preguntar
                df.at[idx, columna_precio] = f"{precio:.2f} €"
                print(f"Precio añadido para {producto} - {local} en {columna_precio}.")
            else:
                # Celda con valor: pregunta si quiere sobrescribir
                sobrescribir = input(f"Ya hay precio para {columna_precio}. ¿Sobrescribir? (s/n): ").lower()
                if sobrescribir == "s":
                    df.at[idx, columna_precio] = f"{precio:.2f} €"
                    print(f"Precio sobrescrito para {producto} - {local} en {columna_precio}.")
                else:
                    print("No se ha modificado.")
                    exit()
        else:
            # Si la columna no existe, la creamos y asignamos el precio
            df[columna_precio] = None
            df.at[idx, columna_precio] = f"{precio:.2f} €"
            print(f"Columna {columna_precio} creada y precio añadido para {producto} - {local}.")

        # Guardar
        df.to_excel(archivo, index=False)
        print("\n¿Quieres añadir otro producto? (s/n)")
        if input().strip().lower() != 's':
            break

# Repetir





# Buscar local con mejores precios
print("\n¿Quieres buscar dónde comprar hoy el precio más bajo? (s/n)")
if input().lower() == "s":
    df = pd.read_excel(archivo)  # Volver a cargar datos actualizados

    import re

    # Crear un diccionario que mapea la fecha 'mm/yyyy' al nombre COMPLETO y EXACTO de la columna
    # Ejemplo: {'06/2025': 'Precio 06/2025 ', '05/2025': 'Precio_05/2025'}
    columnas_de_precios = {
        match.group(1): col
        for col in df.columns
        if col.strip().startswith("Precio") and (match := re.search(r"(\d{2}/\d{4})", col))
    }

    mes_actual = datetime.today().strftime("%m/%Y")
    columna_objetivo = None  # Inicializar la variable

    # Comprobar si el mes actual existe en nuestro diccionario de columnas
    if mes_actual in columnas_de_precios:
        # Si existe, usamos el nombre de columna EXACTO que guardamos
        columna_objetivo = columnas_de_precios[mes_actual]
        print(f"Usando la columna de precios del mes actual: '{columna_objetivo}'")
    else:
        # Si no, buscamos la fecha más cercana entre las disponibles
        print(f"No hay precios del mes actual ({mes_actual}). Buscando la fecha más cercana...")
        if not columnas_de_precios:
            print("Error: No se encontraron columnas de precios con formato 'Precio mm/yyyy' en el archivo.")
            exit()  # Salir si no hay ninguna columna de precios

        fechas_dt = {datetime.strptime(m, "%m/%Y"): nombre_col for m, nombre_col in columnas_de_precios.items()}
        fecha_actual_dt = datetime.strptime(mes_actual, "%m/%Y")

        # Encontrar la clave de fecha (objeto datetime) más cercana
        fecha_mas_cercana_dt = min(fechas_dt.keys(), key=lambda d: abs(d - fecha_actual_dt))

        # Usar esa clave para obtener el nombre de columna correcto del diccionario
        columna_objetivo = fechas_dt[fecha_mas_cercana_dt]
        print(f"Se usará la columna más cercana encontrada: '{columna_objetivo}'")

    df_precio_mes = df[~df[columna_objetivo].isna()].copy()

    def parse_precio(x):
        try:
            return float(str(x).replace("€", "").replace(",", ".").strip())
        except ValueError:
            return None

    df_precio_mes["precio_float"] = df_precio_mes[columna_objetivo].apply(parse_precio)

    locales_disponibles = sorted(df_precio_mes["Local"].dropna().str.strip().unique())

    todos_los_locales = df["Local"].dropna().str.strip().unique()

    locales_sin_precio = [loc for loc in todos_los_locales if loc not in locales_disponibles]

    if locales_sin_precio:
        print(f"\n⚠️ Aviso: Hay {len(locales_sin_precio)} locales sin precio en {columna_objetivo}.")
        print("Es recomendable actualizar los datos.")

    if not locales_disponibles:
        print("No hay locales con precios registrados para este mes.")
        exit()

    while True:
        print("\nLocales disponibles con precios registrados:")
        for i, local in enumerate(locales_disponibles, 1):
            print(f"{i}. {local}")

        try:
            seleccion = int(input("Selecciona el número del local a consultar: "))
            if seleccion < 1 or seleccion > len(locales_disponibles):
                print("Selección inválida.")
                continue
            local_busqueda = locales_disponibles[seleccion - 1].strip().lower()
        except ValueError:
            print("Entrada inválida.")
            continue

        min_precios = df_precio_mes.groupby(["Producto"])["precio_float"].min().reset_index()
        min_precios.rename(columns={"precio_float": "precio_min"}, inplace=True)

        df_merged = pd.merge(df_precio_mes, min_precios, on=["Producto"])

        df_local = df_merged[df_merged["Local"].str.strip().str.lower() == local_busqueda]

        df_local_minimos = df_local[abs(df_local["precio_float"] - df_local["precio_min"]) < 0.01]

        if df_local_minimos.empty:
            print(f"\nNo hay productos con precio mínimo en el local '{local_busqueda}' para {columna_objetivo}.")
        else:
            print(f"\n🛍️ Productos donde '{local_busqueda}' tiene el precio más bajo en {columna_objetivo}:")
            for _, fila in df_local_minimos.iterrows():
                print(f" - {fila['Producto']} ({fila['Marca']} - {fila['Cantidad']} {fila['Unidad']} - {fila['Envase']}): {fila['precio_float']:.2f} €")

        repetir = input("\n¿Quieres consultar otro local? (s/n): ").strip().lower()
        if repetir != "s":
            break
