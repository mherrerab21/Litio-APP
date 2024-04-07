import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Download Yahoo Finance Data (improved error handling)
ticker = 'CNY=X'  # Double-check the ticker symbol
today = datetime.today()
start_date = today - timedelta(days=7)  # Start a week ago
end_date = today

try:
    data_yahoo = yf.download(ticker, start=start_date, end=end_date)
    if not data_yahoo.empty:  # Check if data is empty
        cierre_ajustado = data_yahoo['Close'].iloc[0]  # Access closing price
    else:
        st.warning("No data downloaded for {} in the specified date range.".format(ticker))
except Exception as e:  # Handle different exceptions
    st.error("Error downloading data for {}: {}".format(ticker, e))

# Read Data from Excel
nombre_archivo_excel = 'futuros litio.xlsx'
df_market = pd.read_excel(nombre_archivo_excel, sheet_name='Market')

# Data Cleaning and Transformation (corrected renaming)
df_market.rename(columns={'Conversion en Notas': 'Fecha'}, inplace=True)
df_market.set_index('Fecha', inplace=True)

# Column Name Cleaning
nombres_columnas_originales = ['Industrial\n Grade', 'SMM\n LC Idx', 'Battery \nGrade', 'Lithium \nHydroxide BG',
                              'Lithium Hydroxide Idx', 'Lithium Hydroxide \nBG Fine', 'Lithium Carbonate\n CIF China',
                              'Lithium Hydroxide\n CIF China', 'Lithium \nHexafluorophosphate', 'Lithium \nFluoride BG',
                              'Lithium\n Hydroxide IG', 'Spodumene \nConcentrate IDX\nCIF China', 'Spodumene Domestic\n China 5%',
                              'Spodumene \nDomestic China 4%', 'Spodumene \nDometic China 3%', 'Spodumene\n1,2%',
                              'Spodumene\n2%', 'Spodumene\n3%', 'Lepidolite \n1,5%', 'Lepidolite \n2%', 'Montebrasite \n6%',
                              'Montebrasite \n7%', 'AUS Spodumene 6% Spot cif China', 'BRL Spodumene 6% Spot CIF China']

nombres_columnas_actualizados = [nombre.replace('/', '').replace('\n', '') for nombre in nombres_columnas_originales]

df_market.columns = nombres_columnas_actualizados

# Column Removal
columnas_a_eliminar = ['Lithium Hydroxide Idx', 'SMM LC Idx', 'Lithium Hydroxide BG Fine', 'Lithium Hexafluorophosphate',
                      'Lithium Fluoride BG', 'Spodumene Domestic China 4%', 'Spodumene Dometic China 3%',
                      'Spodumene1,2%', 'Spodumene2%', 'Spodumene3%', 'Lepidolite 1,5%', 'Lepidolite 2%',
                      'Montebrasite 6%', 'Montebrasite 7%']

df_market = df_market.drop(columns=columnas_a_eliminar)

# Convertir el índice a objetos de fecha y luego formatear las fechas
df_market.index = pd.to_datetime(df_market.index).strftime('%d/%m/%y')

# Función para obtener tipo de cambio de USD a CNY desde Yahoo Finance
def obtener_tipo_cambio(ticker):
    try:
        data_yahoo = yf.download(ticker, start=start_date, end=end_date)
        if not data_yahoo.empty:  # Check if data is empty
            return round(data_yahoo['Close'].iloc[0], 2)  # Access closing price and round to 2 decimal places
        else:
            st.warning("No data downloaded for {} in the specified date range.".format(ticker))
            return None
    except Exception as e:  # Handle different exceptions
        st.error("Error downloading data for {}: {}".format(ticker, e))
        return None

# Obtener tipo de cambio de USD a CNY desde Yahoo Finance
tipo_cambio_USD_CNY = obtener_tipo_cambio('USDCNY=X')

# Definir factor de conversión de KG a metric tons
factor_conversion_KG_to_MT = 1000  # 1 KG = 0.001 metric tons

if tipo_cambio_USD_CNY is not None:
    # Operaciones a realizar en las columnas especificadas
    columnas_operaciones = {
        'Industrial Grade': lambda x: x / tipo_cambio_USD_CNY,  # Mantener el resultado como número flotante
        'Battery Grade': lambda x: x / tipo_cambio_USD_CNY,
        'Lithium Hydroxide BG': lambda x: x / tipo_cambio_USD_CNY,
        'Lithium Hydroxide IG': lambda x: x / tipo_cambio_USD_CNY,
        'Spodumene Domestic China 5%': lambda x: (x * 7.5) + 3750,  # Mantener el resultado como número flotante
        'AUS Spodumene 6% Spot cif China': lambda x: (x * 7.5) + 3750,  # Mantener el resultado como número flotante
        'BRL Spodumene 6% Spot CIF China': lambda x: (x * 7.5) + 3750,  # Mantener el resultado como número flotante
        'Lithium Carbonate CIF China': lambda x: x / tipo_cambio_USD_CNY * factor_conversion_KG_to_MT,  # Mantener el resultado como número flotante
        'Lithium Hydroxide CIF China': lambda x: x / tipo_cambio_USD_CNY * factor_conversion_KG_to_MT  # Mantener el resultado como número flotante
    }

    # Aplicar operaciones a las columnas correspondientes
    for columna, operacion in columnas_operaciones.items():
        if columna in df_market.columns:
            df_market[columna] = df_market[columna].apply(operacion)

# Reemplazar los valores NaN por 0
df_market = df_market.fillna(0)

# Calcular las variaciones porcentuales entre el último y penúltimo dato para cada columna
variacion_porcentual = ((df_market.iloc[-1] - df_market.iloc[-2]) / df_market.iloc[-2]) * 100

# Mostrar DataFrame actualizado
st.write("Precios de Contrato:")
st.write(df_market)

# Mostrar tabla de variaciones junto con los precios de contrato
st.write("Variaciones porcentuales entre el último y penúltimo dato:")
st.write(variacion_porcentual.to_frame(name='Variaciones').T.style.format("{:.2f}%").set_caption('Variaciones'))

# Graficar los precios de contrato seleccionados a lo largo del tiempo
st.title("Precios de Contrato a lo largo del Tiempo")
selected_prices = st.multiselect("Seleccionar Precio de Contrato:", df_market.columns)
if selected_prices:
    # Invertir el DataFrame para que las fechas más recientes estén a la derecha
    df_market_inverted = df_market[selected_prices].iloc[::-1]
    chart = st.line_chart(df_market_inverted, use_container_width=True)
    chart.pyplot().invert_xaxis()  # Invertir el eje x del gráfico
    # Mostrar valor y fecha al poner el mouse sobre el gráfico
    chart.pyplot().tooltip(selected_prices)
else:
    st.warning("Por favor selecciona al menos un precio de contrato.")

