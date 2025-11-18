import pandas as pd
import matplotlib.pyplot as plt
import pandas_ta as ta
import os
from matplotlib.backends.backend_pdf import PdfPages
from vnstock import Vnstock
import sys
# ==== 1. Lấy dữ liệu & chuẩn bị ====
def generate_technical_analysis(ticker, start_date, end_date):

    # === Tính ngày bắt đầu để lấy dữ liệu đầy đủ cho chỉ báo ===
    start_dt = pd.to_datetime(start_date)
    start_60_before = (start_dt - pd.Timedelta(days=60)).strftime('%Y-%m-%d')

    # Lùi về 60 ngày để đủ dữ liệu tính chỉ báo
    df_full = Vnstock().stock(symbol=ticker, source='VCI').quote.history(start=start_60_before, end=end_date)
    df_full['time'] = pd.to_datetime(df_full['time'])
    df_full.set_index('time', inplace=True)
    df_full = df_full[['open', 'high', 'low', 'close', 'volume']]
    df_full.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    # Chỉ giữ phần dữ liệu cần hiển thị (sau khi tính đủ chỉ báo)
    df = df_full.copy()

    # ==== 2. Tính chỉ báo kỹ thuật ====
    df['MA20'] = ta.sma(df['Close'], length=20)
    bb = ta.bbands(df['Close'], length=20)
    df = pd.concat([df, bb], axis=1)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    ema12 = ta.ema(df['Close'], length=12)
    ema26 = ta.ema(df['Close'], length=26)
    df['MACD'] = ema12 - ema26
    df['Signal'] = ta.ema(df['MACD'], length=9)
    df['Histogram'] = df['MACD'] - df['Signal']

    # ==== 3. Cắt phần hiển thị theo yêu cầu ====
    df = df.loc[start_date:end_date]
    df = df.reset_index()
    df.rename(columns={'time': 'Date'}, inplace=True)
    df['x'] = range(len(df))
    # để index là số nguyên cho trục X liên tục

    # ==== 4. Vẽ biểu đồ ====
    fig = plt.figure(figsize=(14, 11))  # tăng chiều cao
    gs = fig.add_gridspec(3, 1, height_ratios=[6, 1.3, 1.7], hspace=0.3)

    # === 4.1 Biểu đồ giá (nến, MA20, BB, volume) ===
    ax1 = fig.add_subplot(gs[0])
    colors = ['green' if c >= o else 'red' for c, o in zip(df['Close'], df['Open'])]
    for i, row in df.iterrows():
        color = 'green' if row['Close'] >= row['Open'] else 'red'
        ax1.vlines(row['x'], row['Low'], row['High'], color=color, linewidth=1)
        ax1.vlines(row['x'], row['Open'], row['Close'], color=color, linewidth=6)

    ax1.plot(df['x'], df['MA20'], label='MA20', color='orange', linewidth=1.5)
    ax1.plot(df['x'], df['BBL_20_2.0'], linestyle='dotted', color='gray')
    ax1.plot(df['x'], df['BBU_20_2.0'], linestyle='dotted', color='gray')
    ax1.set_xlim(df['x'].min() - 0.5, df['x'].max() + 0.5)
    ax1.set_ylabel("Giá")

    # Volume scale nhỏ dưới giá (trục phụ)
    ax1v = ax1.twinx()
    ax1v.bar(df['x'], df['Volume'] / 1e6, color=colors, alpha=0.3, width=0.9)
    ax1v.set_ylabel("Volume (triệu CP)")
    ax1v.set_ylim(0, (df['Volume'] / 1e6).max() * 5)
    ax1.set_title(f"Phân tích kỹ thuật {ticker}")

    # === 4.2 RSI ===
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.plot(df['x'], df['RSI'], label='RSI 14', color='royalblue')
    ax2.axhline(70, color='royalblue', linestyle='--', linewidth=1)
    ax2.axhline(30, color='royalblue', linestyle='--', linewidth=1)
    ax2.fill_between(df['x'], 30, 70, color='royalblue', alpha=0.05) # ✅ chỉ tô vùng 30–70
    ax2.set_yticks([30, 70])
    ax2.set_ylabel("RSI 14")
    ax2.set_ylim(20, 80)  # hoặc 25–75 tùy bạn
    ax2.legend(loc='upper left')

    # === 4.3 MACD ===
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax3.plot(df['x'], df['MACD'], label='MACD 12-26', color='green', linewidth=2)
    ax3.plot(df['x'], df['Signal'], label='Signal 9', color='red', linewidth=1.5)
    ax3.set_ylabel("MACD")
    ax3.legend(loc='upper left')

    # Histogram dùng trục phụ và scale thấp xuống
    ax3v = ax3.twinx()
    hist_colors = df['Histogram'].apply(lambda x: 'green' if x >= 0 else 'red')
    ax3v.bar(df['x'], df['Histogram'], color=hist_colors, alpha=0.4, width=0.9)

    # Scale nhỏ để histogram không lấn trục chính
    hist_max = df['Histogram'].abs().max()
    ax3v.set_ylim(-hist_max * 4, hist_max * 4)
    ax3v.set_yticks([])  # Ẩn nhãn trục phụ nếu muốn gọn

    # === 4.4 Trục X hiển thị thông minh ===
    step = max(1, len(df) // 10)
    xticks = df['x'][::step]
    xticklabels = df['Date'].dt.strftime('%Y-%m-%d')[::step]
    ax3.set_xticks(xticks)
    ax3.set_xticklabels(xticklabels, rotation=45, ha='right')

    # === 5. Export ra PDF ===
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports', 'chart_ta.png'))
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    import base64
    with open(output_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")

    return f'<img src="data:image/png;base64,{encoded}" style="width:100%; max-height:500px;">'