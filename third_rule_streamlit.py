import streamlit as st
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="三分之一法股價分析工具", layout="wide")

st.title("📈 三分之一法股價分析工具")

# 股票代碼輸入
stock_id = st.text_input("請輸入台股股票代碼（如 2330）:")

# 讀取股票對照表（若有）
@st.cache_data
def load_stock_map():
    try:
        df = pd.read_csv("tw_stocks.csv", dtype=str)
        return dict(zip(df["股票代碼"], df["公司名稱"]))
    except:
        return {}

stock_name_map = load_stock_map()

# 計算三分之一法
def calculate_third_rule(price):
    base = round(price * 0.07 / 3)
    result = {
        "目前股價 💰": price,
        "基礎數值（四捨五入）": base,
        "⬆ 往上 10%": round(price + 4 * base, 1),
        "⬆ 往上 7%": round(price + 3 * base, 1),
        "⬆ 往上 2/3": round(price + 2 * base, 1),
        "⬆ 往上 1/3": round(price + 1 * base, 1),
        "────────────": "────────────",
        "⬇ 往下 1/3": round(price - 1 * base, 1),
        "⬇ 往下 2/3": round(price - 2 * base, 1),
        "⬇ 往下 7%": round(price - 3 * base, 1),
        "⬇ 往下 10%": round(price - 4 * base, 1),
    }
    return result

# 計算均線
def add_ema(data, spans):
    for span in spans:
        data[f"EMA{span}"] = data["Close"].ewm(span=span).mean()
    return data

# 計算近三日均價
def calculate_recent_average(data):
    results = []
    for offset in range(1, 4):
        row = data.iloc[-offset]
        avg = round((row['Open'] + row['High'] + row['Low'] + row['Close']) / 4, 2)
        date_str = row.name.strftime("%Y-%m-%d")
        results.append((date_str, avg))
    return results

# 下載股價
@st.cache_data
def fetch_data(stock_code):
    ticker = yf.Ticker(f"{stock_code}.TW")
    data = ticker.history(period="7d", interval="1d")
    if data.empty:
        ticker = yf.Ticker(f"{stock_code}.TWO")
        data = ticker.history(period="7d", interval="1d")
    name = stock_name_map.get(stock_code, ticker.info.get("shortName", "未知公司"))
    return data, name

# 畫圖
def plot_chart(data):
    spans = [6, 12, 30, 60, 90, 180]
    colors = ["orange", "cyan", "purple", "limegreen", "pink", "blue"]
    labels = [f"EMA{span}" for span in spans]
    data = add_ema(data, spans)

    apds = [mpf.make_addplot(data[f"EMA{span}"], color=colors[i], panel=0, label=labels[i]) for i, span in enumerate(spans)]

    mc = mpf.make_marketcolors(up='red', down='green', inherit=True)
    s = mpf.make_mpf_style(marketcolors=mc, base_mpf_style='yahoo')

    fig, axes = mpf.plot(
        data,
        type='candle',
        style=s,
        title='日K + EMA',
        addplot=apds,
        volume=True,
        figscale=1.2,
        figratio=(6,4),
        panel_ratios=(6,2),
        ylabel='價格',
        ylabel_lower='成交量',
        returnfig=True
    )

    # 顯示每條 EMA 的最新值
    for i, span in enumerate(spans):
        value = round(data[f"EMA{span}"].iloc[-1], 2)
        axes[0].text(data.index[-1], data[f"EMA{span}"].iloc[-1], f"{labels[i]}: {value}", fontsize=8, color=colors[i], ha='left')

    return fig

# 主執行區域
if stock_id:
    with st.spinner("載入中..."):
        data, name = fetch_data(stock_id)
        if not data.empty:
            current_price = round(data["Close"].iloc[-1], 1)
            third_result = calculate_third_rule(current_price)
            avg_list = calculate_recent_average(data)

            st.subheader(f"📊 {stock_id} - {name} 分析結果")
            for k, v in third_result.items():
                if "⬆" in k:
                    st.markdown(f"<div style='background-color:#ffe6e6;padding:4px;'>{k}：{v}</div>", unsafe_allow_html=True)
                elif "⬇" in k:
                    st.markdown(f"<div style='background-color:#e6ffe6;padding:4px;'>{k}：{v}</div>", unsafe_allow_html=True)
                elif "目前股價" in k:
                    st.markdown(f"<div style='background-color:#fff2cc;padding:6px;font-weight:bold'>{k}：{v}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"{k}：{v}")

            st.markdown("""
            ### 📊 三日均價
            """)
            for d, v in avg_list:
                st.markdown(f"- {d}：{v}")

            st.markdown("---")
            st.pyplot(plot_chart(data))

        else:
            st.warning("找不到資料，請檢查代碼是否正確或暫無資料。")
