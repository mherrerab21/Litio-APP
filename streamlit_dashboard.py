pip install yfinance==0.2.32

# Mejorado para eficiencia, legibilidad y modularidad
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import plotly.express as px

# --- Configuración general ---
LOGO_URL = 'https://github.com/mherrerab21/Litio-APP/raw/main/arrayan-logo.png'
EXCEL_FILE = 'futuros litio.xlsx'
TICKER_CNY = 'USDCNY=X'
KG_TO_MT = 1000
IVA = 1.13
SPODUMENE_CONV = lambda x: (x * 7.5) + 3750

# --- Sidebar ---
st.sidebar.image(LOGO_URL, width=200)
st.sidebar.title("Dashboard de Litio y Contrato 2407")
option = st.sidebar.selectbox('Seleccione una opción', [
    'Litio y Minerales de Litio', 'Contrato Futuro 2407', 'Contrato Futuro 2501', 'Contrato Futuro 2411'
])

# --- Estilo global ---
st.markdown("""
<style>
body { background-color: #4B5320; color: white; }
.css-1h2yj8v { max-width: none !important; }
.css-1xjvdi2 { font-size: 28px !important; max-width: none !important; }
</style>
""", unsafe_allow_html=True)

# --- Funciones auxiliares ---
def obtener_tipo_cambio(ticker):
    try:
        data = yf.download(ticker, start=datetime.today() - timedelta(days=7), end=datetime.today())
        return round(data['Close'].iloc[0], 2) if not data.empty else None
    except Exception as e:
        st.error(f"Error al descargar tipo de cambio {ticker}: {e}")
        return None

def limpiar_columnas(df, columnas_reemplazo, columnas_eliminar):
    df.columns = [c.replace('\n', '').replace('/', '') for c in columnas_reemplazo]
    return df.drop(columns=columnas_eliminar)

def aplicar_conversiones(df, tipo_cambio):
    operaciones = {
        'Industrial Grade': lambda x: x / IVA / tipo_cambio,
        'Battery Grade': lambda x: x / IVA / tipo_cambio,
        'Lithium Hydroxide BG': lambda x: x / IVA / tipo_cambio,
        'Lithium Hydroxide IG': lambda x: x / IVA / tipo_cambio,
        'Spodumene Concentrate IDXCIF China': SPODUMENE_CONV,
        'Spodumene Domestic China 5%': lambda x: (x / IVA / tipo_cambio) * 7.5 + 3750,
        'AUS Spodumene 6% Spot cif China': SPODUMENE_CONV,
        'BRL Spodumene 6% Spot CIF China': SPODUMENE_CONV,
        'Lithium Carbonate CIF China': lambda x: x * KG_TO_MT,
        'Lithium Hydroxide CIF China': lambda x: x * KG_TO_MT
    }
    for col, func in operaciones.items():
        if col in df.columns:
            df[col] = df[col].apply(func)
    return df.fillna(0)

def procesar_contrato(sheet_name, tipo_cambio):
    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
    df.set_index('Date', inplace=True)
    df.index = pd.to_datetime(df.index).strftime('%d/%m/%y')
    for col in ['Var %', 'O.I %']:
        df[col] *= 100
    for col in ['Latest', 'Prev.Close', 'Prev.Settle', 'Open']:
        df[col] /= tipo_cambio
    return df

def graficar_precio_volumen(df, title):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15, subplot_titles=("Price", ""))
    fig.add_trace(go.Scatter(x=df.index, y=df['Latest'], mode='lines', name='Price'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=['red' if df['Volume'].diff().iloc[i] < 0 else 'green' for i in range(len(df))], name='Volume'), row=2, col=1)
    fig.update_layout(title=title, width=1200, height=600)
    fig.update_yaxes(title_text="Price (USD/mt)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    st.plotly_chart(fig, use_container_width=False)

# --- Página principal ---
tipo_cambio = obtener_tipo_cambio(TICKER_CNY)

if option == 'Litio y Minerales de Litio':
    df = pd.read_excel(EXCEL_FILE, sheet_name='Market')
    df.rename(columns={'Conversion en Notas': 'Fecha'}, inplace=True)
    df.set_index('Fecha', inplace=True)

    columnas_originales = list(df.columns)
    columnas_eliminar = [
        'Lithium Hydroxide Idx', 'SMM LC Idx', 'Lithium Hydroxide BG Fine', 'Lithium Hexafluorophosphate',
        'Lithium Fluoride BG', 'Spodumene Domestic China 4%', 'Spodumene Dometic China 3%',
        'Spodumene1,2%', 'Spodumene2%', 'Spodumene3%', 'Lepidolite 1,5%', 'Lepidolite 2%',
        'Montebrasite 6%', 'Montebrasite 7%']

    df = limpiar_columnas(df, columnas_originales, columnas_eliminar)
    df.index = pd.to_datetime(df.index).strftime('%d/%m/%y')

    if tipo_cambio:
        df = aplicar_conversiones(df, tipo_cambio)

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
        fig = px.line(df_long, x='Fecha', y='value', color='variable')
        fig.update_layout(title="Precios de Contrato", xaxis_title="Fecha", yaxis_title="Precio (USD/mt)", width=1600, height=600)
        st.plotly_chart(fig, use_container_width=False)
    else:
        st.warning("Por favor selecciona al menos un precio de contrato.")

else:
    nombre_hoja = option.replace('Contrato Futuro ', 'Contrato ')
    df_contrato = procesar_contrato(nombre_hoja, tipo_cambio)
    st.markdown(f"## {option}:")
    st.dataframe(df_contrato)
    graficar_precio_volumen(df_contrato, f"Data for {option}")
