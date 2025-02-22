# DANIEL HERRERA TORRES

# Visualización de datos de forma interactiva

# Se desarrolla una aplicación interactiva en Streamlit que permite a los usuarios analizar datos de criptomonedas organizadas en pares, obteniendo la información de la API de Kraken utilizando herramientas de análisis técnico. La integración de indicadores como Bandas de Bollinger y MA20 facilita la identificación de tendencias y puntos de entrada/salida en el mercado, así como también la volatilidad del mercado.


import krakenex
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta

# -----------------------
# PASO 1: Crear una instancia de la API de Kraken después de instalar e importar las bibliotecas necesarias para el proyecto
# -----------------------

k = krakenex.API()


# -----------------------
# PASO 2: Construir función para obtener todos los pares de monedas disponibles en Kraken
# -----------------------

def get_all_tradable_pairs():
    # Realiza una solicitud a la API de Kraken para obtener los pares de activos disponibles
    response = k.query_public('AssetPairs')
    if 'result' in response:
        pairs = {}
        # Itera sobre los pares disponibles para formatearlos correctamente
        for pair, info in response['result'].items():
            base = info['base'][1:]  # Elimina el primer carácter ('Z' o 'X') de la moneda base
            quote = info['quote'][1:]  # Elimina el primer carácter ('Z' o 'X') de la moneda de cotización
            formatted_pair = f"{base}/{quote}"  # Construye el formato final del par de monedas: "BASE/QUOTE"
            pairs[formatted_pair] = pair  # Guarda el par formateado y su nombre interno de la API
        return pairs
    else:
        # Muestra un error si no se pueden obtener los pares
        st.error("Error al obtener los pares de monedas.")
        return {}

# -----------------------
# PASO 3: Construir función para calcular la fecha inicial (since) y el intervalo en minutos
# -----------------------

def calculate_since(period):
    now = datetime.now()  # Obtiene la fecha y hora actual
    # Define el rango de tiempo y el intervalo según el periodo seleccionado
    if period == "1 mes":
        return int(time.mktime((now - timedelta(days=30)).timetuple())), 60  # Intervalo de 1 hora
    elif period == "1 año":
        return int(time.mktime((now - timedelta(days=365)).timetuple())), 1440  # Intervalo diario
    elif period == "5 años":
        return int(time.mktime((now - timedelta(days=1825)).timetuple())), 1440  # Intervalo diario
    return None, None

# -----------------------
# PASO 4: Construir función para obtener datos históricos de un par de monedas de Kraken
# -----------------------

def get_historical_data(pair_api_format, interval=1440, since=None):
    # Realiza una solicitud a la API de Kraken para obtener datos OHLC (Open-High-Low-Close)
    response = k.query_public('OHLC', {'pair': pair_api_format, 'interval': interval, 'since': since})
    if 'result' in response:
        # Extrae los datos del par correspondiente
        pair_code = list(response['result'].keys())[0]
        data = response['result'][pair_code]
        # Convierte los datos en un DataFrame
        df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'])
        df['time'] = pd.to_datetime(df['time'], unit='s')  # Convierte la columna de tiempo a formato de fecha
        df['close'] = df['close'].astype(float)  # Asegura que la columna "close" sea de tipo float
        return df
    else:
        # Muestra un error si no se pueden obtener los datos
        st.error("Error al obtener datos históricos.")
        return None

# -----------------------
# PASO 5: Construir función para calcular las Bandas de Bollinger
# -----------------------

def calculate_bollinger_bands(df, window=20, num_std_dev=2):
    # Calcula la media móvil simple (MA20)
    df['MA20'] = df['close'].rolling(window=window).mean()
    # Calcula la desviación estándar sobre la ventana de tiempo
    df['STD'] = df['close'].rolling(window=window).std()
    # Calcula las bandas superior e inferior
    df['Upper Band'] = df['MA20'] + (df['STD'] * num_std_dev)
    df['Lower Band'] = df['MA20'] - (df['STD'] * num_std_dev)
    return df

# -----------------------
# PASO 6: Construir función para calcular las señales de compra y venta
# -----------------------

def calculate_signals(df):
    # Genera una columna para las señales de compra cuando el precio cierra por debajo de la banda inferior
    df['Buy Signal'] = (df['close'] < df['Lower Band'])
    # Genera una columna para las señales de venta cuando el precio cierra por encima de la banda superior
    df['Sell Signal'] = (df['close'] > df['Upper Band'])
    return df


# -----------------------
# PASO 7: Configurar Streamlit para visualizar el código en una gráfica
# -----------------------

st.title("Cotizaciones de Kraken con Bandas de Bollinger y Señales de Compra/Venta")

# Obtener todos los pares de monedas disponibles en Kraken
pairs = get_all_tradable_pairs()

# Verificar si "ETH/USD" está disponible y establecerlo como par de monedas predeterminado al desplegar la gráfica en Streamlit
default_pair = "ETH/USD"
if default_pair in pairs:
    pair_display = default_pair
else:
    pair_display = list(pairs.keys())[0]  # Selecciona el primer par disponible si ETH/USD no está presente

# Selector en Streamlit para elegir el par de monedas
pair_display = st.selectbox("Seleccione el par de monedas:", list(pairs.keys()), index=list(pairs.keys()).index(default_pair))
# Obtiene el nombre interno del par para la API
tair_api_format = pairs[pair_display]

# Selector para elegir el rango de tiempo
period = st.selectbox("Seleccione el rango de tiempo:", ["1 mes", "1 año", "5 años"])
# Calcula la fecha de inicio (since) y el intervalo según el rango de tiempo seleccionado
since, interval = calculate_since(period)

# Muestra el par seleccionado
st.write(f"Par de monedas seleccionado: {pair_display}")

# Obtener los datos históricos usando la función correspondiente
df = get_historical_data(tair_api_format, interval=interval, since=since)

# -----------------------
# PASO 8: Última instrucción para el codigo. Sólo continuar si se obtuvieron datos válidos y desplegar la gráfica en Streamlit
# -----------------------

if df is not None:
    # Calcular las Bandas de Bollinger y señales de compra/venta
    df = calculate_bollinger_bands(df)
    df = calculate_signals(df)

    # Crear el gráfico de velas
    fig = go.Figure()

    # Agregar las velas al gráfico
    fig.add_trace(go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Candlestick'
    ))

    # Agregar las Bandas de Bollinger
    fig.add_trace(go.Scatter(x=df['time'], y=df['Upper Band'], mode='lines', name='Upper Band',
                             line=dict(color='rgba(255,0,0,0.5)')))
    fig.add_trace(go.Scatter(x=df['time'], y=df['Lower Band'], mode='lines', name='Lower Band',
                             line=dict(color='rgba(0,255,0,0.5)')))
    fig.add_trace(go.Scatter(x=df['time'], y=df['MA20'], mode='lines', name='MA20',
                             line=dict(color='rgba(0,0,255,0.5)')))

    # Agregar señales de compra y venta
    fig.add_trace(go.Scatter(
        x=df.loc[df['Buy Signal'], 'time'],
        y=df.loc[df['Buy Signal'], 'close'],
        mode='markers',
        marker=dict(color='green', size=10),
        name='Buy Signal'
    ))

    fig.add_trace(go.Scatter(
        x=df.loc[df['Sell Signal'], 'time'],
        y=df.loc[df['Sell Signal'], 'close'],
        mode='markers',
        marker=dict(color='red', size=10),
        name='Sell Signal'
    ))

    # Configurar el layout de la gráfica
    fig.update_layout(
        title=f"Cotización del par {pair_display} con Bandas de Bollinger y Señales de Compra/Venta",
        xaxis_title="Fecha",
        yaxis_title="Precio",
        legend_title="Elementos",
        xaxis=dict(rangeslider=dict(visible=False))  # Desactiva el rango deslizante para evitar duplicación visual
    )

# Mostrar la gráfica en Streamlit
st.plotly_chart(fig, use_container_width=True)