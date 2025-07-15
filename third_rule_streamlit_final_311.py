
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 標題
st.title("📊 三分之一法股價分析工具")

# 股票代碼輸入
stock_code = st.text_input("請輸入台股股票代碼（如 2330）")

# 計算三分之一法邏輯
def calculate_third_rule(price):
    base = round(price * 0.07 / 3)
    return {
        "目前股價 💰": price,
        "基礎數值（四捨五入）": base,
        "⬆ 往上 10%": round(price + 4 * base, 1),
        "⬆ 往上 7%": round(price + 3 * base, 1),
        "⬆ 往上 2/3": round(price + 2 * base, 1),
        "⬆ 往上 1/3": round(price + base, 1),
        "────────────": "────────────",
        "⬇ 往下 1/3": round(price - base, 1),
        "⬇ 往下 2/3": round(price - 2 * base, 1),
        "⬇ 往下 7%": round(price - 3 * base, 1),
        "⬇ 往下 10%": round(price - 4 * base, 1)
    }

# 畫面顯示邏輯
if stock_code:
    try:
        ticker = yf.Ticker(f"{stock_code}.TW")
        hist = ticker.history(period="90d")
        name = ticker.info.get("shortName", "未知公司")
        if hist.empty:
            ticker = yf.Ticker(f"{stock_code}.TWO")
            hist = ticker.history(period="90d")
            name = ticker.info.get("shortName", "未知公司")

        if hist.empty:
            st.error("⚠️ 找不到此股票資料")
        else:
            close_price = round(hist['Close'][-1], 1)
            rule_result = calculate_third_rule(close_price)

            st.subheader(f"📈 {stock_code} - {name}")
            for key, value in rule_result.items():
                if "⬆" in key:
                    st.markdown(f"<div style='color:red;'>{key}: {value}</div>", unsafe_allow_html=True)
                elif "⬇" in key:
                    st.markdown(f"<div style='color:green;'>{key}: {value}</div>", unsafe_allow_html=True)
                else:
                    st.write(f"{key}: {value}")

            # 繪製K線圖與EMA
            df = hist.copy()
            df["EMA6"] = df["Close"].ewm(span=6).mean()
            df["EMA30"] = df["Close"].ewm(span=30).mean()

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df.index, df["Close"], label="收盤價", color="black")
            ax.plot(df.index, df["EMA6"], label="EMA6", color="orange")
            ax.plot(df.index, df["EMA30"], label="EMA30", color="blue")
            ax.set_title(f"{stock_code} K線與EMA")
            ax.legend()
            st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ 發生錯誤：{e}")
