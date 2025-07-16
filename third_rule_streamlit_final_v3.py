
import streamlit as st
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def fetch_data(stock_id):
    ticker = yf.Ticker(f"{stock_id}.TW")
    hist = ticker.history(period="90d")
    if hist.empty:
        ticker = yf.Ticker(f"{stock_id}.TWO")
        hist = ticker.history(period="90d")
    return hist, ticker

def calculate_third_rule(price):
    base = round(price * 0.07 / 3)
    return {
        "目前股價": price,
        "基礎數值（四捨五入）": base,
        "⬆ 往上 10%": round(price + 4 * base, 1),
        "⬆ 往上 7%": round(price + 3 * base, 1),
        "⬆ 往上 2/3": round(price + 2 * base, 1),
        "⬆ 往上 1/3": round(price + base, 1),
        "────────────""────────────",
        "⬇ 往下 1/3": round(price - base, 1),
        "⬇ 往下 2/3": round(price - 2 * base, 1),
        "⬇ 往下 7%": round(price - 3 * base, 1),
        "⬇ 往下 10%": round(price - 4 * base, 1)
    }

def add_ema(df, spans):
    for span in spans:
        df[f"EMA{span}"] = df["Close"].ewm(span=span).mean()
    return df

def detect_crossovers(df):
    cross = []
    for i in range(1, len(df)):
        if df["EMA6"].iloc[i-1] < df["EMA30"].iloc[i-1] and df["EMA6"].iloc[i] > df["EMA30"].iloc[i]:
            cross.append((df.index[i], df["Close"].iloc[i], "金叉"))
        elif df["EMA6"].iloc[i-1] > df["EMA30"].iloc[i-1] and df["EMA6"].iloc[i] < df["EMA30"].iloc[i]:
            cross.append((df.index[i], df["Close"].iloc[i], "死叉"))
    return cross

def calculate_avg_prices(df):
    last_3 = df.tail(3)
    result = []
    for idx, row in last_3.iterrows():
        avg = round((row["Open"] + row["High"] + row["Low"] + row["Close"]) / 4, 2)
        result.append((idx.strftime("%Y-%m-%d"), avg))
    return result

def plot_k_chart(df):
    spans = [6, 12, 30, 60, 90, 180]
    colors = ["orange", "cyan", "purple", "limegreen", "pink", "blue"]
    labels = [f"EMA{s}" for s in spans]
    df = add_ema(df, spans)
    cross_alerts = detect_crossovers(df)

    apds = [mpf.make_addplot(df[f"EMA{span}"], color=colors[i], width=1) for i, span in enumerate(spans)]

    mc = mpf.make_marketcolors(up='red', down='green', inherit=True)
    style = mpf.make_mpf_style(marketcolors=mc, base_mpf_style="yahoo")

    fig, axes = mpf.plot(df, type='candle', style=style, addplot=apds, volume=True, returnfig=True,
                         figscale=1.3, title="日K圖與EMA均線")

    for i, span in enumerate(spans):
        value = round(df[f"EMA{span}"].iloc[-1], 2)
        axes[0].text(df.index[-1], df[f"EMA{span}"].iloc[-1], f"{labels[i]}: {value}",
                     color=colors[i], fontsize=8, ha='left')

    for t, y, label in cross_alerts[-3:]:
        axes[0].annotate(label, xy=(t, y), xytext=(t, y*1.03), fontsize=9,
                         bbox=dict(boxstyle="round", facecolor="white", edgecolor="red"),
                         arrowprops=dict(arrowstyle="->", color="red"))

    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()
    return f"data:image/png;base64,{encoded}"

# Streamlit 介面
st.set_page_config(page_title="三分之一法股價工具", layout="centered")
st.title("📈 三分之一法股價分析工具")

stock_id = st.text_input("輸入股票代碼（例如 2330）")

if st.button("開始分析"):
    if not stock_id:
        st.warning("請輸入股票代碼")
    else:
        with st.spinner("讀取資料中..."):
            hist, ticker = fetch_data(stock_id)
            if hist.empty:
                st.error("查無資料")
            else:
                price = round(hist["Close"].iloc[-1], 2)
                rule_result = calculate_third_rule(price)
                avg_prices = calculate_avg_prices(hist)

                st.subheader(f"📊 計算結果：{stock_id} - {ticker.info.get('shortName', '未知公司')}")
                for key, value in rule_result.items():
                    if "往上" in key:
                        st.markdown(f"<div style='background-color:#ffe6e6;padding:6px'>{key}: <b>{value}</b></div>", unsafe_allow_html=True)
                    elif "往下" in key:
                        st.markdown(f"<div style='background-color:#e6ffe6;padding:6px'>{key}: <b>{value}</b></div>", unsafe_allow_html=True)
                    elif "目前股價" in key:
                        st.markdown(f"<div style='background-color:#fff2cc;padding:6px'><b>{key}: {value}</b></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='padding:4px'>{key}: {value}</div>", unsafe_allow_html=True)

                st.markdown("📘 **三日均價**")
                for d, v in avg_prices:
                    st.markdown(f"- {d}：{v}")

                st.markdown("📉 **日K + EMA 均線圖表**")
                chart_url = plot_k_chart(hist)
                st.markdown(f"![chart]({chart_url})", unsafe_allow_html=True)
