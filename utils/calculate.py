import pandas as pd
import os
import sys
import numpy as np
def calculate_financial_ratios(kqkd_csv_file_path, scraped_csv_file_path, ticker):

    try:
        # Đọc file CSV KQKD
        kqkd = pd.read_csv(kqkd_csv_file_path, encoding='utf-8')
        print(f"✅ Đã đọc dữ liệu từ file KQKD: {kqkd_csv_file_path}")

        # Đọc file CSV cào từ web
        scraped_data = pd.read_csv(scraped_csv_file_path, encoding='utf-8')
        print(f"✅ Đã đọc dữ liệu từ file scraped: {scraped_csv_file_path}")
        # Fill NaN toàn bộ thành 0
        kqkd = kqkd.fillna(0)
        scraped_data = scraped_data.fillna(0)

        # Lọc dữ liệu theo ticker
        kqkd = kqkd[kqkd["Mã"] == ticker]
        print(f"✅ Đã lọc dữ liệu cho mã cổ phiếu: {ticker}")

        # Chuyển đổi dữ liệu sang định dạng wide format
        scraped_data = scraped_data.melt(id_vars=["Chỉ tiêu"], var_name="Năm", value_name="Giá trị")
        scraped_data["Năm"] = scraped_data["Năm"].astype(int)
        scraped_data = scraped_data.groupby(["Chỉ tiêu", "Năm"], as_index=False).mean()
        scraped_data = scraped_data.pivot(index="Chỉ tiêu", columns="Năm", values="Giá trị")


        def safe_divide(a, b, is_percentage=False):
            try:
                a = float(a)
                b = float(b)
                if b == 0 or pd.isna(b):
                    return np.nan
                result = a / b * 100 if is_percentage else a / b
                return result
            except Exception:
                return np.nan
        all_results = []
            # Lấy danh sách các năm có thể tính toán
        available_years = sorted([y for y in scraped_data.columns if isinstance(y, int)])

        for year in available_years:
            prev_year = year - 1
            if prev_year not in scraped_data.columns:
                continue

            kqkd_row = kqkd[kqkd["Năm"] == year]
            if kqkd_row.empty:
                continue
            kqkd_row = kqkd_row.iloc[0]

            results = {}
            try:

        # Lấy dữ liệu từ cột tương ứng năm
                prev_receivables = scraped_data.loc["1. Phải thu ngắn hạn của khách hàng", year - 1]
                current_receivables = scraped_data.loc["1. Phải thu ngắn hạn của khách hàng", year]
                avg_receivables = (current_receivables + prev_receivables) / 2

                prev_inventory = scraped_data.loc["1. Hàng tồn kho", year - 1]
                current_inventory = scraped_data.loc["1. Hàng tồn kho", year]
                avg_inventory = (current_inventory + prev_inventory) / 2

                prev_payables = scraped_data.loc["1. Phải trả người bán ngắn hạn", year - 1] + scraped_data.loc["1. Phải trả người bán dài hạn", year - 1]
                current_payables = scraped_data.loc["1. Phải trả người bán ngắn hạn", year] + scraped_data.loc["1. Phải trả người bán dài hạn", year]
                avg_payables = (current_payables + prev_payables) / 2
                prev_asset = scraped_data.loc["TỔNG CỘNG TÀI SẢN", year - 1]
                current_asset = scraped_data.loc["TỔNG CỘNG TÀI SẢN",year]
                avg_asset = (prev_asset + current_asset) / 2
                prev_fixed_assets = scraped_data.loc["1. Tài sản cố định hữu hình",year-1] + scraped_data.loc["2. Tài sản cố định thuê tài chính", year - 1]
                current_fixed_assets = scraped_data.loc["1. Tài sản cố định hữu hình", year] + scraped_data.loc["2. Tài sản cố định thuê tài chính", year]
                avg_fixed_assets = (prev_fixed_assets + current_fixed_assets) / 2
                prev_equity = scraped_data.loc["D.VỐN CHỦ SỞ HỮU", year - 1]
                current_equity = scraped_data.loc["D.VỐN CHỦ SỞ HỮU", year]
                avg_equity = (current_equity + prev_equity) / 2
                revenue = kqkd_row.get("Doanh thu thuần")
                net_income = kqkd_row.get("Lợi nhuận sau thuế thu nhập doanh nghiệp")
                ebt= kqkd_row.get("Tổng lợi nhuận kế toán trước thuế")
                gross_profit = kqkd_row.get("Lợi nhuận gộp về bán hàng và cung cấp dịch vụ")
                cogs = revenue - gross_profit
                qldn = abs(kqkd_row.get("Chi phí quản lý doanh  nghiệp"))
                cpbh = abs(kqkd_row.get("Chi phí bán hàng"))
                interest_expense = abs(kqkd_row.get("Trong đó: Chi phí lãi vay"))
                ebit = revenue - cogs - qldn - cpbh
                tax = abs(kqkd_row.get("Chi phí thuế thu nhập doanh nghiệp"))
                pre_invested_capital = scraped_data.loc["I. Vốn chủ sở hữu",year - 1] + scraped_data.loc["10. Vay và nợ thuê tài chính ngắn hạn",year -1] + scraped_data.loc["8. Vay và nợ thuê tài chính dài hạn",year -1] - scraped_data.loc["I. Tiền và các khoản tương đương tiền",year -1]
                current_invested_capital = scraped_data.loc["I. Vốn chủ sở hữu",year] + scraped_data.loc["10. Vay và nợ thuê tài chính ngắn hạn",year] + scraped_data.loc["8. Vay và nợ thuê tài chính dài hạn",year] - scraped_data.loc["I. Tiền và các khoản tương đương tiền",year]
                avg_invested_capital= (pre_invested_capital + current_invested_capital)/2
                results["Vòng quay tài sản"] = safe_divide(revenue, avg_asset)
                results["Vòng quay TSCĐ"] = safe_divide(revenue, avg_fixed_assets)
                results["Số ngày thu tiền bình quân"] = safe_divide(365, safe_divide(revenue, avg_receivables))
                results["Số ngày tồn kho bình quân"] = safe_divide(365, safe_divide(cogs, avg_inventory))
                results["Số ngày thanh toán bình quân"] = safe_divide(365, safe_divide(cogs, avg_payables))
                results["Chu kỳ tiền"] = results["Số ngày thu tiền bình quân"] + results["Số ngày tồn kho bình quân"] - results["Số ngày thanh toán bình quân"]
                results["ROE (%)"] = safe_divide(net_income, avg_equity,True)
                results["ROA (%)"] = safe_divide((net_income + (interest_expense*(1 - (tax/ebt)))), avg_asset,True)
                results["ROIC (%)"] = safe_divide((ebit *(1 - (tax/ebt))),avg_invested_capital,True)
                for indicator, value in results.items():
                    all_results.append([ticker, year, indicator, value])

            except KeyError as key_err:
                print(f"⚠️ Thiếu dữ liệu chỉ tiêu cho năm {year}: {key_err}")
                continue
        # Chuyển đổi dữ liệu thành DataFrame
        financial_ratios_df = pd.DataFrame(all_results, columns=["Mã", "Năm", "Chỉ số", "Giá trị"])
        financial_ratios_df["Giá trị"] = financial_ratios_df["Giá trị"].astype(str).str.replace("%", "")
        financial_ratios_df["Giá trị"] = pd.to_numeric(financial_ratios_df["Giá trị"], errors='coerce')
        financial_ratios_df["Giá trị"] = financial_ratios_df["Giá trị"].apply(
            lambda x: round(x, 2) if pd.notna(x) else np.nan)
        financial_ratios_df = financial_ratios_df[financial_ratios_df["Năm"] != 0]

        # Lọc kết quả cuối cùng để chỉ giữ lại các năm từ 2020 trở đi
        financial_ratios_df = financial_ratios_df[financial_ratios_df["Năm"] >= 2019]

        # Pivot lại bảng dữ liệu theo format mong muốn
        pivot_df = financial_ratios_df.pivot(index=["Mã", "Chỉ số"], columns="Năm", values="Giá trị").reset_index()

        # Đảm bảo thư mục output tồn tại
        output_dir = "D:/Python Project/10_diem - Copy/data/calculate/"
        os.makedirs(output_dir, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại
        output_file = f"{output_dir}{ticker}_financial_ratios.csv"
        pivot_df.to_csv(output_file, index=False, na_rep="NaN")

        print(f"✅ File {ticker}_financial_ratios.csv đã được tạo tại {output_file}")
    # Chuyển đổi dữ liệu thành DataFrame
    except Exception as e:
        print(f"Lỗi: {e}")
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Sử dụng: python calculation.py <đường_dẫn_file_kqkd> <đường_dẫn_file_scraped> <mã_cổ_phiếu>")
    else:
        kqkd_csv_file = sys.argv[1]
        scraped_csv_file = sys.argv[2]
        ticker = sys.argv[3]
        calculate_financial_ratios(kqkd_csv_file, scraped_csv_file, ticker)
