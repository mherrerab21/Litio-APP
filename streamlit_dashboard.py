import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import plotly.express as px

# Constants
LOGO_URL = 'https://github.com/mherrerab21/Litio-APP/raw/main/arrayan-logo.png'
NOMBRE_ARCHIVO_EXCEL = 'futuros litio.xlsx'
TICKER_USD_CNY = 'USDCNY=X'

# Function to download data from Yahoo Finance
def obtener_tipo_cambio(ticker, start_date, end_date):
    try:
        data_yahoo = yf.download(ticker, start=start_date, end=end_date)
        if not data_yahoo.empty:
            return round(data_yahoo['Close'].iloc[0], 2)
        else:
            st.warning(f"No se han descargado datos para {ticker} en el rango de fechas especificado.")
            return None
    except Exception as e:
        st.error(f"Error al descargar datos para {ticker}: {e}")
        return None

# Function to clean and transform market data
def procesar_datos_market(df):
    df.rename(columns={'Conversion en Notas': 'Fecha'}, inplace=True)
    df.set_index('Fecha', inplace=True)

    # Clean column names
    df.columns = [nombre.replace('/', '').replace('\n', '') for nombre in df.columns]

    # Remove unnecessary columns
    columnas_a_eliminar = ['Lithium Hydroxide Idx', 'SMM LC Idx', 'Lithium Hydroxide BG Fine',
                            'Lithium Hexafluorophosphate', 'Lithium Fluoride BG',
                            'Spodumene Domestic China 4%', 'Spodumene Dometic China 3%',
                            'Spodumene1,2%', 'Spodumene2%', 'Spodumene3%', 
                            'Lepidolite 1,5%', 'Lepidolite 2%', 
                            'Montebrasite 6%', 'Montebrasite 7%']
    df.drop(columns=columnas_a_eliminar, inplace=True)

    # Format the index to date
    df.index = pd.to_datetime(df.index).strftime('%d/%m/%y')

    return df

# Function to apply currency conversion to relevant columns
def aplicar_tipo_cambio(df, tipo_cambio):
    if tipo_cambio is not None:
        conversion_columns = ['Industrial Grade', 'Battery Grade', 'Lithium Hydroxide BG', 
                              'Lithium Hydroxide IG', 'Spodumene Concentrate IDXCIF China', 
                              'Spodumene Domestic China 5%', 'AUS Spodumene 6% Spot cif China', 
                              'BRL Spodumene 6% Spot CIF China', 'Lithium Carbonate CIF China', 
                              'Lithium Hydroxide CIF China']
        for column in conversion_columns:
            if column in df.columns:
                df[column] = df[column].apply(lambda x: x / (1 + 0.13) / tipo_cambio if pd.notnull(x) else x)
    return df

# Function to plot data
def graficar_precios_contrato(df_market):
    selected_prices = st.multiselect("Seleccionar Precio de Contrato:", df_market.columns)
    if selected_prices:
        df_market_selected = df_market[selected_prices].reset_index()
        df_market_long = pd.melt(df_market_selected, id_vars=['Fecha'], value_vars=selected_prices)
        fig = px.line(df_market_long, x='Fecha', y='value', color='variable', 
                      labels={'Fecha': 'Fecha', 'value': 'Precio (USD/mt)', 'variable': 'Precio de Contrato'})
        fig.update_layout(title="Precios de Contrato a lo largo del Tiempo", xaxis_title="Fecha", 
                          yaxis_title="Precio (USD/mt)", legend_title="Precio de Contrato", 
                          width=1600, height=600)
        st.plotly_chart(fig, use_container_width=False)
    else:
        st.warning("Por favor selecciona al menos un precio de contrato.")

# Streamlit configuration
st.sidebar.image(LOGO_URL, width=200)
st.sidebar.title("Dashboard de Litio y Contrato 2407")

# Sidebar options
option = st.sidebar.selectbox('Seleccione una opción', 
                                ('Litio y Minerales de Litio', 'Contrato Futuro 2407', 
                                 'Contrato Futuro 2501', 'Contrato Futuro 2411'))

# Change background color
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

# Download Yahoo Finance data
today = datetime.today()
start_date = today - timedelta(days=7)
tipo_cambio_USD_CNY = obtener_tipo_cambio(TICKER_USD_CNY, start_date, today)

# Main logic
if option == 'Litio y Minerales de Litio':
    df_market = pd.read_excel(NOMBRE_ARCHIVO_EXCEL, sheet_name='Market')
    df_market = procesar_datos_market(df_market)

    # Apply currency conversion
    df_market = aplicar_tipo_cambio(df_market, tipo_cambio_USD_CNY)

    # Replace NaN with 0
    df_market.fillna(0, inplace=True)

    # Calculate percentage variations
    variacion_porcentual = (df_market.diff().iloc[-1] / df_market.iloc[-2]) * 100

    # Display data
    st.markdown("## Litio y Minerales de Litio:")
    st.dataframe(df_market)

    st.markdown("## Variaciones Porcentuales:")
    st.dataframe(variacion_porcentual.to_frame(name='Variaciones Porcentuales').transpose().style.format("{:.2f}%"))

    # Plot contract prices
    st.markdown("## Precios de Contrato a lo largo del Tiempo")
    graficar_precios_contrato(df_market)

elif option == 'Contrato Futuro 2407':
    df_lc2407 = pd.read_excel(NOMBRE_ARCHIVO_EXCEL, sheet_name='Contrato 2407')
    df_lc2407.set_index('Date', inplace=True)
    df_lc2407.index = pd.to_datetime(df_lc2407.index).strftime('%d/%m/%y')

    # Convert percentage columns
    df_lc2407['Var %'] *= 100
    df_lc2407['O.I %'] *= 100

    # Apply currency conversion
    df_lc2407 = aplicar_tipo_cambio(df_lc2407, tipo_cambio_USD_CNY)

    # Display data
    st.markdown("## Contrato Futuro 2407:")
    st.dataframe(df_lc2407)

    # Create plot
    fig_lc2407 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               vertical_spacing=0.15, subplot_titles=("Price", "Volume"))
    fig_lc2407.add_trace(go.Scatter(x=df_lc2407.index, y=df_lc2407['Latest'], mode='lines', name='Price'), row=1, col=1)
    fig_lc2407.update_yaxes(title_text="Price (USD/mt)", row=1, col=1)

    colors_volume = ['red' if df_lc2407['Volume'].diff().iloc[i] < 0 else 'green' for i in range(len(df_lc2407))]
    fig_lc2407.add_trace(go.Bar(x=df_lc2407.index, y=df_lc2407['Volume'], name='Volume', marker_color=colors_volume), row=2, col=1)
    fig_lc2407.update_yaxes(title_text="Volume", row=2, col=1)
    fig_lc2407.update_xaxes(title_text="Date", row=2, col=1)

    st.plotly_chart(fig_lc2407, use_container_width=False)

elif option == 'Contrato Futuro 2501':
    df_lc2501 = pd.read_excel(NOMBRE_ARCHIVO_EXCEL, sheet_name='Contrato 2501')
    df_lc2501.set_index('Date', inplace=True)
    df_lc2501.index = pd.to_datetime(df_lc2501.index).strftime('%d/%m/%y')

    # Convert percentage columns
    df_lc2501['Var %'] *= 100
    df_lc2501['O.I %'] *= 100

    # Apply currency conversion
    df_lc2501 = aplicar_tipo_cambio(df_lc2501, tipo_cambio_USD_CNY)

    # Display data
    st.markdown("## Contrato Futuro 2501:")
    st.dataframe(df_lc2501)

    # Create plot
    fig_lc2501 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               vertical_spacing=0.15, subplot_titles=("Price", "Volume"))
    fig_lc2501.add_trace(go.Scatter(x=df_lc2501.index, y=df_lc2501['Latest'], mode='lines', name='Price'), row=1, col=1)
    fig_lc2501.update_yaxes(title_text="Price (USD/mt)", row=1, col=1)

    colors_volume_lc2501 = ['red' if df_lc2501['Volume'].diff().iloc[i] < 0 else 'green' for i in range(len(df_lc2501))]
    fig_lc2501.add_trace(go.Bar(x=df_lc2501.index, y=df_lc2501['Volume'], name='Volume', marker_color=colors_volume_lc2501), row=2, col=1)
    fig_lc2501.update_yaxes(title_text="Volume", row=2, col=1)
    fig_lc2501.update_xaxes(title_text="Date", row=2, col=1)

    st.plotly_chart(fig_lc2501, use_container_width=False)

elif option == 'Contrato Futuro 2411':
    # Similar logic for Contract 2411 can be added here...
    pass
