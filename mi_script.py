import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
import json
from datetime import datetime, timezone, timedelta

# 📌 Configuración de Telegram desde Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

def enviar_mensaje(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": texto})

# 🔹 Archivo de estado
archivo_estado = "estado_rsi.json"
if os.path.exists(archivo_estado):
    with open(archivo_estado, "r") as f:
        estado = json.load(f)
else:
    estado = {}  # Estado independiente por ticker

# 🔹 Función RSI
def RSI(series, period=14):
    delta = series.diff()
    ganancias = delta.where(delta > 0, 0)
    perdidas = -delta.where(delta < 0, 0)
    media_gan = ganancias.rolling(period).mean()
    media_perd = perdidas.rolling(period).mean()
    rs = media_gan / media_perd
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 🔹 Diccionario de tickers
tickers = {
    "^MERV": "Merval",
    "GC=F": "Oro",
    "GGAL.BA": "Grupo Galicia",
    "PAMP.BA": "Pampa Energía",
    "YPFD.BA": "YPF",
    "RIO": "Rio Tinto",
    "USDARS=X": "Dólar oficial"
}

# 🔹 Fechas: último año hasta hoy (hora Argentina UTC-3)
hoy_arg = datetime.now(timezone.utc) - timedelta(hours=3)
hoy = hoy_arg.replace(hour=0, minute=0, second=0, microsecond=0)
hace_un_ano = hoy - timedelta(days=365)

# 🔹 Loop sobre tickers
for t, nombre in tickers.items():
    try:
        df = yf.download(t, start=hace_un_ano, end=hoy)['Close']
        if df.empty or len(df) < 14:
            continue  # No hay datos suficientes

        df = pd.DataFrame(df)
        df.columns = ['Close']
        df['RSI'] = RSI(df['Close'], 14)
        rsi_actual = df['RSI'].iloc[-1]

        estado_anterior = estado.get(t, "normal")

        # Enviar notificación solo para sobrecompra o sobreventa
        if rsi_actual > 70 and estado_anterior != "sobrecompra":
            mensaje = f"⚠️ ({nombre}) RSI {rsi_actual:.2f} → Sobrecompra"
            enviar_mensaje(mensaje)
            estado[t] = "sobrecompra"

        elif rsi_actual < 30 and estado_anterior != "sobreventa":
            mensaje = f"✅ ({nombre}) RSI {rsi_actual:.2f} → Sobreventa"
            enviar_mensaje(mensaje)
            estado[t] = "sobreventa"

        elif 30 <= rsi_actual <= 70:
            estado[t] = "normal"  # Actualiza estado, pero **no envía mensaje**

    except Exception as e:
        print(f"Error con {nombre}: {e}")
        continue

# 🔹 Guardar estado actualizado
with open(archivo_estado, "w") as f:
    json.dump(estado, f)
