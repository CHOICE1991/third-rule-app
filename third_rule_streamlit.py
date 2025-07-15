# streamlit_app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt

# 設定樣式
st.set_page_config(page_title="三分之一法股價工具", layout="wide")
st.title("📈 三分之一法股價分析工具")

# 股票代碼輸入
stock_id = st.text_input("請輸入股票代碼（如 2330）")

# 計算三分之一法
@st.cache_data
def calculate_third_rule(price):
    base = round(price * 0.07 / 3)
    return {
        "目前股價 💰": price,
        "基礎數值（四捨五入）": base,
        "⬆ 往上 10%": round(price + 4 * base, 1),
        "⬆ 往上 7%": round(price + 3 * base, 1),
        "⬆ 往上 2/3": round(price + 2 * base, 1),
        "⬆ 往上 1/3": round(price + base, 1),
        "⬇ 往下 1/3": round(price - base, 1),
        "⬇ 往下 2/3": round(price - 2 * base, 1),
        "⬇ 往下 7%": round(price - 3 * base, 1),
        "⬇ 往下 10%": round(price - 4 * base, 1),
    }

# 加入 EMA 計算
@st.cache_data
def add_ema(data, spans):
    for span in spans:
        data[f"EMA{span}"] = data['Close'].ewm(span=span).mean()
    return data

# 三日均價
def calculate_recent_avg(data):
    results = []
    for i in range(1, 4):
        row = data.iloc[-i]
        avg = round((row['Open'] + row['High'] + row['Low'] + row['Close']) / 4, 2)
        results.append((row.name.strftime("%Y-%m-%d"), avg))
    return results

# 判斷金叉死叉
def detect_crossovers(data):
    events = []
    for i in range(1, len(data)):
        if data['EMA6'].iloc[i-1] < data['EMA30'].iloc[i-1] and data['EMA6'].iloc[i] > data['EMA30'].iloc[i]:
            events.append((data.index[i], data['Close'].iloc[i], '金叉'))
        elif data['EMA6'].iloc[i-1] > data['EMA30'].iloc[i-1] and data['EMA6'].iloc[i] < data['EMA30'].iloc[i]:
            events.append((data.index[i], data['Close'].iloc[i], '死叉'))
    return events

# 畫圖
def plot_chart(data, spans):
    data = add_ema(data.copy(), spans)
    cross = detect_crossovers(data)
    apds = [mpf.make_addplot(data[f"EMA{span}"], color=color, width=1, label=f"EMA{span}")
            for span, color in zip(spans, ['orange','cyan','purple','limegreen','pink','blue'])]
    mc = mpf.make_marketcolors(up='red', down='green')
    style = mpf.make_mpf_style(marketcolors=mc)
    fig, axes = mpf.plot(
        data,
        type='candle',
        addplot=apds,
        style=style,
        returnfig=True,
        volume=True,
        ylabel='價格',
        figratio=(10,6),
        datetime_format='%m-%d'
    )
    for dt, price, label in cross[-3:]:
        axes[0].annotate(label, xy=(dt, price), xytext=(dt, price*1.03),
                         textcoords="data", ha="center",
                         bbox=dict(facecolor='white', edgecolor='red'),
                         arrowprops=dict(facecolor='red', arrowstyle='->'))
    st.pyplot(fig)

# 主邏輯
if stock_id:
    try:
        ticker = yf.Ticker(f"{stock_id}.TW")
        daily = ticker.history(period="7d", interval="1d")
        if daily.empty:
            ticker = yf.Ticker(f"{stock_id}.TWO")
            daily = ticker.history(period="7d", interval="1d")
        name = ticker.info.get("shortName", "未知公司")

        st.subheader(f"📊 {stock_id} - {name} 最新分析")
        price = round(daily['Close'].iloc[-1], 1)
        result = calculate_third_rule(price)

        col1, col2 = st.columns(2)
        with col1:
            for k in ["⬆ 往上 10%", "⬆ 往上 7%", "⬆ 往上 2/3", "⬆ 往上 1/3"]:
                st.markdown(f"🟩 **{k}**：{result[k]}")
        with col2:
            for k in ["⬇ 往下 1/3", "⬇ 往下 2/3", "⬇ 往下 7%", "⬇ 往下 10%"]:
                st.markdown(f"🟥 **{k}**：{result[k]}")

        st.info(f"目前股價 💰：{price} 元\n\n基礎數值：{result['基礎數值（四捨五入）']} 元")

        st.markdown("---")
        spans = [6,12,30,60,90,180]
        plot_chart(daily, spans)

        avg3 = calculate_recent_avg(daily)
        st.markdown("**📆 三日均價（開高低收平均）：**")
        for d, v in avg3:
            st.write(f"{d}：{v} 元")

    except Exception as e:
        st.error(f"錯誤：{e}")
