
import streamlit as st
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from goodinfo import GoodInfoStock
from io import BytesIO
import base64

st.title("📈 台股飆股偵測器（GoodInfo + EMA 金叉 + 爆量）")

# 選擇欲篩選的股票清單（可替換為多檔）
stock_list = st.text_input("輸入股票代碼，逗號分隔（例如：2330,2454...)").split(",")

detect_days = st.slider("過去天數內爆量倍率", min_value=1.5, max_value=5.0, value=2.0, step=0.5)

if st.button("開始篩選"):
    results = []

    for code in stock_list:
        code = code.strip()
        stock = GoodInfoStock(code)
        if not stock.success:
            continue

        df = stock.PriceHistory(period='3m', interval='d')  # DataFrame with Date, Close, Volume ...
        df = df.set_index("Date")
        df["EMA6"] = df["Close"].ewm(span=6).mean()
        df["EMA30"] = df["Close"].ewm(span=30).mean()
        df["MA5Vol"] = df["Volume"].rolling(5).mean()

        # 技術面判斷：金叉
        last = df.iloc[-1]
        prev = df.iloc[-2]
        golden = (prev["EMA6"] < prev["EMA30"]) and (last["EMA6"] > last["EMA30"])

        # 爆量＋收紅
        spike = (last["Volume"] > detect_days * last["MA5Vol"]) and (last["Close"] > prev["Close"])

        if golden and spike:
            results.append((code, stock.BasicInfo()["shortName"], last["Close"], last["Volume"]))

    if not results:
        st.warning("找不到符合條件的飆股")
    else:
        df_res = pd.DataFrame(results, columns=["代碼", "名稱", "收盤", "成交量"])
        st.dataframe(df_res)

        for idx, row in df_res.iterrows():
            code, name = row["代碼"], row["名稱"]
            df = GoodInfoStock(code).PriceHistory(period='1m', interval='d').set_index("Date")

            apds = [
                mpf.make_addplot(df["Close"].ewm(span=6).mean(), color='orange'),
                mpf.make_addplot(df["Close"].ewm(span=30).mean(), color='blue')
            ]
            mc = mpf.make_marketcolors(up='red', down='green')
            fig, axlist = mpf.plot(df, type='candle', style=mpf.make_mpf_style(marketcolors=mc),
                                   addplot=apds, returnfig=True, volume=True, title=f"{code} {name}")
            st.pyplot(fig)
