
import streamlit as st
import pandas as pd
import yfinance as yf
import mplfinance as mpf

st.title("📈 台股自動飆股偵測器（純 Yahoo Finance）")

# 讀取所有上市櫃股票代碼
try:
    df_map = pd.read_csv("tw_stocks.csv", dtype=str)
    codes = df_map["股票代碼"].tolist()
except FileNotFoundError:
    st.error("找不到 tw_stocks.csv，請將股票代碼對照表放在專案根目錄。")
    st.stop()

# 參數設定
vol_mult = st.slider("爆量倍率（當日量 > 前5日平均量 × N）", 1.5, 5.0, 2.0, 0.5)
min_days = st.slider("最低資料天數（至少要有 x 天歷史）", 20, 90, 30, 10)

if st.button("開始自動篩選"):
    results = []
    progress = st.progress(0)
    total = len(codes)
    for idx, code in enumerate(codes):
        progress.progress((idx+1)/total)
        ticker = yf.Ticker(f"{code}.TW")
        df = ticker.history(period="3mo", interval="1d")
        if df.empty or len(df) < min_days:
            continue

        df["EMA6"] = df["Close"].ewm(span=6).mean()
        df["EMA30"] = df["Close"].ewm(span=30).mean()
        df["MA5Vol"] = df["Volume"].rolling(5).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        golden = prev["EMA6"] < prev["EMA30"] and last["EMA6"] > last["EMA30"]
        spike = last["Volume"] > vol_mult * last["MA5Vol"] and last["Close"] > prev["Close"]

        if golden and spike:
            results.append({
                "代碼": code,
                "名稱": (df_map.loc[df_map["股票代碼"]==code, "公司名稱"].values[0] if code in df_map["股票代碼"].values else ""),
                "收盤": round(last["Close"],2),
                "成交量": int(last["Volume"])
            })

    progress.empty()
    if not results:
        st.warning("找不到符合條件的飆股")
    else:
        df_res = pd.DataFrame(results)
        st.dataframe(df_res)

        # 顯示第一檔飆股的 K 線圖
        sel = df_res.iloc[0]["代碼"]
        df2 = yf.Ticker(f"{sel}.TW").history(period="1mo", interval="1d")
        mc = mpf.make_marketcolors(up='red', down='green')
        fig, ax = mpf.plot(
            df2, type='candle', mav=(6,30),
            volume=True, returnfig=True,
            style=mpf.make_mpf_style(marketcolors=mc),
            title=f"{sel} K 線圖"
        )
        st.pyplot(fig)
