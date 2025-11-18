import pandas as pd
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import base64
from io import BytesIO
def format_number(x):
    return f"{x:,.0f}" if pd.notna(x) else ""
from ai_analyzer import (
    generate_return_ratio_analysis,
    generate_activity_analysis,
    generate_dupont_analysis,
    generate_profit_analysis
)
def prepare_financial_ratios_html(ticker):
    # Định nghĩa đường dẫn file
    file1 = r"D:\Python Project\10_diem - Copy\data\financial\financial_ratios.csv"
    file2 = fr"D:\Python Project\10_diem - Copy\data\calculate\{ticker}_financial_ratios.csv"
    # Đọc file CSV, nếu lỗi thì bỏ qua
    try:
        df1 = pd.read_csv(file1)
    except FileNotFoundError:
        df1 = pd.DataFrame()

    try:
        df2 = pd.read_csv(file2)
    except FileNotFoundError:
        df2 = pd.DataFrame()

    # Kết hợp dữ liệu nếu ít nhất 1 file tồn tại
    if not df1.empty and not df2.empty:
        df = pd.concat([df1, df2], ignore_index=True)
    elif not df1.empty:
        df = df1
    elif not df2.empty:
        df = df2
    else:
        return "<p style='color:red;'>⚠️ Không tìm thấy dữ liệu.</p>"

    # Kiểm tra cột 'Mã' có tồn tại không
    if "Mã" in df.columns:
        df = df[df["Mã"] == ticker].copy()
    else:
        return "<p style='color:red;'>⚠️ Không có cột 'Mã' trong dữ liệu.</p>"
    if df.empty:
        return "<p style='color:red;'>⚠️ Không có dữ liệu cho mã này.</p>"
    df.drop(columns=['Mã'], errors='ignore', inplace=True)
    categories = {
        "Nhóm chỉ số định giá": ["P/E", "P/B", "P/S", "P/Cash Flow", "EPS (VND)", "BVPS (VND)", "EV/EBITDA"],
        "Nhóm chỉ tiêu khả năng sinh lời": ["Biên EBIT (%)", "Biên lợi nhuận ròng (%)", "Biên lợi nhuận gộp (%)",
                                            "ROE (%)", "ROA (%)", "ROIC (%)"],
        "Nhóm chỉ số thanh toán": ["Chỉ số thanh toán hiện thời", "Chỉ số thanh toán tiền mặt",
                                   "Chỉ số thanh toán nhanh", "Khả năng chi trả lãi vay", "Đòn bẩy tài chính"],
        "Nhóm hiệu suất hoạt động": ["Vòng quay tài sản", "Vòng quay TSCĐ", "Số ngày thu tiền bình quân",
                                     "Số ngày tồn kho bình quân", "Số ngày thanh toán bình quân", "Chu kỳ tiền"]
    }

    df['Nhóm'] = df['Chỉ số'].apply(
        lambda x: next((cat for cat, keys in categories.items() if x in keys), None))

    df = df[df['Nhóm'].notna()]
    df.rename(columns={col: int(col) for col in df.columns if isinstance(col, float) and col.is_integer()},
              inplace=True)

    for col in df.columns:
        if isinstance(col, int):  # là cột năm
            df[col] = df.apply(
                lambda row: f"{row[col]:.2f}%" if row['Nhóm'] == "Nhóm chỉ tiêu khả năng sinh lời" and pd.notna(
                    row[col]) else row[col],
                axis=1
            )
    index_order = {name: idx for group in categories.values() for idx, name in enumerate(group)}

    # Các đoạn giải thích riêng theo nhóm
    explanation_profitability = """
    <div class='explanation' style="color:#666666;">
      <ul>
        <li><strong>Biên EBIT (%)</strong>: EBIT (Lợi nhuận trước lãi vay và thuế) / Doanh thu thuần × 100%</li>
        <li><strong>Biên lợi nhuận ròng (%)</strong>: Lợi nhuận sau thuế / Doanh thu thuần × 100%</li>
        <li><strong>Biên lợi nhuận gộp (%)</strong>: Lợi nhuận gộp / Doanh thu thuần × 100%</li>
        <li><strong>ROE (%)</strong>: Lợi nhuận sau thuế / Tổng vốn chủ sở hữu bình quân × 100%</li>
        <li><strong>ROA (%)</strong>: NOI / Tổng tài sản bình quân × 100%</li>
        <li><strong>ROIC (%)</strong>: NOPAT / Vốn đầu tư bình quân × 100%</li>
      </ul>
    </div>
    """

    explanation_liquidity = """
    <div class='explanation' style="color:#666666;">
      <ul>
        <li><strong>Chỉ số thanh toán hiện thời</strong>: Tài sản ngắn hạn / Nợ ngắn hạn</li>
        <li><strong>Chỉ số thanh toán nhanh</strong>: (Tài sản ngắn hạn − Hàng tồn kho) / Nợ ngắn hạn</li>
        <li><strong>Chỉ số thanh toán tiền mặt</strong>: Tiền và tương đương tiền / Nợ ngắn hạn</li>
        <li><strong>Khả năng chi trả lãi vay</strong>: EBIT / Chi phí lãi vay</li>
        <li><strong>Đòn bẩy tài chính</strong>: Tổng tài sản / Vốn chủ sở hữu</li>
      </ul>
    </div>
    """

    explanation_efficiency = """
    <div class='explanation' style="color:#666666;">
      <ul>
        <li><strong>Vòng quay tài sản</strong>: Doanh thu thuần / Tổng tài sản bình quân</li>
        <li><strong>Vòng quay TSCĐ</strong>: Doanh thu thuần / TSCĐ bình quân</li>
        <li><strong>Số ngày thu tiền bình quân</strong>: Khoản phải thu trung bình / Doanh thu trung bình ngày</li>
        <li><strong>Số ngày tồn kho bình quân</strong>: Tồn kho trung bình / Giá vốn trung bình ngày</li>
        <li><strong>Số ngày thanh toán bình quân</strong>: Khoản phải trả trung bình / Giá vốn trung bình ngày</li>
        <li><strong>Chu kỳ tiền</strong>: Số ngày thu tiền + Tồn kho − Thanh toán</li>
      </ul>
    </div>
    """

    html_sections = []
    for group_name, indicators in categories.items():
        group_df = df[df['Nhóm'] == group_name].drop(columns='Nhóm')

        group_df['sort_key'] = group_df['Chỉ số'].map(index_order)
        group_df.sort_values(by='sort_key', inplace=True)
        group_df.drop(columns='sort_key', inplace=True)

        for col in group_df.columns:
            if isinstance(col, int):
                group_df[col] = pd.to_numeric(group_df[col], errors='coerce')
                if group_name == "Nhóm chỉ tiêu khả năng sinh lời":
                    group_df[col] = group_df[col].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

        if group_df.empty:
            continue

        table_html = group_df.to_html(index=False, classes="financial-table", border=0, escape=False)
        soup = BeautifulSoup(table_html, 'html.parser')
        header = soup.new_tag('h4')
        header.string = group_name
        header['style'] = 'margin-top:20px;color:#004080;'

        section_html = str(header) + str(soup)
        # Gắn giải thích đúng vị trí
        if group_name == "Nhóm chỉ tiêu khả năng sinh lời":
            section_html += explanation_profitability
            chart_df = group_df.set_index("Chỉ số").T
            chart_df = chart_df.apply(pd.to_numeric, errors='coerce')
            fig, ax = plt.subplots(figsize=(10, 5))

            ax.plot(chart_df.index, chart_df['ROE (%)'], label='ROE', marker='s', color='#26C6DA')
            for i, val in enumerate(chart_df['ROE (%)']):
                ax.text(chart_df.index[i], val + 0.8, f"{val:.1f}", ha='center', fontsize=8, color='black')

            ax.plot(chart_df.index, chart_df['ROA (%)'], label='ROA', marker='o', color='#66BB6A')
            for i, val in enumerate(chart_df['ROA (%)']):
                ax.text(chart_df.index[i], val + 0.8, f"{val:.1f}", ha='center', fontsize=8, color='black')

            ax.plot(chart_df.index, chart_df['ROIC (%)'], label='ROIC', marker='^', color='#FFCCBC')
            for i, val in enumerate(chart_df['ROIC (%)']):
                ax.text(chart_df.index[i], val + 0.8, f"{val:.1f}", ha='center', fontsize=8, color='black')

            ax.set_ylabel('Phần trăm (%)')
            ax.set_title('CHỈ SỐ SINH LỜI', loc='left', fontweight='bold')
            ax.legend(loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.25))
            plt.tight_layout()

            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()

            chart_html = f"""
                    <div style="margin-top:20px;">
                        <img src="data:image/png;base64,{image_base64}" style="max-width:100%; border:1px solid #ccc; border-radius:6px;">
                    </div>
                """
            return_ratio_analysis = generate_return_ratio_analysis(ticker)

            chart_with_analysis = f"""
                    <!-- Biểu đồ chỉ số sinh lời -->
                    <div style='margin-bottom: 10px;'>
                      {chart_html}
                    </div>
                    
                    <!-- Nhận xét chỉ số sinh lời -->
                    <div style='background: #f5f9fe; padding: 14px 18px; border-radius: 8px;
                                font-size: 14px; line-height: 1.6; color: #333; font-family: Arial, sans-serif; margin-bottom: 20px;'>
                      {return_ratio_analysis}
                    </div>
                    """
            section_html += chart_with_analysis
        elif group_name == "Nhóm chỉ số thanh toán":
            section_html += explanation_liquidity
        elif group_name == "Nhóm hiệu suất hoạt động":
            section_html += explanation_efficiency
        if group_name == "Nhóm hiệu suất hoạt động":
            chart_df = group_df.set_index("Chỉ số").T
            chart_df = chart_df.apply(pd.to_numeric, errors='coerce')

            plt.style.use('default')  # dùng nền trắng giống hình
            fig, ax = plt.subplots(figsize=(10, 5))

            ax.bar(chart_df.index, chart_df["Chu kỳ tiền"], label="Chu kỳ tiền", color='#1f78b4')

            ax.plot(chart_df.index, chart_df["Số ngày thu tiền bình quân"], label="Số ngày phải thu", marker='o', color='#9c27b0')
            for i, val in enumerate(chart_df["Số ngày thu tiền bình quân"]):
                ax.text(chart_df.index[i], val + 1, f"{val:.1f}", ha='center', fontsize=8, color='black')

            ax.plot(chart_df.index, chart_df["Số ngày tồn kho bình quân"], label="Số ngày xử lý HTK", marker='s', color='orange')
            for i, val in enumerate(chart_df["Số ngày tồn kho bình quân"]):
                ax.text(chart_df.index[i], val + 1, f"{val:.1f}", ha='center', fontsize=8, color='black')
            ax.plot(chart_df.index, chart_df["Số ngày thanh toán bình quân"], label="Số ngày phải trả", marker='^',
                    color='green')
            for i, val in enumerate(chart_df["Số ngày thanh toán bình quân"]):
                ax.text(chart_df.index[i], val + 1, f"{val:.1f}", ha='center', fontsize=8, color='black')
            ax.set_ylabel("Số ngày")
            ax.set_xlabel("Năm")
            ax.set_title('CHỈ SỐ HOẠT ĐỘNG', loc='left', fontweight='bold')
            ax.legend(loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.25))
            plt.tight_layout()

            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            chart_html = f"""
                            <div style="margin-top:20px;">
                                <img src="data:image/png;base64,{image_base64}" style="max-width:100%; border:1px solid #ccc; border-radius:6px;">
                            </div>
                            """

            activity_combo_html = f"""
            <!-- Biểu đồ hoạt động -->
            <div style='margin-bottom: 10px;'>
              {chart_html}
            </div>

            <!-- Nhận xét hoạt động -->
            <div style='background: #f5f9fe; padding: 14px 18px; border-radius: 8px;
                        font-size: 14px; line-height: 1.6; color: #333; font-family: Arial, sans-serif; margin-bottom: 20px;'>
              {generate_activity_analysis(ticker)}
            </div>
            """
            section_html += activity_combo_html
        html_sections.append(section_html)
    # === Dupont biểu đồ ===
    dupont_df = df[df['Chỉ số'].isin(['ROE (%)', 'Biên lợi nhuận ròng (%)', 'Đòn bẩy tài chính', 'Vòng quay tài sản'])].copy()
    dupont_df = dupont_df.set_index('Chỉ số').T
    dupont_df = dupont_df[dupont_df.index.to_series().apply(lambda x: str(x).isdigit())]
    dupont_df = dupont_df.apply(lambda col: col.map(lambda x: float(str(x).replace('%', '')) if pd.notna(x) else None))

    years = dupont_df.index.astype(int)
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Trục bên trái: ROE và Biên lợi nhuận ròng (%)
    bar1 = ax1.bar(years, dupont_df['ROE (%)'], color='#fb9a99', label='ROE')
    line1, = ax1.plot(years, dupont_df['Biên lợi nhuận ròng (%)'], color='#FF8A65', marker='s', label='Biên LN ròng')

    for i, year in enumerate(years):
        val = dupont_df['Biên lợi nhuận ròng (%)'].iloc[i]
        if pd.notna(val):
            ax1.text(year, val + 0.5, f"{val:.1f}", ha='center', fontsize=8)

    # Trục bên phải: Đòn bẩy tài chính và Vòng quay tài sản (lần)
    ax2 = ax1.twinx()
    line2, = ax2.plot(years, dupont_df['Đòn bẩy tài chính'], color='#B39DDB', marker='o', label='Đòn bẩy tài chính')
    line3, = ax2.plot(years, dupont_df['Vòng quay tài sản'], color='#4DB6AC', marker='^', label='Vòng quay TTS TTM')

    for i, year in enumerate(years):
        for col, offset in zip(['Đòn bẩy tài chính', 'Vòng quay tài sản'], [0.2, 0.2]):
            val = dupont_df[col].iloc[i]
            if pd.notna(val):
                ax2.text(year, val + offset, f"{val:.2f}", ha='center', fontsize=8)

    # Thiết lập trục và tiêu đề
    ax1.set_ylabel('Phần trăm (%)')
    ax2.set_ylabel('Lần')
    ax1.set_title('DUPONT', loc='left', fontweight='bold')

    # Gộp chú thích từ cả hai trục
    lines, labels = [], []
    for ax in [ax1, ax2]:
        l, lab = ax.get_legend_handles_labels()
        lines.extend(l)
        labels.extend(lab)

    fig.legend(lines, labels, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.05), frameon=True,
    fancybox=True, fontsize=9)

    # Xuất ra ảnh
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    img_b64 = base64.b64encode(buffer.read()).decode()
    plt.close()
    chart_html2 = f"""
        <div style="margin-top:20px;">
            <img src="data:image/png;base64,{img_b64}" style="max-width:100%; border:1px solid #ccc; border-radius:6px;">
        </div>
        """
    dupont_profit_combo_html = f"""
    <!-- Biểu đồ Dupont -->
    <div style='margin-bottom: 10px;'>
      {chart_html2}
    </div>

    <!-- Nhận xét Dupont -->
    <div style='background: #f5f9fe; padding: 14px 18px; border-radius: 8px;
                font-size: 14px; line-height: 1.6; color: #333; font-family: Arial, sans-serif; margin-bottom: 20px;'>
      {generate_dupont_analysis(ticker)}
    </div>
    """
    html_sections.append("<h4 style='margin-top:20px;color:#004080;'>CÁC BIỂU ĐỒ TỔNG HỢP</h4>")
    html_sections.append(dupont_profit_combo_html)
    # === Biểu đồ lợi nhuận ===
    kqkd_file = r"D:\Python Project\10_diem - Copy\data\financial\KQKD.csv"
    try:
        kqkd_all = pd.read_csv(kqkd_file)
        kqkd_all = kqkd_all[kqkd_all['Mã'] == ticker]
    except:
        kqkd_all = pd.DataFrame()

    profit_df = df[df['Chỉ số'].isin(['Biên EBIT (%)', 'Biên lợi nhuận ròng (%)', 'Biên lợi nhuận gộp (%)'])].copy()
    profit_df = profit_df.set_index('Chỉ số').T
    profit_df = profit_df[profit_df.index.to_series().apply(lambda x: str(x).isdigit())]
    profit_df = profit_df.apply(lambda col: col.map(lambda x: float(str(x).replace('%', '')) if pd.notna(x) else None))

    if not kqkd_all.empty and 'Năm' in kqkd_all.columns and 'Lợi nhuận sau thuế thu nhập doanh nghiệp' in kqkd_all.columns:
        kqkd_all = kqkd_all.set_index('Năm')
        # Gán khớp theo index (năm)
        profit_df = profit_df.copy()
        for year in profit_df.index:
            if int(year) in kqkd_all.index:
                val = kqkd_all.loc[int(year), 'Lợi nhuận sau thuế thu nhập doanh nghiệp']
                try:
                    profit_df.loc[year, 'Lợi nhuận ròng'] = float(val) / 1e9
                except:
                    profit_df.loc[year, 'Lợi nhuận ròng'] = None
    if 'Lợi nhuận ròng' in profit_df.columns:
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.bar(profit_df.index, profit_df['Lợi nhuận ròng'], color='#90CAF9', label='Lợi nhuận ròng')
        ax2 = ax1.twinx()
        ax2.plot(profit_df.index, profit_df['Biên lợi nhuận gộp (%)'], color='green', marker='s', label='Biên LN gộp')
        for i, val in enumerate(profit_df['Biên lợi nhuận gộp (%)']):
            ax2.text(profit_df.index[i], val + 1, f"{val:.1f}", ha='center', fontsize=8, color='black')
        ax2.plot(profit_df.index, profit_df['Biên EBIT (%)'], color='#FFCC80', marker='o', label='Biên EBIT')
        for i, val in enumerate(profit_df['Biên EBIT (%)']):
            ax2.text(profit_df.index[i], val + 1, f"{val:.1f}", ha='center', fontsize=8, color='black')
        ax2.plot(profit_df.index, profit_df['Biên lợi nhuận ròng (%)'], color='#fb9a99', marker='^',
                 label='Biên LN ròng')
        for i, val in enumerate(profit_df['Biên lợi nhuận ròng (%)']):
            ax2.text(profit_df.index[i], val + 1, f"{val:.1f}", ha='center', fontsize=8, color='black')

        ax1.set_ylabel('Lãi thuần (Tỷ VND)')
        ax2.set_ylabel('Biên lãi thuần (%)')
        ax1.set_title('LỢI NHUẬN', loc='left', fontweight='bold')
        lines_labels = [ax.get_legend_handles_labels() for ax in [ax1, ax2]]
        lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        fig.legend(lines, labels, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.05))

        buffer = BytesIO()
        plt.savefig(buffer, format='png',bbox_inches='tight')
        buffer.seek(0)
        profit_b64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        chart_html3 = f"""
            <div style="margin-top:20px;">
                <img src="data:image/png;base64,{profit_b64}" style="max-width:100%; border:1px solid #ccc; border-radius:6px;">
            </div>
            """
        profit_combo_html = f"""
        <!-- Biểu đồ lợi nhuận -->
        <div style='margin-bottom: 10px;'>
          {chart_html3}
        </div>
        <!-- Nhận xét lợi nhuận -->
        <div style='background: #f5f9fe; padding: 14px 18px; border-radius: 8px;
                    font-size: 14px; line-height: 1.6; color: #333; font-family: Arial, sans-serif; margin-bottom: 20px;'>
          {generate_profit_analysis(ticker)}
        </div>
        """
        html_sections.append(profit_combo_html)
    return "<br>".join(html_sections)
def load_merged_financial_ratios(ticker: str) -> pd.DataFrame:
    path1 = r"D:\Python Project\10_diem - Copy\data\financial\financial_ratios.csv"
    path2 = fr"D:\Python Project\10_diem - Copy\data\calculate\{ticker}_financial_ratios.csv"

    try:
        df1 = pd.read_csv(path1)
    except:
        df1 = pd.DataFrame()

    try:
        df2 = pd.read_csv(path2)
    except:
        df2 = pd.DataFrame()

    if not df1.empty and not df2.empty:
        return pd.concat([df1, df2], ignore_index=True)
    elif not df1.empty:
        return df1
    elif not df2.empty:
        return df2
    else:
        return pd.DataFrame()
def generate_industry_comparison_html(ticker: str, year: int) -> str:
    year = str(year)
    prev_year = str(int(year) - 1)

    ratios_all = load_merged_financial_ratios(ticker)

    try:
        kqkd_all = pd.read_csv(r"D:\Python Project\10_diem - Copy\data\financial\KQKD.csv")
        bcdkt_all = pd.read_csv(r"D:\Python Project\10_diem - Copy\data\financial\BCDKT.csv")
        nganh_df = pd.read_csv(r"D:\Python Project\10_diem - Copy\data\financial\Nganh.csv")
    except FileNotFoundError:
        return "<p style='color:red;'>⚠️ Không tìm thấy đủ dữ liệu cần thiết.</p>"

    sector_row = kqkd_all[kqkd_all["Mã"] == ticker]
    if sector_row.empty or "Ngành ICB - cấp 3" not in sector_row.columns:
        return "<p style='color:red;'>⚠️ Không tìm thấy thông tin ngành của mã cổ phiếu.</p>"

    icb_sector = sector_row["Ngành ICB - cấp 3"].dropna().values[0]

    ratio_map = {
        "ROE (%)": None,
        "ROA (%)": None,
        "ROIC (%)": None,
        "Biên EBIT (%)": None,
        "Biên lợi nhuận gộp (%)": None,
        "Biên lợi nhuận ròng (%)": None,
        "Tăng trưởng lợi nhuận (%)": None,
        "Tăng trưởng doanh thu (%)": None,
        "Chỉ số thanh toán hiện thời": None,
        "Chỉ số thanh toán nhanh": None,
        "(Vay NH + DH)/VCSH": None,
        "Nợ/VCSH": None,
        "Vòng quay tài sản": None,
    }

    df_ratios = ratios_all[ratios_all["Mã"] == ticker]
    for key in ratio_map:
        if key in ["Tăng trưởng lợi nhuận (%)", "Tăng trưởng doanh thu (%)", "(Vay NH + DH)/VCSH", "Nợ/VCSH"]:
            continue
        col_key = "Vòng quay tài sản" if key == "Vòng quay tài sản" else key
        val = df_ratios[df_ratios["Chỉ số"] == col_key][year]
        if not val.empty:
            ratio_map[key] = float(val.values[0]) if pd.notna(val.values[0]) else None
    kqkd_firm = kqkd_all[(kqkd_all["Mã"] == ticker)]
    for col, label in [("Cổ đông của Công ty mẹ", "Tăng trưởng lợi nhuận (%)"),
                       ("Doanh thu thuần", "Tăng trưởng doanh thu (%)")]:
        df = kqkd_firm.pivot(index="Năm", columns="Mã", values=col)
        try:
            v_this = df.loc[int(year), ticker]
            v_last = df.loc[int(prev_year), ticker]
            if pd.notna(v_this) and pd.notna(v_last) and v_last != 0:
                ratio_map[label] = (v_this - v_last) / v_last * 100
        except:
            ratio_map[label] = None

    bcdkt_firm = bcdkt_all[(bcdkt_all["Mã"] == ticker) & (bcdkt_all["Năm"] == int(year))]
    if not bcdkt_firm.empty:
        row = bcdkt_firm.iloc[0]
        try:
            vcs = row["VỐN CHỦ SỞ HỮU"]
            if vcs != 0 and pd.notna(vcs):
                no = row["NỢ PHẢI TRẢ"]
                vayngan = row["Vay và nợ thuê tài chính ngắn hạn"]
                vaydai = row["Vay và nợ thuê tài chính dài hạn"]
                ratio_map["Nợ/VCSH"] = no / vcs
                ratio_map["(Vay NH + DH)/VCSH"] = (vayngan + vaydai) / vcs
        except:
            pass

    rows = []
    percent_keywords = ["%", "tăng trưởng", "Biên"]
    for key, val in ratio_map.items():
        industry_key = "Quay vòng tài sản" if key == "Vòng quay tài sản" else key
        nganh_val = nganh_df[(nganh_df["Ngành"] == icb_sector) & (nganh_df["Chỉ số"] == industry_key)][year]
        industry_val = float(nganh_val.values[0]) if not nganh_val.empty and pd.notna(nganh_val.values[0]) else None
        if industry_val is not None and any(kw in key for kw in percent_keywords):
            industry_val *= 100
        if val is None or industry_val is None:
            dg = "Không đủ dữ liệu"
            color = "#999"
        else:
            # Chỉ so sánh và đánh giá cho các chỉ số KHÔNG phải Nợ/VCSH hoặc (Vay NH+DH)/VCSH
            if key in ["Nợ/VCSH", "(Vay NH + DH)/VCSH"]:
                dg = "Không đủ dữ liệu để đánh giá"
                color = "#999"
            else:
                good = val >= industry_val
                dg = "Tốt" if good else "Cần cải thiện"
                color = "green" if good else "red"

        rows.append({
            "Chỉ số": key,
            ticker: f"{val:.2f}" if val is not None else "-",
            "Trung bình ngành": f"{industry_val:.2f}" if industry_val is not None else "-",
            "Đánh giá": f"<span style='color:{color}; font-weight:bold'>{dg}</span>"
        })

    df_result = pd.DataFrame(rows)
    df_result = df_result[["Chỉ số", ticker, "Trung bình ngành", "Đánh giá"]]

    html_table = df_result.to_html(index=False, escape=False, classes="financial-table", border=0)
    soup = BeautifulSoup(html_table, "html.parser")
    for tr in soup.find("tbody").find_all("tr"):
        tds = tr.find_all("td")
        if tds:
            tds[0]["class"] = "label-cell"
    note = f"""
    <div style="font-size:13px; color:#666; margin-bottom:4px;">So sánh dữ liệu tài chính năm {year}.</div>
    <div style="font-size:13px; color:#666; margin-bottom:8px;">Dữ liệu ngành theo chuẩn phân ngành cấp 3 ICB.</div>
    """
    brief_lines = [
        f"- {row['Chỉ số']}: {ticker} đạt {row[ticker]} so với TB ngành {row['Trung bình ngành']} → {BeautifulSoup(row['Đánh giá'], 'html.parser').text}"
        for _, row in df_result.iterrows()
        if 'Không đủ dữ liệu' not in row['Đánh giá']
    ]

    from ai_analyzer import call_gemini, wrap_brief

    prompt = f"""
    Bạn là chuyên gia tài chính. Hãy viết một đoạn phân tích (150-200 từ) về mức độ hiệu quả tài chính của công ty {ticker.upper()} so với trung bình ngành trong năm {year}, dựa trên các điểm sau:
    {chr(10).join(brief_lines)}
    Sinh lời: "ROE (%)", "ROA (%)", "ROIC (%)","Biên EBIT (%)","Biên lợi nhuận gộp (%)","Biên lợi nhuận ròng (%)"
    Tăng trưởng: Tăng trưởng lợi nhuận (%)","Tăng trưởng doanh thu (%)
    Thanh khoản: Chỉ số thanh toán hiện thời",Chỉ số thanh toán nhanh
    Đòn bẩy: (Vay NH + DH)/VCSH","Nợ/VCSH
    Hiệu quả hoạt động: Vòng quay tài sản
    Yêu cầu:
    - Trình bày thành các đoạn nhỏ rõ ràng, mỗi đoạn nên nói về 1 nhóm chỉ số như: Sinh lời, Tăng trưởng, Thanh khoản, Đòn bẩy, Hiệu quả hoạt động
    - Viết xuống dòng rõ ràng từng đoạn như báo cáo chuyên nghiệp
    - Văn phong chuyên nghiệp, không dùng kiểu nói chuyện, không cảm thán
    - Mở đầu phân tích bằng các đoạn phân tích từng nhóm luôn rồi tóm lại.
    - Không viết lại tên chỉ số từng dòng (vì đã liệt kê ở trên), chỉ phân tích theo nhóm
    """

    ai_comment = call_gemini(prompt)

    return note + str(soup) + wrap_brief("Nhận xét tổng hợp so với ngành", ai_comment)

