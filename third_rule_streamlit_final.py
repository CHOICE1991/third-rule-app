import streamlit as st
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt

# 頁面設定
st.set_page_config(page_title="三分之一法股價分析工具", layout="wide")
st.title("📈 三分之一法股價分析工具")

# 輸入股票代碼
stock_symbol = st.text_input("請輸入股票代碼（如 2330 ）", value="2330")

if stock_symbol:
    stock_symbol = stock_symbol.strip()
    ticker_symbol = f"{stock_symbol}.TW"
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="90d")

    if hist.empty:
        st.error("找不到此股票資料，請確認代碼正確。")
    else:
        stock_info = ticker.info
        stock_name = stock_info.get("longName", "N/A").upper()

        # 取得最新股價與均線
        price = hist["Close"].iloc[-1]
        base = round(price * 0.07 / 3)
        avg_price_today = round((hist["High"].iloc[-1] + hist["Low"].iloc[-1] + hist["Close"].iloc[-1]) / 3, 1)
        avg_1d = round((hist["High"].iloc[-2] + hist["Low"].iloc[-2] + hist["Close"].iloc[-2]) / 3, 1)
        avg_2d = round((hist["High"].iloc[-3] + hist["Low"].iloc[-3] + hist["Close"].iloc[-3]) / 3, 1)

        # 顯示標題與漲跌資料
        st.subheader(f"📊 {stock_symbol} - {stock_name} 最新分析")

        # 計算目標區間
        up_10 = round(price + 4 * base, 1)
        up_7 = round(price + 3 * base, 1)
        up_2_3 = round(price + 2 * base, 1)
        up_1_3 = round(price + base, 1)

        down_1_3 = round(price - base, 1)
        down_2_3 = round(price - 2 * base, 1)
        down_7 = round(price - 3 * base, 1)
        down_10 = round(price - 4 * base, 1)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<span style='color:green;'>⬆ 往上 10%：{up_10}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:green;'>⬆ 往上 7%：{up_7}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:green;'>⬆ 往上 2/3：{up_2_3}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:green;'>⬆ 往上 1/3：{up_1_3}</span>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<span style='color:red;'>⬇ 往下 1/3：{down_1_3}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:red;'>⬇ 往下 2/3：{down_2_3}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:red;'>⬇ 往下 7%：{down_7}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:red;'>⬇ 往下 10%：{down_10}</span>", unsafe_allow_html=True)

        # 顯示目前價格與基礎數值
        st.info(f"目前股價 💰：{price} 元\n\n基礎數值：{base} 元\n\n三日均價：[ 今天：{avg_price_today}，昨天：{avg_1d}，前天：{avg_2d} ]")

        # 計算與繪製K線圖與EMA
        hist["EMA6"] = hist["Close"].ewm(span=6, adjust=False).mean()
        hist["EMA12"] = hist["Close"].ewm(span=12, adjust=False).mean()
        hist["EMA30"] = hist["Close"].ewm(span=30, adjust=False).mean()
        hist["EMA60"] = hist["Close"].ewm(span=60, adjust=False).mean()

        mc = mpf.make_marketcolors(up="red", down="green", inherit=True)
        s  = mpf.make_mpf_style(marketcolors=mc)

        fig, axlist = mpf.plot(
            hist[-60:], type='candle',
            style=s,
            mav=(6, 12, 30, 60),
            volume=True,
            returnfig=True,
            title=f"{stock_symbol} - K 線圖與均線分析"
        )
        st.pyplot(fig)
