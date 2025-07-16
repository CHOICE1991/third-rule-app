import streamlit as st
import pandas as pd
import yfinance as yf
import mplfinance as mpf

st.title("📈 台股飆股偵測器（純 Yahoo Finance）")

# 輸入欲篩選的股票代碼（逗號分隔，如：2330,2454）
codes_input = st.text_input("輸入股票代碼（逗號分隔，例如：2330,2454）")
codes = [c.strip() for c in codes_input.split(",") if c.strip()]

# 爆量倍率設定
vol_mult = st.slider("爆量倍率（當日量 > 前5日平均量 × N）", 1.5, 5.0, 2.0, 0.5)

if st.button("開始篩選"):
    spikes = []
    for code in codes:
        try:
            # 取得最近三個月的日線資料
            df = yf.Ticker(f"{code}.TW").history(period="3mo", interval="1d")
        except Exception as e:
            continue

        if df.empty or len(df) < 7:
            continue

        # 計算技術指標
        df["EMA6"]   = df["Close"].ewm(span=6).mean()
        df["EMA30"]  = df["Close"].ewm(span=30).mean()
        df["MA5Vol"] = df["Volume"].rolling(5).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 判斷 EMA6 上穿 EMA30（金叉）
        golden = (prev["EMA6"] < prev["EMA30"]) and (last["EMA6"] > last["EMA30"])
        # 判斷爆量且收紅
        spike  = (last["Volume"] > vol_mult * last["MA5Vol"]) and (last["Close"] > prev["Close"])

        if golden and spike:
            spikes.append((code, round(last["Close"], 2), int(last["Volume"])))

    if not spikes:
        st.warning("找不到符合條件的飆股")
    else:
        df_spike = pd.DataFrame(spikes, columns=["代碼", "收盤", "成交量"])
        st.dataframe(df_spike)

        # 顯示第一檔飆股的 K 線圖
        sel = df_spike.iloc[0]["代碼"]
        hist1m = yf.Ticker(f"{sel}.TW").history(period="1mo", interval="1d")
        mc = mpf.make_marketcolors(up='red', down='green')
        fig, axlist = mpf.plot(
            hist1m, type='candle', mav=(6,30),
            volume=True, returnfig=True,
            style=mpf.make_mpf_style(marketcolors=mc)
        )
        st.pyplot(fig)