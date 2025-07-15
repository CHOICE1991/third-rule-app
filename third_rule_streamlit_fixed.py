import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf

st.set_page_config(page_title="三分之一法分析工具", layout="wide")

def calculate_third_rule(price):
    base = round(price * 0.07 / 3)
    result = {
        "目前股價 💰": price,
        "基礎數值（四捨五入）": base,
        "⬆ 往上 10%": round(price + 4 * base, 1),
        "⬆ 往上 7%": round(price + 3 * base, 1),
        "⬆ 往上 2/3": round(price + 2 * base, 1),
        "⬆ 往上 1/3": round(price + base, 1),
        "⬇ 往下 1/3": round(price - base, 1),
        "⬇ 往下 2/3": round(price - 2 * base, 1),
        "⬇ 往下 7%": round(price - 3 * base, 1),
        "⬇ 往下 10%": round(price - 4 * base, 1)
    }
    return result

def fetch_price(stock_id):
    try:
        ticker = yf.Ticker(f"{stock_id}.TW")
        hist = ticker.history(period="5d")
        if hist.empty:
            ticker = yf.Ticker(f"{stock_id}.TWO")
            hist = ticker.history(period="5d")
        price = round(hist["Close"].iloc[-1], 1)
        return price, ticker.info.get("shortName", stock_id)
    except:
        return None, "未知股票"

st.title("📈 三分之一法分析工具")

stock_id = st.text_input("請輸入股票代碼（如 2330）")

if stock_id:
    price, name = fetch_price(stock_id)
    if price is None:
        st.error("找不到此股票資料")
    else:
        result = calculate_third_rule(price)

        st.subheader(f"📊 計算結果：{stock_id} - {name}")
        st.markdown(f"**目前股價 💰：{result['目前股價 💰']}**")
        st.markdown(f"**基礎數值（四捨五入）：{result['基礎數值（四捨五入）']}**")

        col1, col2 = st.columns(2)
        with col1:
            for k in ["⬆ 往上 10%", "⬆ 往上 7%", "⬆ 往上 2/3", "⬆ 往上 1/3"]:
                st.markdown(f"🟥 **{k}**：{result[k]}")
        with col2:
            for k in ["⬇ 往下 1/3", "⬇ 往下 2/3", "⬇ 往下 7%", "⬇ 往下 10%"]:
                st.markdown(f"🟩 **{k}**：{result[k]}")
