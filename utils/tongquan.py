# tongquan.py
from vnstock import Vnstock
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import base64
from io import BytesIO
def export_tongquan_to_csv(ticker):
    try:
        print(f"Đang lấy dữ liệu tổng quan tài chính cho mã: {ticker}")
        stock = Vnstock().stock(symbol=ticker, source='VCI')
        df = stock.finance.ratio(period='year', lang='vi')

        if df is None or df.empty:
            print(f"⚠️ Không có dữ liệu tài chính tổng quan cho mã {ticker}.")
            return None

        # Đảm bảo thư mục tồn tại
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports'))
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"{ticker}_tongquan.csv")
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ Đã lưu dữ liệu vào: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Lỗi khi lấy dữ liệu tổng quan: {e}")
        return None


# tongquan.py


def generate_industry_analysis_html(
    ticker,
    path_kqkd="D:/Python Project/10_diem - Copy/data/financial/KQKD.csv",
    path_nganh="D:/Python Project/10_diem - Copy/data/financial/Nganh.csv",
    path_merged="D:/Python Project/10_diem - Copy/data/technical/merged_marketcap.csv"
):
    # 1. Load dữ liệu
    merged_df = pd.read_csv(path_merged)
    df_kqkd = pd.read_csv(path_kqkd)
    df_nganh = pd.read_csv(path_nganh)

    merged_df["Sector"] = merged_df["Sector"].astype(str)
    df_kqkd["Mã"] = df_kqkd["Mã"].str.strip()

    # 2. Lấy ngành ICB từ KQKD
    matched_row = df_kqkd[df_kqkd["Mã"] == ticker]
    if matched_row.empty:
        return f"<p>⚠️ Không tìm thấy mã {ticker} trong KQKD.csv để xác định ngành.</p>"
    icb_sector = matched_row.iloc[0]["Ngành ICB - cấp 3"]

    # 3. Tổng hợp vốn hóa theo ngày cuối
    date_columns = merged_df.columns[2:-1]
    merged_df[date_columns] = merged_df[date_columns].apply(pd.to_numeric, errors="coerce")
    last_date = pd.to_datetime(date_columns[-1]).strftime("%d/%m/%Y")
    latest_values = merged_df.groupby("Sector")[date_columns[-1]].sum().sort_values(ascending=False)
    top_sectors = latest_values.head(5).index.tolist()

    # 4. Vẽ biểu đồ vốn hóa top 5 ngành
    sector_marketcap_T = merged_df.groupby("Sector")[date_columns].sum().T
    sector_marketcap_T.index = pd.to_datetime(sector_marketcap_T.index)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    for sector in top_sectors:
        ax.plot(sector_marketcap_T.index, sector_marketcap_T[sector], label=sector,
                linewidth=2 if sector == icb_sector else 1.5)

    ax.set_title(f"Vốn hóa theo ngành - Top 5 (Dữ liệu đến {last_date})", fontsize=13, weight="bold")
    ax.set_xlabel("Thời gian")
    ax.set_ylabel("Vốn hóa (VNĐ)")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x / 1e9:.1f}B"))
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    plt.tight_layout()

    # Encode biểu đồ thành base64
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode("utf-8")

    # 5. Tạo bảng xếp hạng ngành (dữ liệu ngày cuối)
    ranking = latest_values.reset_index()
    ranking = ranking[~ranking["Sector"].isin(["nan", "NaN", None, pd.NA])]
    ranking = ranking[ranking["Sector"].notna()]
    ranking.columns = ["Ngành", "Tổng vốn hóa (Tỷ VND)"]
    ranking["Tổng vốn hóa (Tỷ VND)"] = ranking["Tổng vốn hóa (Tỷ VND)"] / 1e9
    ranking["Tổng vốn hóa (Tỷ VND)"] = ranking["Tổng vốn hóa (Tỷ VND)"].round(2)
    ranking["Thứ hạng"] = ranking.index + 1
    rank_row = ranking[ranking["Ngành"] == icb_sector]

    rank_text = ""
    if not rank_row.empty:
        rank_number = int(rank_row["Thứ hạng"].values[0])
        rank_text = f"<p>Ngành <strong>\"{icb_sector}\"</strong> hiện đang xếp <strong>hạng {rank_number}</strong> về vốn hóa toàn thị trường (dữ liệu đến {last_date}).</p>"


    table_html = ranking.head(10).to_html(index=False, classes="financial-table", border=0)

    stock_data = merged_df[merged_df["Code"] == ticker]
    stock_data_line = stock_data.iloc[:, 2:-1].T
    stock_data_line.index = pd.to_datetime(stock_data_line.index)

    fig2, ax2 = plt.subplots(figsize=(10, 4.5))
    ax2.plot(stock_data_line, label=ticker)
    ax2.set_title(f"Vốn hóa thị trường {ticker} - (Dữ liệu đến {last_date})")
    ax2.set_xlabel("Thời gian")
    ax2.set_ylabel("Giá trị vốn hóa (Triệu VNĐ)")
    ax2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x / 1e6:.0f}M"))
    ax2.grid(True)
    ax2.legend()
    plt.tight_layout()

    buf2 = BytesIO()
    fig2.savefig(buf2, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig2)
    buf2.seek(0)
    chart_ticker = base64.b64encode(buf2.read()).decode("utf-8")

    html_output = f"""
        <div><strong>Tổng quan thị trường: {icb_sector}</strong></div>
        <img src="data:image/png;base64,{chart_base64}" style="max-width:100%; margin-bottom:10px;" />
        {rank_text}
        <p>Dưới đây là top 10 ngành có vốn hóa cao nhất tính đến ngày {last_date}:</p>
        {table_html}
        <div class="section-subtitle">Vốn hóa mã cổ phiếu <strong>{ticker}</strong></div>
    <img src="data:image/png;base64,{chart_ticker}" style="max-width:100%; margin-top:10px;" />
    """
    return html_output
def generate_vonhoa_piecharts_html(
    ticker,
    path_tongquan="D:/Python Project/10_diem - Copy/reports",
    path_nganh="D:/Python Project/10_diem - Copy/data/financial/Nganh.csv",
    path_kqkd="D:/Python Project/10_diem - Copy/data/financial/KQKD.csv"
):
    try:
        # Load dữ liệu
        df_ticker = pd.read_csv(f"{path_tongquan}/{ticker}_tongquan.csv", header=1)  # Bỏ dòng "Meta"
        df_nganh = pd.read_csv(path_nganh)
        df_kqkd = pd.read_csv(path_kqkd)
        df_kqkd["Mã"] = df_kqkd["Mã"].str.strip()

        # Lấy ngành từ KQKD
        matched = df_kqkd[df_kqkd["Mã"] == ticker]
        if matched.empty:
            return f"<p>⚠️ Không tìm thấy mã {ticker} trong KQKD.csv.</p>"
        sector = matched.iloc[0]["Ngành ICB - cấp 3"]

        # Lọc dữ liệu 'Vốn hóa' của ngành
        df_sector_vh = df_nganh[(df_nganh["Ngành"] == sector) & (df_nganh["Chỉ số"].str.lower() == "vốn hóa")]
        if df_sector_vh.empty:
            return f"<p>⚠️ Không có dữ liệu 'Vốn hóa' cho ngành {sector}.</p>"

        # Lấy các năm giao nhau
        years_ticker = df_ticker["Năm"].astype(str).unique().tolist()
        years_sector = [col for col in df_sector_vh.columns[2:] if col.isnumeric()]
        available_years = sorted([y for y in ["2021", "2022", "2023", "2024"] if y in years_ticker and y in years_sector])

        if not available_years:
            return "<p>⚠️ Không có năm nào trùng nhau giữa hai bảng dữ liệu để vẽ biểu đồ.</p>"

        # Chọn cột vốn hóa gần đúng tên nhất (ưu tiên đúng nếu bạn biết)
        vh_col = [col for col in df_ticker.columns if "vốn hóa" in col.lower()]
        if not vh_col:
            return f"<p>⚠️ Không tìm thấy cột nào chứa 'Vốn hóa' trong file của {ticker}.</p>"
        vh_col = vh_col[0]

        # Vẽ pie chart
        fig, axs = plt.subplots(1, 4, figsize=(16, 4))
        table_data = []
        for i, year in enumerate(available_years[:4]):
            try:
                ticker_value = df_ticker[df_ticker["Năm"] == int(year)][vh_col].values[0]
                sector_total = df_sector_vh[year].values[0]
                percent = round(100 * ticker_value / sector_total, 1)
                axs[i].pie(
                    [ticker_value, sector_total - ticker_value],
                    labels=[f"{ticker}", "Phần còn lại"],
                    autopct="%.1f%%",
                    startangle=90,
                    colors=["#007ACC", "#A0C4FF"]
                )
                axs[i].set_title(f"Năm {year}", fontsize=10)
                table_data.append({
                    "Năm": year,
                    f"Vốn hóa {ticker} (tỷ)": f"{round(ticker_value / 1e9, 2):,.2f}",
                    "Vốn hóa ngành (tỷ)": f"{round(sector_total / 1e9, 2):,.2f}",
                    "Tỷ lệ (%)": f"{percent:.1f}"
                })
            except Exception:
                axs[i].axis("off")

        plt.tight_layout()

        # Encode biểu đồ thành base64
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
        buf.seek(0)
        chart_base64 = base64.b64encode(buf.read()).decode("utf-8")
        df_table = pd.DataFrame(table_data)
        df_table_html = df_table.to_html(index=False, classes="financial-table", border=0)

        html_output = f"""
        <div class=\"section-subtitle\">Tỷ trọng vốn hóa của <strong>{ticker}</strong> trong tổng vốn hóa ngành <strong>{sector}</strong> theo từng năm:</div>
        <img src=\"data:image/png;base64,{chart_base64}\" style=\"max-width:100%; margin-top:10px;\" />
        <p>Dưới đây là bảng số liệu tương ứng:</p>
        {df_table_html}
        """
        return html_output


    except Exception as e:
        return f"<p>❌ Lỗi khi tạo biểu đồ vốn hóa pie chart: {e}</p>"
# Re-integrate full HTML output + original paths and fix plotting issues
def generate_valuation_analysis_html(
    ticker,
    path_tongquan="D:/Python Project/10_diem - Copy/reports",
    path_nganh="D:/Python Project/10_diem - Copy/data/financial/Nganh.csv",
    path_kqkd="D:/Python Project/10_diem - Copy/data/financial/KQKD.csv"
):
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        import base64
        from io import BytesIO

        # Load dữ liệu
        df_ticker = pd.read_csv(f"{path_tongquan}/{ticker}_tongquan.csv", header=1)
        df_nganh = pd.read_csv(path_nganh)
        df_kqkd = pd.read_csv(path_kqkd)
        df_kqkd["Mã"] = df_kqkd["Mã"].str.strip()

        df_ticker["Năm"] = df_ticker["Năm"].astype(str)
        df_nganh.columns = [col.strip() for col in df_nganh.columns]
        df_ticker.rename(columns={"Số CP lưu hành (Triệu CP)": "Số CP lưu hành"}, inplace=True)

        matched = df_kqkd[df_kqkd["Mã"] == ticker]
        if matched.empty:
            return f"<p>⚠️ Không tìm thấy mã {ticker} trong KQKD.csv.</p>"
        sector = matched.iloc[0]["Ngành ICB - cấp 3"]

        # Tạo bảng so sánh 2024
        metrics = ["EPS (VND)", "P/E", "P/B", "P/S", "P/Cash Flow", "Số CP lưu hành", "EV/EBITDA", "BVPS (VND)"]
        result_rows = []
        for metric in metrics:
            ticker_row = df_ticker[df_ticker["Năm"] == "2024"]
            ticker_value = float(ticker_row[metric].values[0]) if not ticker_row.empty and metric in df_ticker.columns else None
            nganh_row = df_nganh[
                (df_nganh["Chỉ số"].str.strip() == metric.strip()) &
                (df_nganh["Ngành"].str.strip() == sector.strip())
            ]
            sector_value = float(nganh_row["2024"].values[0]) if not nganh_row.empty else None
            formatted_ticker = f"{ticker_value:,.2f}" if ticker_value is not None else "-"
            formatted_sector = f"{sector_value:,.2f}" if sector_value is not None else "-"
            result_rows.append({"Chỉ số": metric, ticker: formatted_ticker, "Trung bình ngành": formatted_sector})

        df_compare = pd.DataFrame(result_rows)
        compare_html = df_compare.to_html(index=False, classes="financial-table", border=0)

        valid_years = ["2021", "2022", "2023", "2024"]
        valid_years_int = [int(y) for y in valid_years]

        # Chart 1: P/E, P/B, P/S, P/Cash Flow
        fig1, axs = plt.subplots(2, 2, figsize=(14, 8))
        for ax, metric in zip(axs.flat, ["P/E", "P/B", "P/S", "P/Cash Flow"]):
            if metric in df_ticker.columns:
                df_plot = df_ticker[df_ticker["Năm"].isin(valid_years)][["Năm", metric]].dropna()
                df_plot["Năm"] = df_plot["Năm"].astype(int)
                df_plot[metric] = df_plot[metric].astype(float)
                ax.plot(df_plot["Năm"], df_plot[metric], marker="o", label=ticker)
                for x, y in zip(df_plot["Năm"], df_plot[metric]):
                    ax.text(x, y, f"{y:,.0f}", fontsize=8, ha='center', va='bottom')

            nganh_row = df_nganh[
                (df_nganh["Chỉ số"].str.strip() == metric.strip()) &
                (df_nganh["Ngành"].str.strip() == sector.strip())
            ]
            if not nganh_row.empty:
                nganh_values = nganh_row.iloc[0][valid_years].astype(float)
                ax.plot(valid_years_int, nganh_values, marker="x", label="Ngành")
                for x, y in zip(valid_years_int, nganh_values):
                    ax.text(x, y, f"{y:,.0f}", fontsize=8, ha='center', va='bottom')

            ax.set_title(metric)
            ax.set_xticks(valid_years_int)
            ax.set_xticklabels(valid_years)
            ax.grid(True)
            ax.legend()
        fig1.tight_layout()
        buf1 = BytesIO()
        fig1.savefig(buf1, format="png", dpi=100, bbox_inches="tight")
        chart1 = base64.b64encode(buf1.getvalue()).decode("utf-8")
        plt.close(fig1)

        # Chart 2: EPS và BVPS tách 2 subplot ngang hàng
        fig2, (ax_eps, ax_bvps) = plt.subplots(1, 2, figsize=(14, 4))
        for ax, metric, color in zip([ax_eps, ax_bvps], ["EPS (VND)", "BVPS (VND)"], ["blue", "green"]):
            if metric in df_ticker.columns:
                df_plot = df_ticker[df_ticker["Năm"].isin(valid_years)][["Năm", metric]].dropna()
                df_plot["Năm"] = df_plot["Năm"].astype(int)
                df_plot[metric] = df_plot[metric].astype(float)
                ax.plot(df_plot["Năm"], df_plot[metric], marker="o", label=ticker, color=color)
                for x, y in zip(df_plot["Năm"], df_plot[metric]):
                    ax.text(x, y, f"{y:,.0f}", fontsize=8, ha='center', va='bottom')

            nganh_row = df_nganh[
                (df_nganh["Chỉ số"].str.strip() == metric.strip()) &
                (df_nganh["Ngành"].str.strip() == sector.strip())
            ]
            if not nganh_row.empty:
                nganh_values = nganh_row.iloc[0][valid_years].astype(float)
                ax.plot(valid_years_int, nganh_values, marker="x", linestyle="--", label="Ngành", color=color)
                for x, y in zip(valid_years_int, nganh_values):
                    ax.text(x, y, f"{y:,.0f}", fontsize=8, ha='center', va='bottom')

            ax.set_title(metric)
            ax.set_xticks(valid_years_int)
            ax.set_xticklabels(valid_years)
            ax.grid(True)
            ax.legend()
        fig2.tight_layout()
        buf2 = BytesIO()
        fig2.savefig(buf2, format="png", dpi=100, bbox_inches="tight")
        chart2 = base64.b64encode(buf2.getvalue()).decode("utf-8")
        plt.close(fig2)

        # Chart 3: EV/EBITDA riêng
        fig3, ax3 = plt.subplots(figsize=(8, 4))
        metric = "EV/EBITDA"
        if metric in df_ticker.columns:
            df_ev = df_ticker[df_ticker["Năm"].isin(valid_years)][["Năm", metric]].dropna()
            df_ev["Năm"] = df_ev["Năm"].astype(int)
            df_ev[metric] = df_ev[metric].astype(float)
            ax3.plot(df_ev["Năm"], df_ev[metric], marker="o", label=ticker)
            for x, y in zip(df_ev["Năm"], df_ev[metric]):
                ax3.text(x, y, f"{y:,.0f}", fontsize=8, ha='center', va='bottom')

        nganh_row = df_nganh[
            (df_nganh["Chỉ số"].str.strip() == metric.strip()) &
            (df_nganh["Ngành"].str.strip() == sector.strip())
        ]
        if not nganh_row.empty:
            nganh_values = nganh_row.iloc[0][valid_years].astype(float)
            ax3.plot(valid_years_int, nganh_values, marker="x", linestyle="--", label="Ngành")
            for x, y in zip(valid_years_int, nganh_values):
                ax3.text(x, y, f"{y:,.0f}", fontsize=8, ha='center', va='bottom')

        ax3.set_title("EV/EBITDA")
        ax3.set_xticks(valid_years_int)
        ax3.set_xticklabels(valid_years)
        ax3.grid(True)
        ax3.legend()
        fig3.tight_layout()
        buf3 = BytesIO()
        fig3.savefig(buf3, format="png", dpi=100, bbox_inches="tight")
        chart3 = base64.b64encode(buf3.getvalue()).decode("utf-8")
        plt.close(fig3)

        # HTML kết quả
        html_output = f"""
        <div><strong>Định giá {ticker} so với ngành {sector} (năm 2024)</strong></div>
        {compare_html}
        <div style='margin-top:10px'><strong>Biểu đồ các chỉ tiêu định giá theo thời gian (2021–2024):</strong></div>
        <img src='data:image/png;base64,{chart1}' style='max-width:100%; margin-bottom:20px;' />
        <img src='data:image/png;base64,{chart2}' style='width: 100%; margin-bottom: 20px;' />
        <img src='data:image/png;base64,{chart3}' style='width: 100%; margin-bottom: 20px;' />
        """
        return html_output

    except Exception as e:
        return f"<p>❌ Lỗi khi phân tích chỉ số định giá: {e}</p>"





