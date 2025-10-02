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
    estado = {"RSI_estado": "normal"}

# 🔹 Fechas: último año hasta hoy (hora Argentina UTC-3)
hoy_arg = datetime.now(timezone.utc) - timedelta(hours=3)
hoy = hoy_arg.replace(hour=0, minute=0, second=0, microsecond=0)
hace_un_ano = hoy - timedelta(days=365)

# 🔹 Descargar datos del Merval
merval = yf.download("^MERV", start=hace_un_ano, end=hoy)['Close']
df = pd.DataFrame(merval)
df.columns = ['Merval']

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

df['RSI'] = RSI(df['Merval'], 14)
rsi_actual = df['RSI'].iloc[-1]

# 🔹 Enviar notificación solo si cambia de estado
if rsi_actual > 70 and estado.get("RSI_estado") != "sobrecompra":
    mensaje = f"⚠️ ¡MERVAL RSI {rsi_actual:.2f}! Sobrecompra → posible señal bajista"
    enviar_mensaje(mensaje)
    estado["RSI_estado"] = "sobrecompra"

elif rsi_actual < 30 and estado.get("RSI_estado") != "sobreventa":
    mensaje = f"✅ ¡MERVAL RSI {rsi_actual:.2f}! Sobreventa → posible señal alcista"
    enviar_mensaje(mensaje)
    estado["RSI_estado"] = "sobreventa"

elif 30 <= rsi_actual <= 70 and estado.get("RSI_estado") != "normal":
    mensaje = f"ℹ️ ¡MERVAL RSI {rsi_actual:.2f}! Volvió a zona neutral (30-70)"
    enviar_mensaje(mensaje)
    estado["RSI_estado"] = "normal"

# 🔹 Guardar estado actualizado
with open(archivo_estado, "w") as f:
    json.dump(estado, f)
