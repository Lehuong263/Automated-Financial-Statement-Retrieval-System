import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ====== HÀM PHÂN TÍCH GIAO DỊCH NHÓM NHÀ ĐẦU TƯ ======
def analyze_investor_trade(ticker: str, df_kqkd: pd.DataFrame, df_out: pd.DataFrame):
    df_out['ngày'] = pd.to_datetime(df_out['ngày']).dt.date

    # ====== TÌM NGÀNH TỪ MÃ ======
    sector_row = df_kqkd[df_kqkd["Mã"] == ticker]
    if sector_row.empty:
        raise ValueError(f"Không tìm thấy mã {ticker} trong KQKD.csv")
    sector_icb = sector_row.iloc[0]["Ngành ICB - cấp 2"]

    # ====== TÌM NGÀNH TRONG output.csv ======
    nganh_out = df_out[df_out['ngành'].str.contains(sector_icb, case=False, na=False)]
    if nganh_out.empty:
        raise ValueError(f"Không tìm thấy ngành {sector_icb} trong output.csv")

    nganh_name = nganh_out.iloc[0]['ngành'].replace(" L2", "")
    df_nganh = df_out[df_out['ngành'] == nganh_out.iloc[0]['ngành']].copy()

    # ====== NHẬP NGÀY TỪ BÀN PHÍM ======
    start_date = input("Nhập ngày bắt đầu (YYYY-MM-DD): ")
    end_date = input("Nhập ngày kết thúc (YYYY-MM-DD): ")

    # ====== LỌC NGÀY ======
    df_nganh['ngày'] = pd.to_datetime(df_nganh['ngày'])  # vẫn giữ
    start_dt = pd.to_datetime(start_date)  # KHÔNG chuyển sang date()
    end_dt = pd.to_datetime(end_date)

    start_display = start_dt.date()
    end_display = end_dt.date()

    df_nganh = df_nganh[(df_nganh['ngày'] >= start_dt) & (df_nganh['ngày'] <= end_dt)]

    # ====== NHÓM NHÀ ĐẦU TƯ ======
    investors = ["cá_nhân", "tổ_chức_trong_nước", "tự_doanh", "nước_ngoài"]

    # ====== TÍNH BẢNG TỔNG ======
    def calc_summary(df, prefix):
        rows = []
        for inv in investors:
            col = f"{inv}_{prefix}_ròng"
            buy = df[df[col] > 0][col].sum()
            sell = df[df[col] < 0][col].sum()
            total = df[col].sum()
            rows.append([inv.replace("_", " ").title(), buy / 1e9, sell / 1e9, total / 1e9])
        return pd.DataFrame(rows, columns=["Nhóm nhà đầu tư", "Mua ròng", "Bán ròng", "Tổng GT ròng"])

    summary_khop = calc_summary(df_nganh, "khớp")
    summary_thoa = calc_summary(df_nganh, "thỏa_thuận")

    # ====== VẼ BIỂU ĐỒ KHỚP LỆNH ======
    fig_khop, ax1 = plt.subplots(figsize=(10, 4))
    ax1.bar(summary_khop["Nhóm nhà đầu tư"], summary_khop["Mua ròng"], label="Mua ròng", color='#4CAF50')
    ax1.bar(summary_khop["Nhóm nhà đầu tư"], summary_khop["Bán ròng"], label="Bán ròng", color='#FF9800')
    ax1.plot(summary_khop["Nhóm nhà đầu tư"], summary_khop["Tổng GT ròng"], color="#4B8BBE", marker='o', linewidth=2, label="Tổng GT ròng")
    ax1.set_title("KHỚP LỆNH", loc='left')
    ax1.set_ylabel("Giá trị (Tỷ VND)")
    ax1.legend()
    plt.tight_layout()
    plt.close(fig_khop)

    # ====== VẼ BIỂU ĐỒ THỎA THUẬN ======
    fig_thoa, ax2 = plt.subplots(figsize=(10, 4))
    ax2.bar(summary_thoa["Nhóm nhà đầu tư"], summary_thoa["Mua ròng"], label="Mua ròng", color='#4CAF50')
    ax2.bar(summary_thoa["Nhóm nhà đầu tư"], summary_thoa["Bán ròng"], label="Bán ròng", color='#FF9800')
    ax2.plot(summary_thoa["Nhóm nhà đầu tư"], summary_thoa["Tổng GT ròng"], color="#006699", marker='o', linewidth=2, label="Tổng GT ròng")
    ax2.set_title("THỎA THUẬN", loc='left')
    ax2.set_ylabel("Giá trị (Tỷ VND)")
    ax2.legend()
    plt.tight_layout()
    plt.close(fig_thoa)

    # ====== BIỂU ĐỒ DÒNG TIỀN ======
    # ====== BIỂU ĐỒ DÒNG TIỀN (MÔ PHỎNG DASHBOARD PLOTLY) ======
    import numpy as np
    from scipy.interpolate import make_interp_spline

    # Label tiếng Việt rõ ràng
    investor_labels = ["Cá nhân", "Tổ chức", "Tự doanh", "Nước ngoài"]
    x = np.arange(len(investor_labels))

    # Giá trị khớp và thỏa thuận
    khop_values = np.array([df_nganh[f"{inv}_khớp_ròng"].sum() / 1e9 for inv in investors])
    thoa_values = np.array([df_nganh[f"{inv}_thỏa_thuận_ròng"].sum() / 1e9 for inv in investors])

    # Interpolation cho đường cong mượt
    x_new = np.linspace(x.min(), x.max(), 300)
    khop_smooth = make_interp_spline(x, khop_values, k=3)(x_new)
    thoa_smooth = make_interp_spline(x, thoa_values, k=3)(x_new)

    fig, ax = plt.subplots(figsize=(10, 4))

    # Fill vùng dưới đường
    ax.fill_between(x_new, khop_smooth, color='dodgerblue', alpha=0.3, label='Khớp lệnh')
    ax.fill_between(x_new, thoa_smooth, color='darkblue', alpha=0.3, label='Thỏa thuận')

    # Vẽ đường
    ax.plot(x_new, khop_smooth, color='dodgerblue', linewidth=2)
    ax.plot(x_new, thoa_smooth, color='darkblue', linewidth=2)

    # Marker và text cho điểm gốc
    for i in range(len(x)):
        ax.plot(x[i], khop_values[i], 'o', color='dodgerblue')
        ax.plot(x[i], thoa_values[i], 'o', color='darkblue')
        ax.text(x[i], khop_values[i], f"{khop_values[i]:,.1f}", ha='center', va='bottom', fontsize=9,
                color='dodgerblue')
        ax.text(x[i], thoa_values[i], f"{thoa_values[i]:,.1f}", ha='center', va='bottom', fontsize=9, color='darkblue')

    # Cấu hình trục
    ax.set_xticks(x)
    ax.set_xticklabels(investor_labels)
    ax.set_title("Thống Kê Dòng Tiền", loc='left')
    ax.set_ylabel("Giá trị giao dịch (Tỷ VND)")
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.close(fig)



    df_nganh_sorted = df_nganh.sort_values('ngày')
    df_nganh_sorted['ngày'] = pd.to_datetime(df_nganh_sorted['ngày'])
    df_nganh_sorted = df_nganh_sorted.sort_values('ngày')

    grouped = df_nganh_sorted.groupby('ngày').sum()
    dates = grouped.index.strftime('%d/%m')

    col_mapping = {
        "Cá Nhân": "cá_nhân",
        "Tổ Chức Trong Nước": "tổ_chức_trong_nước",
        "Tự Doanh": "tự_doanh",
        "Nước Ngoài": "nước_ngoài"
    }
    colors = {
        "Cá Nhân": "#1f77b4",
        "Tổ Chức Trong Nước": "#ff7f0e",
        "Tự Doanh": "#2ca02c",
        "Nước Ngoài": "#d62728"
    }

    investor_labels = list(col_mapping.keys())
    x = np.arange(len(dates))

    # === Tạo figure với 2 biểu đồ song song ===
    fig_date, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    def draw_stacked(ax, prefix, title):
        pos_bottom = np.zeros(len(dates))
        neg_bottom = np.zeros(len(dates))

        for label in investor_labels:
            values = grouped[f"{col_mapping[label]}_{prefix}_ròng"] / 1e9
            values = values.values

            pos_vals = np.where(values > 0, values, 0)
            neg_vals = np.where(values < 0, values, 0)

            ax.bar(x, pos_vals, bottom=pos_bottom, label=f"{label} ({'Khớp' if prefix == 'khớp' else 'Thỏa thuận'})",
                   color=colors[label])
            ax.bar(x, neg_vals, bottom=neg_bottom, color=colors[label], alpha=0.8)

            pos_bottom += pos_vals
            neg_bottom += neg_vals

        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(dates, rotation=45)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.legend(fontsize=9)

    # Vẽ từng biểu đồ
    draw_stacked(ax1, "khớp", "Khớp Lệnh")
    draw_stacked(ax2, "thỏa_thuận", "Thỏa Thuận")

    fig_date.suptitle("Giao Dịch Theo Ngày", fontsize=14)
    plt.tight_layout()
    plt.close(fig_date)

    daily_data = df_nganh_sorted[['ngày']].copy()

    for label, col in col_mapping.items():
        daily_data[f"{label} (Khớp)"] = df_nganh_sorted[f"{col}_khớp_ròng"] / 1e9
        daily_data[f"{label} (Thỏa thuận)"] = df_nganh_sorted[f"{col}_thỏa_thuận_ròng"] / 1e9

    # Làm sạch bảng
    daily_data['ngày'] = daily_data['ngày'].dt.strftime('%d/%m/%Y')
    daily_data = daily_data.groupby('ngày').sum().reset_index()
    # Đổi tên cột "ngày" -> "Ngày" viết hoa
    daily_data.rename(columns={"ngày": "Ngày"}, inplace=True)

    # Chuyển thành HTML table, và in đậm cột "Ngày" bằng định dạng CSS thủ công
    daily_html = daily_data.to_html(
        index=False,
        float_format='{:,.2f}'.format,
        border=0,
        classes='financial-table'
    )
    # ==== Cuối hàm, thêm vào return ====
    return summary_khop, summary_thoa, nganh_name, start_display, end_display, fig_khop, fig_thoa, fig, fig_date,daily_html
def generate_investor_trade_html(ticker, df_kqkd, df_out):
    import base64
    from io import BytesIO

    summary_khop, summary_thoa, nganh_name, start_dt, end_dt, fig1, fig2, fig3, fig4,daily_html = analyze_investor_trade(ticker, df_kqkd, df_out)

    def fig_to_base64(fig):
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        return f"<img src='data:image/png;base64,{img_base64}' style='max-width:100%; margin-bottom:20px;'>"


    summary_khop.columns = [
        "Nhóm nhà đầu tư",
        "Mua ròng (Tỷ VNĐ)",
        "Bán ròng (Tỷ VNĐ)",
        "Tổng GT ròng (Tỷ VNĐ)"
    ]
    summary_thoa.columns = [
        "Nhóm nhà đầu tư",
        "Mua ròng (Tỷ VNĐ)",
        "Bán ròng (Tỷ VNĐ)",
        "Tổng GT ròng (Tỷ VNĐ)"
    ]

    html = f"""
    <div style='font-size:13px; color:#666; margin-bottom:10px;'>
        Dữ liệu giao dịch theo phân ngành ICB cấp 2 <strong>{nganh_name}</strong><br>
        Dữ liệu từ ngày {start_dt.strftime('%d/%m/%Y')} đến {end_dt.strftime('%d/%m/%Y')}
    </div>

    <h4 style='color:#004080; margin-top:20px;'>KHỚP LỆNH</h4>
    {summary_khop.to_html(index=False, float_format='{:,.2f}'.format, border=0, classes='financial-table')}
    {fig_to_base64(fig1)}

    <h4 style='color:#004080; margin-top:20px;'>THỎA THUẬN</h4>
    {summary_thoa.to_html(index=False, float_format='{:,.2f}'.format, border=0, classes='financial-table')}
    {fig_to_base64(fig2)}

    <h4 style='color:#004080; margin-top:20px;'>THỐNG KÊ DÒNG TIỀN</h4>
    {fig_to_base64(fig3)}
    
    <h4 style='color:#004080; margin-top:20px;'>GIAO DỊCH THEO NGÀY</h4>
    {fig_to_base64(fig4)}
    
    <h4 style='color:#004080; margin-top:20px;'>BẢNG GIAO DỊCH THEO NGÀY (Đơn vị: Tỷ VNĐ)</h4>
    {daily_html}
    """
    return html
