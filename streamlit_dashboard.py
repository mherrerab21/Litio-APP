import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Configuración
nombre_archivo_excel = 'futuros litio.xlsx'
ticker_cny = 'USDCNY=X'
today = datetime.today()
start_date = today - timedelta(days=7)
end_date = today

# Sidebar
st.sidebar.image('https://github.com/mherrerab21/Litio-APP/raw/main/arrayan-logo.png', width=200)
st.sidebar.title("Dashboard de Litio y Contrato 2407")

option = st.sidebar.selectbox(
    'Seleccione una opción',
    ('Litio y Minerales de Litio', 'Contrato Futuro 2407', 'Contrato Futuro 2501', 'Contrato Futuro 2511')
)

# Estilo CSS
st.markdown("""
<style>
body {
    background-color: #1e1e1e;
    color: white;
}
.css-1h2yj8v {
    max-width: none !important;
}
.css-1xjvdi2 {
    font-size: 28px !important;
    max-width: none !important;
}
</style>
""", unsafe_allow_html=True)

################# Función de tipo de cambio ####################
@st.cache_data(ttl=3600)
def obtener_tipo_cambio(ticker):
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if not data.empty:
            return round(data['Close'].iloc[0].item(), 2)
        else:
            st.warning(f"No se han descargado datos para {ticker} en el rango de fechas especificado.")
            return None
    except Exception as e:
        st.error(f"Error al descargar datos para {ticker}: {e}")
        return None

tipo_cambio_USD_CNY = obtener_tipo_cambio(ticker_cny)
if tipo_cambio_USD_CNY is None:
    tipo_cambio_USD_CNY = 7.2
    st.info("⚠️ Usando tipo de cambio de respaldo: 7.2 USD/CNY debido a un error en la descarga.")

##################### OPCIÓN 1: Litio ##########################
if option == 'Litio y Minerales de Litio':
    df = pd.read_excel(nombre_archivo_excel, sheet_name='Market')
    df.rename(columns={'Conversion en Notas': 'Fecha'}, inplace=True)
    df.set_index('Fecha', inplace=True)

    # Limpiar nombres de columnas
    df.columns = [c.replace('/', '').replace('\n', '') for c in df.columns]

    # Eliminar columnas innecesarias
    columnas_a_eliminar = [
        'Lithium Hydroxide Idx', 'SMM LC Idx', 'Lithium Hydroxide BG Fine', 'Lithium Hexafluorophosphate',
        'Lithium Fluoride BG', 'Spodumene Domestic China 4%', 'Spodumene Dometic China 3%',
        'Spodumene1,2%', 'Spodumene2%', 'Spodumene3%', 'Lepidolite 1,5%', 'Lepidolite 2%',
        'Montebrasite 6%', 'Montebrasite 7%'
    ]
    df = df.drop(columns=[c for c in columnas_a_eliminar if c in df.columns])

    # Formatear fechas
    df.index = pd.to_datetime(df.index).strftime('%d/%m/%y')

    # Conversiones
    iva = 1.13
    kg_to_mt = 1000

    operaciones = {
        'Industrial Grade': lambda x: x / iva / tipo_cambio_USD_CNY,
        'Battery Grade': lambda x: x / iva / tipo_cambio_USD_CNY,
        'Lithium Hydroxide BG': lambda x: x / iva / tipo_cambio_USD_CNY,
        'Lithium Hydroxide IG': lambda x: x / iva / tipo_cambio_USD_CNY,
        'Spodumene Concentrate IDXCIF China': lambda x: (x * 7.5) + 3750,
        'Spodumene Domestic China 5%': lambda x: (x / iva / tipo_cambio_USD_CNY) * 7.5 + 3750,
        'AUS Spodumene 6% Spot cif China': lambda x: (x * 7.5) + 3750,
        'BRL Spodumene 6% Spot CIF China': lambda x: (x * 7.5) + 3750,
        'Lithium Carbonate CIF China': lambda x: x * kg_to_mt,
        'Lithium Hydroxide CIF China': lambda x: x * kg_to_mt
    }

    for col, func in operaciones.items():
        if col in df.columns:
            df[col] = df[col].apply(func)

    df = df.fillna(0)

    st.markdown("## Litio y Minerales de Litio:")
    st.dataframe(df)

    variaciones = (df.diff().iloc[-1] / df.iloc[-2]) * 100
    st.markdown("## Variaciones Porcentuales:")
    st.dataframe(variaciones.to_frame(name='Variaciones Porcentuales').transpose().style.format("{:.2f}%"))

    st.markdown("## Precios de Contrato a lo largo del Tiempo")
    selected = st.multiselect("Seleccionar Precio de Contrato:", df.columns)
    if selected:
        df_selected = df[selected].reset_index()
        df_long = pd.melt(df_selected, id_vars=['Fecha'], value_vars=selected)
        fig = px.line(df_long, x='Fecha', y='value', color='variable',
                      labels={'Fecha': 'Fecha', 'value': 'Precio (USD/mt)', 'variable': 'Precio'})
        fig.update_layout(title="Precios de Contrato", width=1600, height=600)
        st.plotly_chart(fig, use_container_width=False)
    else:
        st.warning("Por favor selecciona al menos un precio de contrato.")

##################### FUNCIONES PARA CONTRATOS ##################
def procesar_contrato(sheet):
    df = pd.read_excel(nombre_archivo_excel, sheet_name=sheet)
    df.set_index('Date', inplace=True)
    df.index = pd.to_datetime(df.index).strftime('%d/%m/%y')
    df['Var %'] *= 100
    df['O.I %'] *= 100
    for col in ['Latest', 'Prev.Close', 'Prev.Settle', 'Open']:
        df[col] /= tipo_cambio_USD_CNY
    return df

def graficar(df, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Latest'], mode='lines', name='Price'))
    fig.update_layout(title=title, width=1200, height=400, xaxis_title='Fecha', yaxis_title='Precio (USD/mt)')
    return fig

def graficar_volumen(df):
    colors = ['red' if df['Volume'].diff().iloc[i] < 0 else 'green' for i in range(len(df))]
    fig = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], marker_color=colors)])
    fig.update_layout(width=1200, height=200, xaxis_title='Fecha', yaxis_title='Volumen')
    return fig

###################### CONTRATOS FUTUROS ######################
if option.startswith('Contrato Futuro'):
    hoja = 'Contrato ' + option.split()[-1]
    df_contrato = procesar_contrato(hoja)
    st.markdown(f"## {option}:")
    st.dataframe(df_contrato)
    st.plotly_chart(graficar(df_contrato, f"Precio - {option}"))
    st.plotly_chart(graficar_volumen(df_contrato))
