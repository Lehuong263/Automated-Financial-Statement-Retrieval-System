import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from weasyprint import HTML
import os
from jinja2 import Environment, FileSystemLoader
import numpy as np

import base64
import io
from bs4 import BeautifulSoup

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = env.get_template("report_template.html")
def prepare_financial_statement(df, ticker, statement_name):
    if statement_name not in ["BCDKT", "KQKD", "LCTT"]:
        return f"<p style='color:red;'>❌ Loại báo cáo không hợp lệ: {statement_name}</p>"
    df = df[df["Mã"] == ticker].copy()
    if df.empty:
        return f"<p style='color:red;'>⚠️ Không có dữ liệu {statement_name} cho mã {ticker}.</p>"
    drop_cols = ["Unnamed: 0", "STT", "Mã", "Tên công ty", "Sàn", "Ngành ICB - cấp 1",
                 "Ngành ICB - cấp 2", "Ngành ICB - cấp 3", "Ngành ICB - cấp 4", "Quý", "Trạng thái kiểm toán"]
    df.drop(columns=[col for col in drop_cols if col in df.columns], inplace=True)
    df["Năm"] = pd.to_numeric(df["Năm"], errors="coerce").astype("Int64")
    if statement_name == "BCDKT":
        selected_items = [
            "TỔNG CỘNG TÀI SẢN",
            "TÀI SẢN NGẮN HẠN",
            "Tiền và tương đương tiền",
            "Đầu tư tài chính ngắn hạn",
            "Các khoản phải thu ngắn hạn",
            "Hàng tồn kho, ròng",
            "Tài sản ngắn hạn khác",
            "TÀI SẢN DÀI HẠN",
            "Phải thu dài hạn",
            "Tài sản cố định",
            "Giá trị ròng tài sản đầu tư",
            "Tài sản dở dang dài hạn",
            "Đầu tư dài hạn",
            "Tài sản dài hạn khác",
            "NỢ PHẢI TRẢ",
            "Nợ ngắn hạn",
            "Vay và nợ thuê tài chính ngắn hạn",
            "Nợ dài hạn",
            "Vay và nợ thuê tài chính dài hạn",
            "VỐN CHỦ SỞ HỮU",
            "TỔNG CỘNG NGUỒN VỐN",
        ]
    elif statement_name == "KQKD":
        excluded_cols = [
            "Lãi/ lỗ từ công ty liên doanh (trước 2015)",
            "Lợi ích của cổ đông thiểu số",
            "Cổ đông của Công ty mẹ",
            "Lãi cơ bản trên cổ phiếu"
        ]

        selected_items = [col for col in df.columns if col not in excluded_cols and col != "Năm"]
    elif statement_name == "LCTT":
        rename_map = {
            "Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh (TT)": "Lưu chuyển tiền thuần từ hoạt động kinh doanh (CFO)",
            "Lưu chuyển tiền tệ ròng từ hoạt động đầu tư (TT)": "Lưu chuyển tiền thuần từ hoạt động đầu tư (CFI)",
            "Lưu chuyển tiền tệ từ hoạt động tài chính (TT)": "Lưu chuyển tiền thuần từ hoạt động tài chính (CFF)",
            "Lưu chuyển tiền thuần trong kỳ (TT)": "Lưu chuyển tiền thuần trong kỳ",
            "Tiền và tương đương tiền đầu kỳ (TT)": "Tiền và tương đương tiền đầu kỳ",
            "Ảnh hưởng của chênh lệch tỷ giá(TT)": "Ảnh hưởng của chênh lệch tỷ giá",
            "Tiền và tương đương tiền cuối kỳ (TT)": "Tiền và tương đương tiền cuối kỳ",

        }
        # Áp dụng đổi tên
        df = df.rename(columns=rename_map)
        # Lọc đúng các cột bạn cần (kèm theo Mã và Năm)
        selected_items = list(rename_map.values())
    original_items = df.drop(columns=["Năm"]).columns.tolist()
    df_filtered = df[["Năm"] + [item for item in original_items if item in selected_items]]
    df_melted = df_filtered.melt(id_vars=["Năm"], var_name="Chỉ tiêu", value_name="Giá trị")
    df_pivot = df_melted.pivot(index="Chỉ tiêu", columns="Năm", values="Giá trị").reset_index()
    df_pivot['Chỉ tiêu'] = pd.Categorical(df_pivot['Chỉ tiêu'], categories=selected_items, ordered=True)
    df_pivot = df_pivot.sort_values('Chỉ tiêu').reset_index(drop=True)
    df_pivot.columns = ["Chỉ tiêu"] + [str(col) for col in df_pivot.columns[1:]]
    column_count = len(df_pivot.columns)
    # === THÊM DÒNG CHART VÀO BẢNG ===
    if statement_name == "BCDKT":
        extra_items = ["GTCL TSCĐ hữu hình", "GTCL tài sản cố định vô hình"]
        all_items = list(set(selected_items + extra_items))
        df_filtered = df[["Năm"] + [col for col in df.columns if col in all_items]].copy()

        df_filtered["Tài sản khác"] = (
                df_filtered["TÀI SẢN DÀI HẠN"]
                - df_filtered["GTCL TSCĐ hữu hình"]
                - df_filtered["GTCL tài sản cố định vô hình"]
        )

        # Màu giống biểu đồ FireAnt
        color_map = {
            "TÀI SẢN NGẮN HẠN": "#f8e29a",
            "GTCL TSCĐ hữu hình": "#33a02c",
            "GTCL tài sản cố định vô hình": "#1f78b4",
            "Tài sản khác": "#a6cee3",
            "Nợ ngắn hạn": "#fb9a99",
            "Nợ dài hạn": "#e31a1c",
            "VỐN CHỦ SỞ HỮU": "#ff7f00"
        }
        order = [
            "TÀI SẢN NGẮN HẠN", "GTCL TSCĐ hữu hình", "GTCL tài sản cố định vô hình", "Tài sản khác",
            "Nợ ngắn hạn", "Nợ dài hạn", "VỐN CHỦ SỞ HỮU"
        ]

        legend_html = ""
        for label in order:
            color = color_map[label]
            legend_html += (
                f"<div style='margin-bottom:4px; font-size:12px; line-height:1.2;'>"
                f"<span style='display:inline-block;width:12px;height:12px;background:{color};"
                f"margin-right:6px;border-radius:2px;'></span>{label}</div>"
            )
        chart_row = [f"<div style='line-height:1.4'>{legend_html.strip()}</div>"]
        for _, row in df_filtered.iterrows():
            try:
                fig, ax = plt.subplots(figsize=(1.6, 2.6))
                left, right = -0.15, 0.15
                # === CỘT TÀI SẢN (bên trái) ===

                ax.bar(left, row["Tài sản khác"],
                       color=color_map["Tài sản khác"], width=0.3)

                ax.bar(left, row["GTCL tài sản cố định vô hình"],
                       bottom=row["Tài sản khác"],
                       color=color_map["GTCL tài sản cố định vô hình"], width=0.3)

                ax.bar(left, row["GTCL TSCĐ hữu hình"],
                       bottom=row["Tài sản khác"] + row["GTCL tài sản cố định vô hình"],
                       color=color_map["GTCL TSCĐ hữu hình"], width=0.3)

                ax.bar(left, row["TÀI SẢN NGẮN HẠN"],
                       bottom=row["Tài sản khác"] + row["GTCL tài sản cố định vô hình"] + row["GTCL TSCĐ hữu hình"],
                       color=color_map["TÀI SẢN NGẮN HẠN"], width=0.3)


                # === CỘT NỢ & VỐN (bên phải) ==
                ax.bar(right, row["VỐN CHỦ SỞ HỮU"],
                       color=color_map["VỐN CHỦ SỞ HỮU"], width=0.3)

                ax.bar(right, row["Nợ dài hạn"],
                       bottom=row["VỐN CHỦ SỞ HỮU"],
                       color=color_map["Nợ dài hạn"], width=0.3)

                ax.bar(right, row["Nợ ngắn hạn"],
                       bottom=row["VỐN CHỦ SỞ HỮU"] + row["Nợ dài hạn"],
                       color=color_map["Nợ ngắn hạn"], width=0.3)

                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_frame_on(False)
                buf = io.BytesIO()
                plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", transparent=True)
                plt.close(fig)
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                chart_row.append(f'<img src="data:image/png;base64,{img_base64}" style="height:100px;" />')
            except:
                chart_row.append("N/A")

        while len(chart_row) < column_count:
            chart_row.append("")
        df_chart = pd.DataFrame([chart_row], columns=df_pivot.columns)
        df_pivot = pd.concat([df_chart, df_pivot], ignore_index=True)

    for col in df_pivot.columns[1:]:
        df_pivot[col] = df_pivot[col].apply(
            lambda x: x if isinstance(x, str) and x.startswith("<img") else (
                f"{pd.to_numeric(x, errors='coerce') / 1e9:,.1f}" if pd.notna(x) else "N/A"
            )
        )
    def format_label(label):
        if not isinstance(label, str):
            return label
        if "vay và nợ thuê tài chính ngắn hạn" in label.lower():
            return '<span style="padding-left: 20px; font-style: italic; font-family: Arial, sans-serif;">- Vay và nợ thuê tài chính ngắn hạn</span>'
        if "vay và nợ thuê tài chính dài hạn" in label.lower():
            return '<span style="padding-left: 20px; font-style: italic; font-family: Arial, sans-serif;">- Vay và nợ thuê tài chính dài hạn</span>'
        if "Trong đó: Chi phí lãi vay" in label.lower():
            return '<span style="padding-left: 20px; font-style: italic; font-family: Arial, sans-serif;">- Trong đó: Chi phí lãi vay</span>'
        if label.isupper():
            return f"<span class='bold-label'>{label}</span>"
        return label

    df_pivot["Chỉ tiêu"] = df_pivot["Chỉ tiêu"].apply(format_label)

    html = df_pivot.to_html(index=False, classes="financial-table", border=0, escape=False)
    soup = BeautifulSoup(html, "html.parser")
    for i, tr in enumerate(soup.find("tbody").find_all("tr")):
        tds = tr.find_all("td")
        if tds:
            tds[0]["class"] = "label-cell"
        if i % 2 == 1:
            tr["class"] = tr.get("class", []) + ["even"]
    if soup.find("thead").find("th").text.strip().lower() == "năm":
        soup.find("thead").find("th").decompose()
    for tr in soup.find("tbody").find_all("tr"):
        tds = tr.find_all("td")
        if tds: tds[0]["class"] = "label-cell"

    return str(soup)


def generate_financial_structure_chart(df, ticker):
    df = df[df["Mã"] == ticker].copy()
    if df.empty:
        return "<p style='color:red;'>⚠️ Không có dữ liệu để tạo biểu đồ cấu trúc tài sản.</p>"
    df["Năm"] = pd.to_numeric(df["Năm"], errors="coerce")
    df = df.sort_values("Năm")

    df["Nợ/VCSH"] = df["NỢ PHẢI TRẢ"] / df["VỐN CHỦ SỞ HỮU"]
    df["(Vay NH+DH)/VCSH"] = (
                                     df["Vay và nợ thuê tài chính ngắn hạn"] + df["Vay và nợ thuê tài chính dài hạn"]
                             ) / df["VỐN CHỦ SỞ HỮU"]

    plt.figure(figsize=(10, 5))
    plt.plot(df["Năm"], df["Nợ/VCSH"], marker='s', label="Nợ/VCSH", color='#00bcd4')
    plt.plot(df["Năm"], df["(Vay NH+DH)/VCSH"], marker='o', label="(Vay NH+DH)/VCSH", color='#ffab91')
    for i, row in df.iterrows():
        plt.text(row["Năm"], row["Nợ/VCSH"] + 0.05, f'{row["Nợ/VCSH"]:.2f}', ha='center', fontsize=9, color='black')
        plt.text(row["Năm"], row["(Vay NH+DH)/VCSH"] + 0.05, f'{row["(Vay NH+DH)/VCSH"]:.2f}', ha='center', fontsize=9,
                 color='black')
    plt.title("CẤU TRÚC TÀI SẢN", fontsize=14, weight='bold')
    plt.ylabel("Lần")
    plt.xticks(df["Năm"])
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.legend()
    plt.tight_layout()

    # Lưu vào buffer dưới dạng base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")

    return f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%;" />'

def plot_profitability_chart(df, ticker):
    df = df[df["Mã"] == ticker].copy()
    if df.empty:
        return "<p style='color:red;'>⚠️ Không có dữ liệu KQKD cho mã này.</p>"

    df.columns = df.columns.str.strip()
    df["Năm"] = pd.to_numeric(df["Năm"], errors="coerce")

    # Định nghĩa các cột cần dùng
    revenue_col = "Doanh thu bán hàng và cung cấp dịch vụ"
    operating_profit_col = "Lợi nhuận thuần từ hoạt động kinh doanh"
    net_profit_col = "Lợi nhuận sau thuế thu nhập doanh nghiệp"

    # Kiểm tra đủ cột chưa
    for col in [revenue_col, operating_profit_col, net_profit_col]:
        if col not in df.columns:
            return f"<p style='color:red;'>⚠️ Thiếu cột {col} trong dữ liệu.</p>"

    # Lọc và sắp xếp
    df = df[["Năm", revenue_col, operating_profit_col, net_profit_col]].dropna()
    df = df.sort_values("Năm")

    # Tính toán
    revenue = df[revenue_col].values / 1e9
    op_profit = df[operating_profit_col].values / 1e9
    net_profit = df[net_profit_col].values / 1e9
    margin = (df[net_profit_col] / df[revenue_col] * 100).values
    years = df["Năm"].astype(int).tolist()
    x = np.arange(len(years))
    width = 0.25

    fig, ax1 = plt.subplots(figsize=(10, 4.5))
    ax2 = ax1.twinx()

    bars1 = ax1.bar(x - width, revenue, width, label="Doanh thu", color="#1f78b4")
    bars2 = ax1.bar(x, op_profit, width, label="Lợi nhuận từ hoạt động KD", color="#a6cee3")
    bars3 = ax1.bar(x + width, net_profit, width, label="Lợi nhuận thuần", color="#ffffb3")

    line = ax2.plot(x, margin, color="#f781bf", marker="o", label="Biên lợi nhuận thuần (%)", linewidth=2)

    # Hiển thị giá trị
    def show_values(bars, axis):
        for bar in bars:
            height = bar.get_height()
            if pd.notna(height):
                axis.text(bar.get_x() + bar.get_width()/2, height, f"{height:,.0f}", ha="center", va="bottom", fontsize=8)

    show_values(bars1, ax1)
    show_values(bars2, ax1)
    show_values(bars3, ax1)

    ax1.set_title("Lãi và Lỗ", fontsize=14, fontweight="bold")
    ax1.set_ylabel("Tỷ VNĐ")
    ax2.set_ylabel("%")

    ax1.set_xticks(x)
    ax1.set_xticklabels(years)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}%"))

    lines_labels = [*zip([bars1, bars2, bars3], ["Doanh thu", "Lợi nhuận từ hoạt động KD", "Lợi nhuận thuần"])]
    line_label = [(line[0], "Biên lợi nhuận thuần (%)")]

    handles = [h for h, _ in lines_labels] + [h for h, _ in line_label]
    labels = [l for _, l in lines_labels] + [l for _, l in line_label]

    ax1.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)
    ax1.grid(True, axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout(rect=[0, 0.05, 1, 1])

    # Encode
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")

    return f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%;" />'
def plot_cashflow_bar_chart(df, ticker):
    df = df[df["Mã"] == ticker].copy()
    if df.empty:
        return "<p style='color:red;'>⚠️ Không có dữ liệu LCTT cho mã này.</p>"

    df.columns = df.columns.str.strip()
    df["Năm"] = pd.to_numeric(df["Năm"], errors="coerce")

    # === Rename các cột gốc thành dạng chuẩn ===
    rename_map = {
        "Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh (TT)": "Lưu chuyển tiền thuần từ hoạt động kinh doanh (CFO)",
        "Lưu chuyển tiền tệ ròng từ hoạt động đầu tư (TT)": "Lưu chuyển tiền thuần từ hoạt động đầu tư (CFI)",
        "Lưu chuyển tiền tệ từ hoạt động tài chính (TT)": "Lưu chuyển tiền thuần từ hoạt động tài chính (CFF)",
        "Tiền và tương đương tiền cuối kỳ (TT)": "Tiền và tương đương tiền cuối kỳ"
    }
    df = df.rename(columns=rename_map)

    # Các cột sau đổi tên
    cfo_col = "Lưu chuyển tiền thuần từ hoạt động kinh doanh (CFO)"
    cfi_col = "Lưu chuyển tiền thuần từ hoạt động đầu tư (CFI)"
    cff_col = "Lưu chuyển tiền thuần từ hoạt động tài chính (CFF)"
    cash_col = "Tiền và tương đương tiền cuối kỳ"
    if not all(col in df.columns for col in [cfo_col, cfi_col, cff_col]):
        return "<p style='color:red;'>⚠️ Thiếu cột CFO/CFI/CFF trong dữ liệu.</p>"

    df = df[["Năm", cfo_col, cfi_col, cff_col, cash_col]].dropna()
    df = df.sort_values("Năm")

    cash = (np.array(df[cash_col].tolist()) / 1e9).tolist()
    cfo = (np.array(df[cfo_col].tolist()) / 1e9).tolist()
    cfi = (np.array(df[cfi_col].tolist()) / 1e9).tolist()
    cff = (np.array(df[cff_col].tolist()) / 1e9).tolist()
    years = df["Năm"].astype(int).tolist()

    x = np.arange(len(years))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 4.5))

    bars1 = ax.bar(x - width, cfo, width, label="CFO", color="#1f78b4")
    bars2 = ax.bar(x, cfi, width, label="CFI", color="#fb9a99")
    bars3 = ax.bar(x + width, cff, width, label="CFF", color="#fde0c6")

    # Hiển thị giá trị trên cột
    def show_values(bars):
        for bar in bars:
            height = bar.get_height()
            if pd.notna(height):
                ax.text(bar.get_x() + bar.get_width() / 2, height,
                        f"{height:,.0f}", ha='center', va='bottom', fontsize=8)

    show_values(bars1)
    show_values(bars2)
    show_values(bars3)
    ax.plot(x, cash, color="#9c27b0", label="Tiền và tương đương tiền cuối kỳ", linewidth=2, marker='o')
    ax.set_title("Lưu chuyển tiền tệ", fontsize=14, fontweight="bold")
    ax.set_ylabel("Tỷ VNĐ")
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=4, frameon=False)
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout(rect=[0, 0.05, 1, 1])

    # Encode to base64 for embedding in HTML
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")

    return f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%;" />'
def export_to_pdf(company_data, financial_data, filename="company_info.pdf", start_date=None, end_date=None):
    ticker = company_data["Mã CK"]

    df_bcdkt = financial_data.get("BCDKT.csv")
    df_kqkd = financial_data.get("KQKD.csv")
    df_lctt = financial_data.get("LCTT.csv")
    df_out = pd.read_csv("D:/Python Project/10_diem - Copy/data/technical/output.csv")
    from financial_ratios import prepare_financial_ratios_html, generate_industry_comparison_html
    financial_ratios_html = prepare_financial_ratios_html(ticker)
    industry_comparison_table = generate_industry_comparison_html(ticker, 2024)  # hoặc năm bạn chọn

    # Các bảng tài chính
    balance_sheet_html = prepare_financial_statement(df_bcdkt, ticker, "BCDKT")
    income_statement_html = prepare_financial_statement(df_kqkd, ticker, "KQKD")
    cashflow_statement_html = prepare_financial_statement(df_lctt, ticker, "LCTT")

    balance_sheet_chart = generate_financial_structure_chart(df_bcdkt, ticker)
    income_profitability_chart = plot_profitability_chart(df_kqkd, ticker)
    cashflow_bar_chart = plot_cashflow_bar_chart(df_lctt, ticker)
    # Render vào HTML template

    from ai_analyzer import generate_combined_section_analysis

    # Phân tích AI gộp (dữ liệu thật + biểu đồ mô tả)
    sections = generate_combined_section_analysis(ticker, df_bcdkt, df_kqkd, df_lctt)
    from investor_trade import generate_investor_trade_html
    template_data = {}
    template_data["investor_trade_analysis"] = generate_investor_trade_html(ticker, df_kqkd, df_out)

    # Gắn đoạn phân tích vào biểu đồ
    balance_sheet_chart += sections["balance_analysis"]
    income_profitability_chart += sections["income_analysis"]
    cashflow_bar_chart += sections["cashflow_analysis"]
    from TA_analysis import generate_technical_analysis
    technical_analysis = generate_technical_analysis(ticker,start_date,end_date)
    from tongquan import generate_industry_analysis_html
    industry_analysis = generate_industry_analysis_html(ticker)
    from tongquan import generate_vonhoa_piecharts_html
    pie_html = generate_vonhoa_piecharts_html(ticker)
    from tongquan import generate_valuation_analysis_html
    valuation_analysis = generate_valuation_analysis_html(ticker)
    from ai_analyzer import generate_final_conclusion_with_ai
    html_conclusion = generate_final_conclusion_with_ai(ticker, df_bcdkt, df_kqkd, df_lctt)
    from datetime import datetime
    today = datetime.today().strftime("%d/%m/%Y")
    rendered_html = template.render(
        company=company_data,
        balance_sheet=balance_sheet_html,
        income_statement=income_statement_html,
        cashflow_statement=cashflow_statement_html,
        balance_sheet_chart=balance_sheet_chart,
        cashflow_bar_chart=cashflow_bar_chart,
        income_profitability_chart=income_profitability_chart,
        financial_ratios_table=financial_ratios_html,
        industry_comparison_table=industry_comparison_table,
        investor_trade_analysis=template_data["investor_trade_analysis"],
        technical_analysis=technical_analysis,
        industry_analysis=industry_analysis,
        pie_html=pie_html,
        valuation_analysis=valuation_analysis,
        conclusion = html_conclusion,
        today=today
    )

    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    HTML(string=rendered_html).write_pdf(output_path)
    print(f"✅ PDF đã được lưu tại: {output_path}")
    return output_path
