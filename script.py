import pandas as pd
from datetime import datetime
import os

archivo = "/Users/cidonchac/Downloads/Comparador de precios.xlsx"

# Cargar archivo
if not os.path.exists(archivo):
    print("No se encuentra el archivo.")
    exit()

df = pd.read_excel(archivo)

# Introducir detalles clave
print("\n¿Quieres introducir un nuevo precio? (s/n)")
introducir_precio = input().strip().lower() == 's'

if introducir_precio:
    print("\nIntroduce los datos del nuevo precio:")
    producto = input("Producto: ").strip()
    local = input("Local: ").strip()
    marca = input("Marca: ").strip()
    formato = input("Formato: ").strip()

    # Buscar fila existente
    filtro = (
        (df["Producto"].str.strip() == producto) &
        (df["Local"].str.strip() == local) &
        (df["Marca"].str.strip() == marca) &
        (df["Formato"].str.strip() == formato)
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
                "Formato": formato,
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
            sobrescribir = input(f"Ya hay precio para {columna_precio}. ¿Sobrescribir? (s/n): ").lower()
            if sobrescribir != "s" and not pd.isna(df.at[idx, columna_precio]):
                print("No se ha modificado.")
                exit()
        else:
            df[columna_precio] = None

        df.at[idx, columna_precio] = f"{precio:.2f} €"

        # Guardar
        df.to_excel(archivo, index=False)
        print(f"Precio añadido para {producto} - {local} en {columna_precio}.")

# Buscar local con mejores precios
print("\n¿Quieres buscar dónde comprar hoy el precio más bajo? (s/n)")
if input().lower() == "s":
    df = pd.read_excel(archivo)  # Volver a cargar datos actualizados

    columnas_mes = [col for col in df.columns if col.startswith("Precio ")]
    columnas_mes_formateadas = [col.replace("Precio ", "") for col in columnas_mes]

    mes_actual = datetime.today().strftime("%m/%Y")

    if mes_actual in columnas_mes_formateadas:
        columna_objetivo = "Precio " + mes_actual
    else:
        fechas_dt = [datetime.strptime(m, "%m/%Y") for m in columnas_mes_formateadas]
        fecha_actual_dt = datetime.strptime(mes_actual, "%m/%Y")
        columna_mas_cercana = min(fechas_dt, key=lambda d: abs(d - fecha_actual_dt))
        columna_objetivo = "Precio " + columna_mas_cercana.strftime("%m/%Y")
        print(f"No hay precios del mes actual. Se usa: {columna_objetivo}")

    df_precio_mes = df[~df[columna_objetivo].isna()].copy()

    def parse_precio(x):
        try:
            return float(str(x).replace("€", "").replace(",", ".").strip())
        except:
            return None

    df_precio_mes["precio_float"] = df_precio_mes[columna_objetivo].apply(parse_precio)

    locales_disponibles = sorted(df_precio_mes["Local"].dropna().str.strip().unique())

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
                print(f" - {fila['Producto']} ({fila['Marca']} - {fila['Formato']}): {fila['precio_float']:.2f} €")

        repetir = input("\n¿Quieres consultar otro local? (s/n): ").strip().lower()
        if repetir != "s":
            break
