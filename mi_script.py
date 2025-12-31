# -*- coding: utf-8 -*-
import yfinance as yf
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import requests
import os

# ---------------- TELEGRAM ----------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_imagen(path, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(path, "rb") as img:
        r = requests.post(
            url,
            files={"photo": img},
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            timeout=30
        )
    print("Telegram status:", r.status_code)
    print(r.text)

# ---------------- CONFIG ----------------
tickers = {
    "^MERV": "Merval",
    "GC=F": "Oro",
    "GGAL.BA": "Grupo Galicia",
    "PAMP.BA": "Pampa Energía",
    "YPFD.BA": "YPF",
    "RIO": "Rio Tinto",
    "USDARS=X": "Dólar"
}

tickers_rsi_plot = ["GC=F", "RIO", "^MERV"]

# ---------------- FUNCIONES ----------------
def RSI(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calcular_macd(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd - signal

# ---------------- ANALISIS ----------------
resultados = []
data_rsi = {}

for ticker, nombre in tickers.items():
    df = yf.download(
        ticker,
        period="180d",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if df.empty or "Close" not in df.columns:
        continue

    df["RSI"] = RSI(df["Close"])
    df["MACD_Hist"] = calcular_macd(df["Close"])

    precio = round(float(df["Close"].iloc[-1]), 2)
    rsi = round(float(df["RSI"].iloc[-1]), 1)
    macd_hist = round(float(df["MACD_Hist"].iloc[-1]), 2)

    estado = (
        "Sobrecompra" if rsi > 70 else
        "Sobreventa" if rsi < 30 else
        "Neutral"
    )

    resultados.append({
        "Activo": nombre,
        "Precio": precio,
        "RSI": rsi,
        "MACD_Hist": macd_hist,
        "Estado": estado
    })

    if ticker in tickers_rsi_plot:
        data_rsi[nombre] = df["RSI"]

tabla = pd.DataFrame(resultados)

# ---------------- GRAFICO RSI ----------------
plt.figure(figsize=(12, 6))

for nombre, serie in data_rsi.items():
    plt.plot(serie.index, serie, linewidth=1.5, label=nombre)

plt.axhline(70, linestyle="--", linewidth=1)
plt.axhline(30, linestyle="--", linewidth=1)
plt.axhline(50, linestyle=":", linewidth=1)

plt.ylim(20, 95)
plt.title("RSI Diario – Merval, Oro y Rio Tinto")
plt.ylabel("RSI")
plt.xlabel("Fecha")
plt.grid(True)

plt.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, 0.1),
    ncol=len(data_rsi),
    frameon=False,
    fontsize=12
)

# ---------------- TABLA EN GRAFICO ----------------
cabecera = f"{'Activo':<15}{'Precio':>10}{'RSI':>7}{'MACD':>10}   Estado\n"
linea_sep = "-" * 60 + "\n"
texto = cabecera + linea_sep

for _, row in tabla.iterrows():
    texto += (
        f"{row['Activo']:<15}"
        f"{row['Precio']:>10}"
        f"{row['RSI']:>7}"
        f"{row['MACD_Hist']:>10}"
        f"{row['Estado']}\n"
    )

plt.text(
    0.01, 0.98,
    texto,
    transform=plt.gca().transAxes,
    fontsize=9,
    verticalalignment="top",
    family="monospace",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#f2f2f2", edgecolor="gray", alpha=0.7)
)

plt.tight_layout(rect=[0, 0.18, 1, 1])

# ---------------- GUARDAR Y ENVIAR ----------------
imagen = "rsi_diario.png"
plt.savefig(imagen, dpi=150)
plt.close()

enviar_imagen(
    imagen,
    "📈 RSI diario – Merval, Oro y Rio Tinto"
)
