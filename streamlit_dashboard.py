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

try:
    data_yahoo = yf.download(ticker, start=start_date, end=end_date)
    if not data_yahoo.empty:  
        cierre_ajustado = data_yahoo['Close'].iloc[0]  
    else:
        st.warning("No se han descargado datos para {} en el rango de fechas especificado.".format(ticker))
except Exception as e:  
    st.error("Error al descargar datos para {}: {}".format(ticker, e))

# Read Data from Excel
nombre_archivo_excel = 'futuros litio.xlsx'

# Función para obtener tipo de cambio de USD a CNY desde Yahoo Finance
def obtener_tipo_cambio(ticker):
    try:
        data_yahoo = yf.download(ticker, start=start_date, end=end_date)
        if not data_yahoo.empty:  
            return round(data_yahoo['Close'].iloc[0], 2)  
        else:
            st.warning("No se han descargado datos para {} en el rango de fechas especificado.".format(ticker))
            return None
    except Exception as e:  
        st.error("Error al descargar datos para {}: {}".format(ticker, e))
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
        fig.update_layout(title="Precios de Contrato a lo largo del Tiempo", xaxis_title="Fecha", yaxis_title="Precio (USD/mt)", legend_title="Precio de Contrato", width=1600, height=600) 
        fig.update_traces(hovertemplate='%{x}<br>%{y}')
        st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': True, 'scrollZoom': False})
    else:
        st.warning("Por favor selecciona al menos un precio de contrato.")

elif option == 'Contrato Futuro 2407':  
    # Read Data from Excel
    df_lc2407 = pd.read_excel(nombre_archivo_excel, sheet_name='Contrato 2407')

    # Data Cleaning and Transformation
    df_lc2407.set_index('Date', inplace=True)
    df_lc2407.index = pd.to_datetime(df_lc2407.index).strftime('%d/%m/%y')

    # Convertir las columnas 'Var%' y 'O.I%' a formato de porcentaje
    df_lc2407['Var %'] = df_lc2407['Var %'] * 100
    df_lc2407['O.I %'] = df_lc2407['O.I %'] * 100

    # Obtener tipo de cambio de USD a CNY desde Yahoo Finance
    tipo_cambio_USD_CNY = obtener_tipo_cambio('USDCNY=X')

 
    # Aplicar el tipo de cambio a las columnas necesarias
    if tipo_cambio_USD_CNY is not None:
        columns_to_convert = ['Latest', 'Prev.Close','Prev.Settle', 'Open']
        for column in columns_to_convert:
            df_lc2407[column] /= tipo_cambio_USD_CNY

    # Mostrar DataFrame actualizado
    st.markdown("## Contrato Futuro 2407:")  
    st.dataframe(df_lc2407)

    # Create a subplot for price and volume
    fig_lc2407 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               vertical_spacing=0.15, subplot_titles=("Price", ""))  

    # Add trace for price
    fig_lc2407.add_trace(go.Scatter(x=df_lc2407.index, y=df_lc2407['Latest'], mode='lines', name='Price'), row=1, col=1)
    fig_lc2407.update_yaxes(title_text="Price (USD/mt)", row=1, col=1)  

    # Add trace for volume
    colors_volume = ['red' if df_lc2407['Volume'].diff().iloc[i] < 0 else 'green' for i in range(len(df_lc2407))]
    fig_lc2407.add_trace(go.Bar(x=df_lc2407.index, y=df_lc2407['Volume'], name='Volume', marker_color=colors_volume), row=2, col=1)
    fig_lc2407.update_yaxes(title_text="Volume", row=2, col=1)
    fig_lc2407.update_xaxes(title_text="Date", row=2, col=1)  # Move x-axis title to volume plot

    # Update layout
    fig_lc2407.update_layout(title="Data for Future Contract 2407",
                             width=1200, height=600)  

    # Show the plot
    st.plotly_chart(fig_lc2407, use_container_width=False, config={'displayModeBar': True, 'scrollZoom': False})

elif option == 'Contrato Futuro 2501':  
    # Read Data from Excel for Contract 2501
    df_lc2501 = pd.read_excel(nombre_archivo_excel, sheet_name='Contrato 2501')

    # Data Cleaning and Transformation for Contract 2501
    df_lc2501.set_index('Date', inplace=True)
    df_lc2501.index = pd.to_datetime(df_lc2501.index).strftime('%d/%m/%y')

    # Convertir las columnas 'Var%' y 'O.I%' a formato de porcentaje
    df_lc2501['Var %'] = df_lc2501['Var %'] * 100
    df_lc2501['O.I %'] = df_lc2501['O.I %'] * 100

    # Obtener tipo de cambio de USD a CNY desde Yahoo Finance
    tipo_cambio_USD_CNY = obtener_tipo_cambio('USDCNY=X')

    # Aplicar el tipo de cambio a las columnas necesarias
    if tipo_cambio_USD_CNY is not None:
        columns_to_convert = ['Latest', 'Prev.Close','Prev.Settle' ,'Open']
        for column in columns_to_convert:
            df_lc2501[column] /= tipo_cambio_USD_CNY

    # Mostrar DataFrame actualizado para el Contrato 2501
    st.markdown("## Contrato Futuro 2501:") 
    st.dataframe(df_lc2501)

    # Create a subplot for price and volume for Contract 2501
    fig_lc2501 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               vertical_spacing=0.15, subplot_titles=("Price", ""))
    fig_lc2501.add_trace(go.Scatter(x=df_lc2501.index, y=df_lc2501['Latest'], mode='lines', name='Price'), row=1, col=1)
    fig_lc2501.update_yaxes(title_text="Price (USD/mt)", row=1, col=1)  

    # Add trace for volume for Contract 2501
    colors_volume_lc2501 = ['red' if df_lc2501['Volume'].diff().iloc[i] < 0 else 'green' for i in range(len(df_lc2501))]
    fig_lc2501.add_trace(go.Bar(x=df_lc2501.index, y=df_lc2501['Volume'], name='Volume', marker_color=colors_volume_lc2501), row=2, col=1)
    fig_lc2501.update_yaxes(title_text="Volume", row=2, col=1)
    fig_lc2501.update_xaxes(title_text="Date", row=2, col=1)  # Move x-axis title to volume plot

    # Update layout for Contract 2501
    fig_lc2501.update_layout(title="Data for Future Contract 2501",
                             width=1200, height=600)  

    # Show the plot for Contract 2501
    st.plotly_chart(fig_lc2501, use_container_width=False, config={'displayModeBar': True, 'scrollZoom': False})

elif option == 'Contrato Futuro 2411':  
    # Read Data from Excel for Contract 2411
    df_lc2411 = pd.read_excel(nombre_archivo_excel, sheet_name='Contrato 2411')

    # Data Cleaning and Transformation for Contract 2411
    df_lc2411.set_index('Date', inplace=True)
    df_lc2411.index = pd.to_datetime(df_lc2411.index).strftime('%d/%m/%y')

    # Convertir las columnas 'Var%' y 'O.I%' a formato de porcentaje
    df_lc2411['Var %'] = df_lc2411['Var %'] * 100
    df_lc2411['O.I %'] = df_lc2411['O.I %'] * 100

    # Obtener tipo de cambio de USD a CNY desde Yahoo Finance
    tipo_cambio_USD_CNY = obtener_tipo_cambio('USDCNY=X')

    # Aplicar el tipo de cambio a las columnas necesarias
    if tipo_cambio_USD_CNY is not None:
        columns_to_convert = ['Latest', 'Prev.Close','Prev.Settle' ,'Open']
        for column in columns_to_convert:
            df_lc2411[column] /= tipo_cambio_USD_CNY

    # Mostrar DataFrame actualizado para el Contrato 2411
    st.markdown("## Contrato Futuro 2411:") 
    st.dataframe(df_lc2411)

    # Create a subplot for price and volume for Contract 2411
    fig_lc2411 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               vertical_spacing=0.15, subplot_titles=("Price", ""))
    fig_lc2411.add_trace(go.Scatter(x=df_lc2411.index, y=df_lc2411['Latest'], mode='lines', name='Price'), row=1, col=1)
    fig_lc2411.update_yaxes(title_text="Price (USD/mt)", row=1, col=1)  

    # Add trace for volume for Contract 2411
    colors_volume_lc2411 = ['red' if df_lc2411['Volume'].diff().iloc[i] < 0 else 'green' for i in range(len(df_lc2411))]
    fig_lc2411.add_trace(go.Bar(x=df_lc2411.index, y=df_lc2411['Volume'], name='Volume', marker_color=colors_volume_lc2411), row=2, col=1)
    fig_lc2411.update_yaxes(title_text="Volume", row=2, col=1)
    fig_lc2411.update_xaxes(title_text="Date", row=2, col=1)  # Move x-axis title to volume plot

    # Update layout for Contract 2411
    fig_lc2411.update_layout(title="Data for Future Contract 2411",
                             width=1200, height=600)  

    # Show the plot for Contract 2411
    st.plotly_chart(fig_lc2411, use_container_width=False, config={'displayModeBar': True, 'scrollZoom': False})
