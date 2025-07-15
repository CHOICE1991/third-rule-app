import tkinter as tk
from tkinter import messagebox, ttk
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf

# 從 CSV 載入股票代碼與公司名稱
try:
    stock_df = pd.read_csv("tw_stocks.csv", dtype=str)
    custom_names = dict(zip(stock_df["股票代碼"], stock_df["公司名稱"]))
except:
    custom_names = {}

def get_stock_data(stock_code):
    try:
        ticker = yf.Ticker(f"{stock_code}.TW")
        daily_data = ticker.history(period="7d", interval="1d")
        intraday_data = ticker.history(period="5d", interval="5m")
        info = ticker.info
        if daily_data.empty:
            ticker = yf.Ticker(f"{stock_code}.TWO")
            daily_data = ticker.history(period="7d", interval="1d")
            intraday_data = ticker.history(period="5d", interval="5m")
            info = ticker.info
        name = custom_names.get(stock_code, info.get("shortName", "未知公司"))
        return daily_data, intraday_data, name
    except Exception as e:
        print(f"錯誤：{e}")
        return None, None, "未知公司"

def calculate_third_rule(price):
    base = round(price * 0.07 / 3)
    result = {
        "目前股價 💰        ": price,
        "基礎數值（四捨五入）": base,
        "⬆ 往上 10%        ": round(price + 3 * base + base, 1),
        "⬆ 往上 7%         ": round(price + 2 * base + base, 1),
        "⬆ 往上 2/3        ": round(price + 2 * base, 1),
        "⬆ 往上 1/3        ": round(price + base, 1),
        "────────────": "────────────",
        "⬇ 往下 1/3        ": round(price - base, 1),
        "⬇ 往下 2/3        ": round(price - 2 * base, 1),
        "⬇ 往下 7%         ": round(price - 2 * base - base, 1),
        "⬇ 往下 10%        ": round(price - 3 * base - base, 1)
    }
    return result

def add_ema(data, spans):
    for span in spans:
        data[f"EMA{span}"] = data["Close"].ewm(span=span).mean()
    return data

def detect_crossovers(data):
    alerts = []
    for i in range(1, len(data)):
        if data["EMA6"].iloc[i-1] < data["EMA30"].iloc[i-1] and data["EMA6"].iloc[i] > data["EMA30"].iloc[i]:
            alerts.append((data.index[i], data["Close"].iloc[i], "金叉：EMA6 上穿 EMA30"))
        elif data["EMA6"].iloc[i-1] > data["EMA30"].iloc[i-1] and data["EMA6"].iloc[i] < data["EMA30"].iloc[i]:
            alerts.append((data.index[i], data["Close"].iloc[i], "死叉：EMA6 下穿 EMA30"))
    return alerts

def calculate_recent_average(data):
    results = []
    for offset in range(1, 4):
        row = data.iloc[-offset]
        avg = round((row['Open'] + row['High'] + row['Low'] + row['Close']) / 4, 2)
        date_str = row.name.strftime("%Y-%m-%d")
        results.append((date_str, avg))
    return results  # [(日期, 均價), ...]

def plot_trend_with_ema(daily_data, intraday_data):
    if daily_data is None or intraday_data is None:
        messagebox.showerror("錯誤", "找不到股票資料")
        return

    spans = [6, 12, 30, 60, 90, 180]
    colors = ["orange", "cyan", "purple", "limegreen", "pink", "blue"]
    labels = ["EMA6", "EMA12", "EMA30", "EMA60", "EMA90", "EMA180"]

    daily_data = add_ema(daily_data, spans)
    intraday_data = add_ema(intraday_data, spans)

    alerts = detect_crossovers(daily_data)
    avg_list = calculate_recent_average(daily_data)

    apds_daily = [mpf.make_addplot(daily_data[f"EMA{span}"], color=colors[i], panel=0, label=labels[i]) for i, span in enumerate(spans)]
    apds_intra = [mpf.make_addplot(intraday_data[f"EMA{span}"], color=colors[i], panel=0, label=labels[i]) for i, span in enumerate(spans)]

    mc = mpf.make_marketcolors(up='red', down='green', inherit=True)
    s = mpf.make_mpf_style(marketcolors=mc, base_mpf_style='yahoo')

    fig_daily, axes_daily = mpf.plot(
        daily_data,
        type='candle',
        style=s,
        title='日K + EMA',
        addplot=apds_daily,
        volume=True,
        figscale=1.2,
        figratio=(6,4),
        panel_ratios=(6,2),
        ylabel='價格',
        ylabel_lower='成交量',
        returnfig=True,
        datetime_format='%Y-%m-%d'
    )
    axes_daily[0].legend(loc='upper left')

    for i, span in enumerate(spans):
        value = round(daily_data[f"EMA{span}"].iloc[-1], 2)
        axes_daily[0].text(daily_data.index[-1], daily_data[f"EMA{span}"].iloc[-1], f"{labels[i]}: {value}", fontsize=8, color=colors[i], ha='left')

    for alert in alerts[-3:]:
        axes_daily[0].annotate(alert[2], xy=(alert[0], alert[1]), xytext=(alert[0], alert[1] * 1.03),
                               textcoords="data", ha="center", fontsize=9,
                               bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='red'),
                               arrowprops=dict(facecolor='red', arrowstyle="->"))

    avg_str = " / ".join([f"{d}：{v}" for d, v in avg_list])
    axes_daily[0].text(0.02, 0.92, f"📊 三日均價：{avg_str}",
                      transform=axes_daily[0].transAxes, fontsize=10, verticalalignment='top')

    fig_intra, axes_intra = mpf.plot(
        intraday_data,
        type='candle',
        style=s,
        title='5分K + EMA',
        addplot=apds_intra,
        volume=True,
        figscale=1.2,
        figratio=(6,4),
        panel_ratios=(6,2),
        ylabel='價格',
        ylabel_lower='成交量',
        returnfig=True,
        datetime_format='%Y-%m-%d %H:%M'
    )
    axes_intra[0].legend(loc='upper left')

    for i, span in enumerate(spans):
        value = round(intraday_data[f"EMA{span}"].iloc[-1], 2)
        axes_intra[0].text(intraday_data.index[-1], intraday_data[f"EMA{span}"].iloc[-1], f"{labels[i]}: {value}", fontsize=8, color=colors[i], ha='left')

    plt.show()

def analyze():
    stock_id = entry.get()
    if not stock_id:
        messagebox.showwarning("輸入錯誤", "請輸入股票代碼")
        return

    daily_data, intraday_data, name = get_stock_data(stock_id)
    if daily_data is None:
        messagebox.showerror("錯誤", "無法取得股價資料")
        return

    latest_price = round(daily_data['Close'][-1], 1)
    result = calculate_third_rule(latest_price)
    avg_list = calculate_recent_average(daily_data)

    output.config(state='normal')
    output.delete("1.0", tk.END)
    output.insert(tk.END, f"📊 計算結果：{stock_id} - {name}\n\n")
    for key, value in result.items():
        if "目前股價" in key:
            output.insert(tk.END, f"{key}: {value}\n", "price")
        elif "⬆" in key:
            output.insert(tk.END, f"{key}: {value}\n", "up")
        elif "⬇" in key:
            output.insert(tk.END, f"{key}: {value}\n", "down")
        else:
            output.insert(tk.END, f"{key}: {value}\n")

    output.insert(tk.END, "\n📊 三日均價：\n")
    for d, v in avg_list:
        output.insert(tk.END, f"{d}：{v}\n")

    output.config(state='disabled')
    plot_trend_with_ema(daily_data, intraday_data)

# GUI 介面
window = tk.Tk()
window.title("📈 三分之一法股價工具 v2")
window.geometry("450x620")
window.configure(bg="#f5f5f5")

style = ttk.Style()
style.theme_use('clam')
style.configure("TButton", font=("Arial", 16), padding=6)

header = tk.Label(window, text="🔍 三分之一法股價分析工具", font=("Arial", 18, "bold"), bg="#f5f5f5")
header.pack(pady=(20, 10))

label = tk.Label(window, text="請輸入股票代碼（如 2330）", font=("Arial", 12), bg="#f5f5f5")
label.pack()

entry = tk.Entry(window, font=("Arial", 14), width=20, justify='center')
entry.pack(pady=5)

button = ttk.Button(window, text="分析股價", command=analyze)
button.pack(pady=10)

output = tk.Text(window, height=25, width=50, font=("Courier New", 12), state='disabled', bg="#ffffff")
output.tag_configure("up", background="#ffe6e6")
output.tag_configure("down", background="#e6ffe6")
output.tag_configure("price", background="#fff2cc", font=("Courier New", 12, "bold"))
output.pack(pady=(10, 20))

window.mainloop()
