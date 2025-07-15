
output.insert(tk.END, f"📊 計算結果：{stock_id} - {name}\n\n")
for key, value in result.items():
    if "目前股價" in key:
        output.insert(tk.END, f"{key} {value}\n", "price")
    elif "⬆" in key:
        output.insert(tk.END, f"{key} {value}\n", "up")
    elif "⬇" in key:
        output.insert(tk.END, f"{key} {value}\n", "down")
    else:
        output.insert(tk.END, f"{key}\n")
