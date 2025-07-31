import streamlit as st
import pandas as pd
import yfinance as yf
import mplfinance as mpf

st.title("📈 台股自動飆股偵測器（Bulk 下載版）")

# 載入所有股票代碼
try:
    df_map = pd.read_csv("tw_stocks.csv", dtype=str)
    codes = df_map["股票代碼"].tolist()
    names_map = dict(zip(df_map["股票代碼"], df_map["公司名稱"]))
except Exception as e:
    st.error(f"載入 tw_stocks.csv 失敗: {e}")
    st.stop()

# 參數設定
vol_mult = st.slider("爆量倍率 (Volume > 前5日平均 × N)", 1.5, 5.0, 2.0, 0.5)
min_days = st.slider("最低歷史天數", 20, 90, 30, 10)

if st.button("開始篩選"):
    tickers = [f"{code}.TW" for code in codes]
    # Bulk download
    data = yf.download(tickers, period="3mo", interval="1d", group_by="ticker", threads=True)

    results = []
    progress = st.progress(0)
    total = len(codes)
    for idx, code in enumerate(codes):
        progress.progress((idx+1)/total)
        try:
            df = data[code + ".TW"].dropna()
        except KeyError:
            continue
        if len(df) < min_days:
            continue
        df["EMA6"] = df["Close"].ewm(span=6).mean()
        df["EMA30"] = df["Close"].ewm(span=30).mean()
        df["MA5Vol"] = df["Volume"].rolling(5).mean()
        last = df.iloc[-1]
        prev = df.iloc[-2]
        golden = (prev["EMA6"] < prev["EMA30"]) and (last["EMA6"] > last["EMA30"])
        spike  = (last["Volume"] > vol_mult * last["MA5Vol"]) and (last["Close"] > prev["Close"])
        if golden and spike:
            results.append({"代碼": code, "名稱": names_map.get(code, ""), "收盤": round(last["Close"],2), "成交量": int(last["Volume"])})
    progress.empty()
    if not results:
        st.warning("找不到符合條件的飆股")
    else:
        df_res = pd.DataFrame(results)
        st.dataframe(df_res)
        sel = df_res.iloc[0]["代碼"]
        df2 = data[sel + ".TW"].dropna().tail(30)
        mc = mpf.make_marketcolors(up='red', down='green')
        fig, ax = mpf.plot(df2, type='candle', mav=(6,30), volume=True, returnfig=True,
                           style=mpf.make_mpf_style(marketcolors=mc),
                           title=f"{sel} ({names_map.get(sel)}) 最近 1 個月 K 線")
        st.pyplot(fig)