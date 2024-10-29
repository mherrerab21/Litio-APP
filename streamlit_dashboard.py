import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import plotly.express as px

# URL del logo de la compañía en GitHub
logo_url = 'https://github.com/mherrerab21/Litio-APP/raw/main/arrayan-logo.png'

# Mostrar el logo de la compañía en el dashboard
st.sidebar.image(logo_url, width=200) 

# Establecer el título de la página
st.sidebar.title("Dashboard de Litio y Contrato 2407")

# Opciones del sidebar
option = st.sidebar.selectbox(
    'Seleccione una opción',
    ('Litio y Minerales de Litio', 'Contrato Futuro 2407', 'Contrato Futuro 2501', 'Contrato Futuro 2411')
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
ticker = 'CNY=X' 
today = datetime.today()
start_date = today - timedelta(days=7)  
end_date = today

def download_data(ticker):
    try:
        data_yahoo = yf.download(ticker, start=start_date, end=end_date)
        if not data_yahoo.empty:  
            return data_yahoo
        else:
            st.warning("No se han descargado datos para {} en el rango de fechas especificado.".format(ticker))
            return None
    except Exception as e:  
        st.error("Error al descargar datos para {}: {}".format(ticker, e))
        return None

data_yahoo = download_data(ticker)
if data_yahoo is not None:
    cierre_ajustado = data_yahoo['Close'].iloc[0]

# Read Data from Excel
nombre_archivo_excel = 'futuros litio.xlsx'

# Función para obtener tipo de cambio de USD a CNY desde Yahoo Finance
def obtener_tipo_cambio(ticker):
    data_yahoo = download_data(ticker)
    if data_yahoo is not None:
        return round(data_yahoo['Close'].iloc[0], 2)
    return None

if option == 'Litio y Minerales de Litio':  
    df_market = pd.read_excel(nombre_archivo_excel, sheet_name='Market')

    # Data Cleaning and Transformation
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

    # Obtener tipo de cambio de USD a CNY desde Yahoo Finance
    tipo_cambio_USD_CNY = obtener_tipo_cambio('USDCNY=X')

    # Definir factor de conversión de KG a metric tons
    factor_conversion_KG_to_MT = 1000  

    if tipo_cambio_USD_CNY is not None:
        # Operaciones a realizar en las columnas especificadas
        columnas_operaciones = {
            'Industrial Grade': lambda x: x /(1+0.13)/tipo_cambio_USD_CNY,  
            'Battery Grade': lambda x: x /(1+0.13)/tipo_cambio_USD_CNY,
            'Lithium Hydroxide BG': lambda x: x /(1+0.13)/tipo_cambio_USD_CNY,
            'Lithium Hydroxide IG': lambda x: x /(1+0.13)/tipo_cambio_USD_CNY,
            'Spodumene Concentrate IDXCIF China': lambda x: (x * 7.5) + 3750,  
            'Spodumene Domestic China 5%': lambda x: ((x/(1+0.13))/tipo_cambio_USD_CNY)* 7.5 + 3750,  
            'AUS Spodumene 6% Spot cif China': lambda x: (x * 7.5) + 3750,  
            'BRL Spodumene 6% Spot CIF China': lambda x: (x * 7.5) + 3750,  
            'Lithium Carbonate CIF China': lambda x: x * factor_conversion_KG_to_MT,  
            'Lithium Hydroxide CIF China': lambda x: x * factor_conversion_KG_to_MT  
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
    st.markdown("## Litio y Minerales de Litio:")  
    st.dataframe(df_market)

    # Mostrar tabla de variaciones porcentuales de forma horizontal con el símbolo de porcentaje
    st.markdown("## Variaciones Porcentuales:")
    st.dataframe(variacion_porcentual.to_frame(name='Variaciones Porcentuales').transpose().style.format("{:.2f}%"))

    # Graficar los precios de contrato seleccionados a lo largo del tiempo
    st.markdown("## Precios de Contrato a lo largo del Tiempo")
    selected_prices = st.multiselect("Seleccionar Precio de Contrato:", df_market.columns)
    if selected_prices:
        df_market_selected = df_market[selected_prices].reset_index()
        df_market_selected_long = pd.melt(df_market_selected, id_vars=['Fecha'], value_vars=selected_prices)
        fig = px.line(df_market_selected_long, x='Fecha', y='value', color='variable', labels={'Fecha': 'Fecha', 'value': 'Precio (USD/mt)', 'variable': 'Precio de Contrato'})
        fig.update_layout(title="Precios de Contrato a lo largo del Tiempo", xaxis_title="Fecha", yaxis_title="Precio (USD/mt)", legend_title="Precio de Contrato", width=1600, height=800)
        st.plotly_chart(fig, use_container_width=True)

elif option == 'Contrato Futuro 2407':
    df_lc2407 = pd.read_excel(nombre_archivo_excel, sheet_name='Contrato 2407')
    df_lc2407.rename(columns={'Date': 'Fecha'}, inplace=True)
    df_lc2407.set_index('Fecha', inplace=True)

    # Convertir el índice a objetos de fecha y luego formatear las fechas
    df_lc2407.index = pd.to_datetime(df_lc2407.index).strftime('%d/%m/%y')

    # Reemplazar los valores NaN por 0
    df_lc2407 = df_lc2407.fillna(0)

    # Calcular las variaciones porcentuales entre el último y penúltimo dato
    variacion_porcentual_2407 = (df_lc2407.diff().iloc[-1] / df_lc2407.iloc[-2]) * 100

    # Mostrar DataFrame actualizado
    st.markdown("## Contrato Futuro 2407:")  
    st.dataframe(df_lc2407)

    # Mostrar tabla de variaciones porcentuales de forma horizontal con el símbolo de porcentaje
    st.markdown("## Variaciones Porcentuales:")
    st.dataframe(variacion_porcentual_2407.to_frame(name='Variaciones Porcentuales').transpose().style.format("{:.2f}%"))

    # Graficar los precios del contrato
    st.markdown("## Gráfica del Contrato Futuro 2407")
    fig_2407 = go.Figure()
    fig_2407.add_trace(go.Scatter(x=df_lc2407.index, y=df_lc2407['Close'], mode='lines', name='Precio de Cierre'))
    fig_2407.update_layout(title='Evolución del Precio del Contrato Futuro 2407', xaxis_title='Fecha', yaxis_title='Precio (USD)', width=1600, height=800)
    st.plotly_chart(fig_2407, use_container_width=True)

elif option == 'Contrato Futuro 2501':
    df_lc2501 = pd.read_excel(nombre_archivo_excel, sheet_name='Contrato 2501')
    df_lc2501.rename(columns={'Date': 'Fecha'}, inplace=True)
    df_lc2501.set_index('Fecha', inplace=True)

    # Convertir el índice a objetos de fecha y luego formatear las fechas
    df_lc2501.index = pd.to_datetime(df_lc2501.index).strftime('%d/%m/%y')

    # Reemplazar los valores NaN por 0
    df_lc2501 = df_lc2501.fillna(0)

    # Calcular las variaciones porcentuales entre el último y penúltimo dato
    variacion_porcentual_2501 = (df_lc2501.diff().iloc[-1] / df_lc2501.iloc[-2]) * 100

    # Mostrar DataFrame actualizado
    st.markdown("## Contrato Futuro 2501:")  
    st.dataframe(df_lc2501)

    # Mostrar tabla de variaciones porcentuales de forma horizontal con el símbolo de porcentaje
    st.markdown("## Variaciones Porcentuales:")
    st.dataframe(variacion_porcentual_2501.to_frame(name='Variaciones Porcentuales').transpose().style.format("{:.2f}%"))

    # Graficar los precios del contrato
    st.markdown("## Gráfica del Contrato Futuro 2501")
    fig_2501 = go.Figure()
    fig_2501.add_trace(go.Scatter(x=df_lc2501.index, y=df_lc2501['Close'], mode='lines', name='Precio de Cierre'))
    fig_2501.update_layout(title='Evolución del Precio del Contrato Futuro 2501', xaxis_title='Fecha', yaxis_title='Precio (USD)', width=1600, height=800)
    st.plotly_chart(fig_2501, use_container_width=True)

elif option == 'Contrato Futuro 2411':
    df_lc2411 = pd.read_excel(nombre_archivo_excel, sheet_name='Contrato 2411')
    df_lc2411.rename(columns={'Date': 'Fecha'}, inplace=True)
    df_lc2411.set_index('Fecha', inplace=True)

    # Convertir el índice a objetos de fecha y luego formatear las fechas
    df_lc2411.index = pd.to_datetime(df_lc2411.index).strftime('%d/%m/%y')

    # Reemplazar los valores NaN por 0
    df_lc2411 = df_lc2411.fillna(0)

    # Calcular las variaciones porcentuales entre el último y penúltimo dato
    variacion_porcentual_2411 = (df_lc2411.diff().iloc[-1] / df_lc2411.iloc[-2]) * 100

    # Mostrar DataFrame actualizado
    st.markdown("## Contrato Futuro 2411:")  
    st.dataframe(df_lc2411)

    # Mostrar tabla de variaciones porcentuales de forma horizontal con el símbolo de porcentaje
    st.markdown("## Variaciones Porcentuales:")
    st.dataframe(variacion_porcentual_2411.to_frame(name='Variaciones Porcentuales').transpose().style.format("{:.2f}%"))

    # Graficar los precios del contrato
    st.markdown("## Gráfica del Contrato Futuro 2411")
    fig_2411 = go.Figure()
    fig_2411.add_trace(go.Scatter(x=df_lc2411.index, y=df_lc2411['Close'], mode='lines', name='Precio de Cierre'))
    fig_2411.update_layout(title='Evolución del Precio del Contrato Futuro 2411', xaxis_title='Fecha', yaxis_title='Precio (USD)', width=1600, height=800)
    st.plotly_chart(fig_2411, use_container_width=True)

