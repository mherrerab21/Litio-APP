import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime, timedelta

# URL del logo de la compañía en GitHub
logo_url = 'https://github.com/mherrerab21/Litio-APP/raw/main/arrayan-logo.png'

# Mostrar el logo de la compañía en el dashboard
st.sidebar.image(logo_url, width=200)  # Ajusta el ancho según sea necesario

# Establecer el título de la página
st.sidebar.title("Dashboard de Precios de Litio y Derivados")

# Opciones del sidebar
option = st.sidebar.selectbox(
    'Seleccione una opción',
    ('Precios de Contrato', 'Contract Data', 'Opción 3')
)

# Cambiar el color de fondo de la página a un verde militar
st.markdown(
    """
    <style>
    body {
        background-color: #4B5320;
        color: white;
    }
    .css-1h2yj8v {
        max-width: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Establecer todos los títulos con el mismo tamaño
st.markdown(
    """
    <style>
    .css-1xjvdi2 {
        font-size: 28px !important;
        max-width: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
variacion_porcentual = (df_market.diff().iloc[-1] / df_market.iloc[-2]) * 100

# Mostrar DataFrame actualizado
if option == 'Precios de Contrato':
    st.markdown("## Precios de Contrato:")
    st.dataframe(df_market)

    # Mostrar tabla de variaciones junto con los precios de contrato
    st.markdown("## Variaciones Porcentuales entre el último y penúltimo dato:")
    st.dataframe(variacion_porcentual.to_frame(name='Variaciones Porcentuales'), height=400)

    # Graficar los precios de contrato seleccionados a lo largo del tiempo
    st.markdown("## Precios de Contrato a lo largo del Tiempo")
    selected_prices = st.multiselect("Seleccionar Precio de Contrato:", df_market.columns)
    if selected_prices:
        df_market_selected = df_market[selected_prices].reset_index()
        df_market_selected_long = pd.melt(df_market_selected, id_vars=['Fecha'], value_vars=selected_prices)
        fig = px.line(df_market_selected_long, x='Fecha', y='value', color='variable', labels={'Fecha': 'Fecha', 'value': 'Precio', 'variable': 'Precio de Contrato'})
        fig.update_layout(title="Precios de Contrato a lo largo del Tiempo", xaxis_title="Fecha", yaxis_title="Precio", legend_title="Precio de Contrato", width=1600, height=600)  # Ajusta el ancho del gráfico
        fig.update_traces(hovertemplate='%{x}<br>%{y}')
        st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': True, 'scrollZoom': False})
    else:
        st.warning("Por favor selecciona al menos un precio de contrato.")

elif option == 'Contract Data':
    # Read Data from Excel
    nombre_archivo_excel = 'futuros litio.xlsx'
    df_lc2407 = pd.read_excel(nombre_archivo_excel, sheet_name='Contrato 2407')

    # Data Cleaning and Transformation (corrected renaming)
    df_lc2407.set_index('Date', inplace=True)
    df_lc2407.index = pd.to_datetime(df_lc2407.index).strftime('%d/%m/%y')

    # Convertir las columnas 'Var%' y 'O.I%' a formato de porcentaje
    df_lc2407['Var %'] = df_lc2407['Var %'] * 100
    df_lc2407['O.I %'] = df_lc2407['O.I %'] * 100

    # Mostrar DataFrame actualizado
    st.markdown("## Contract Data:")
    st.dataframe(df_lc2407)

    # Graficar los datos de las columnas 'Latest' y 'Volume'
    fig_lc2407 = px.line(df_lc2407, x=df_lc2407.index, y=['Latest', 'Volume'], labels={'Date': 'Fecha', 'value': 'Valor', 'variable': 'Variable'})
    fig_lc2407.update_layout(title="Datos de Contrato 2407", xaxis_title="Fecha", yaxis_title="Valor", legend_title="Variable", width=1600, height=600)
    fig_lc2407.update_traces(hovertemplate='%{x}<br>%{y}')
    st.plotly_chart(fig_lc2407, use_container_width=False, config={'displayModeBar': True, 'scrollZoom': False})

elif option == 'Opción 3':
    st.write('Has seleccionado la opción 3')
    # Aquí puedes agregar el código para la opción 3

