import numpy as np
import pandas as pd
# Đọc dữ liệu từ các file CSV
bcdkt = pd.read_csv('BCDKT.csv')
kqkd = pd.read_csv('KQKD.csv')
lctt = pd.read_csv('LCTT.csv')

def safe_divide(a, b, is_percentage=False):
    if b == 0 or pd.isna(b):
        return np.nan
    result = round(a / b * 100, 2) if is_percentage else round(a / b, 2)
    return f"{result}%" if is_percentage else result

financial_indicators = [
    "Chỉ số thanh toán tiền mặt", "Chỉ số thanh toán hiện thời",
    "Chỉ số thanh toán nhanh","Vòng quay tài sản",
    "Vòng quay TSCĐ", "Đòn bẩy tài chính", "Khả năng chi trả lãi vay",
    "Biên EBIT (%)", "Biên lợi nhuận gộp (%)","Biên lợi nhuận ròng (%)", "ROE (%)", "ROA (%)","ROIC (%)"
]
all_results = []
def ensure_all_indicators(ticker, year, results_dict):
    """ Đảm bảo rằng mỗi chỉ tiêu tài chính đều có mặt trong dữ liệu, nếu thiếu thì thêm NaN """
    for indicator in financial_indicators:
        if indicator not in results_dict:
            results_dict[indicator] = np.nan
    for indicator, value in results_dict.items():
        all_results.append([ticker, year, indicator, value])

# Duyệt theo độ dài lớn nhất của 3 bảng
data_length = max(len(bcdkt), len(kqkd), len(lctt))
for i in range(data_length):
    try:
        ticker = bcdkt.iloc[i]["Mã"] if i < len(bcdkt) else (kqkd.iloc[i]["Mã"] if i < len(kqkd) else "N/A")
        year = bcdkt.iloc[i]["Năm"] if i < len(bcdkt) else (kqkd.iloc[i]["Năm"] if i < len(kqkd) else "N/A")
        if pd.isna(year):
            year = 0  # Đặt giá trị mặc định để tránh lỗi ép kiểu
        year = int(year)
        results = {}
        prev_equity = bcdkt.iloc[i - 1]["VỐN CHỦ SỞ HỮU"]
        avg_equity = (bcdkt.iloc[i]["VỐN CHỦ SỞ HỮU"] + prev_equity) / 2

        net_income = kqkd.iloc[i].get("Lợi nhuận sau thuế thu nhập doanh nghiệp")
        revenue = kqkd.iloc[i].get("Doanh thu thuần")
        gross_profit = kqkd.iloc[i].get("Lợi nhuận gộp về bán hàng và cung cấp dịch vụ")
        cogs = revenue - gross_profit
        current_liab = bcdkt.iloc[i].get("Nợ ngắn hạn")
        cash = bcdkt.iloc[i].get("Tiền và tương đương tiền")
        short_debt = bcdkt.iloc[i].get("Vay và nợ thuê tài chính ngắn hạn")
        long_debt = bcdkt.iloc[i].get("Vay và nợ thuê tài chính dài hạn")
        equity = bcdkt.iloc[i].get("VỐN CHỦ SỞ HỮU")
        total_assets = bcdkt.iloc[i].get("TỔNG CỘNG TÀI SẢN")
        qldn = abs(kqkd.iloc[i].get("Chi phí quản lý doanh  nghiệp"))
        cpbh= abs(kqkd.iloc[i].get("Chi phí bán hàng"))
        interest_expense = abs(kqkd.iloc[i].get("Trong đó: Chi phí lãi vay"))
        ebit = revenue - cogs - qldn - cpbh
        tax = abs(kqkd.iloc[i].get("Chi phí thuế thu nhập doanh nghiệp"))
        results["Chỉ số thanh toán tiền mặt"] = safe_divide(cash, current_liab)
        results["Chỉ số thanh toán hiện thời"] = safe_divide(bcdkt.iloc[i]["TÀI SẢN NGẮN HẠN"], current_liab)
        results["Chỉ số thanh toán nhanh"] = safe_divide(
            cash + bcdkt.iloc[i]["Các khoản phải thu ngắn hạn"] + bcdkt.iloc[i].get("Đầu tư tài chính ngắn hạn"),
            current_liab)
        results["Đòn bẩy tài chính"] = safe_divide(total_assets, equity)
        results["Khả năng chi trả lãi vay"] = safe_divide(ebit, interest_expense)
        results["Biên EBIT (%)"] = safe_divide(ebit, revenue,True)
        results["Biên lợi nhuận gộp (%)"] = safe_divide(gross_profit, revenue,True)
        results["Biên lợi nhuận ròng (%)"] = safe_divide(net_income, revenue,True)


        ensure_all_indicators(ticker, year, results)
    except Exception as e:
        print(f"⚠️ Lỗi khi tính toán {ticker} năm {year}: {e}")

# Chuyển đổi dữ liệu thành DataFrame
financial_ratios_df = pd.DataFrame(all_results, columns=["Mã", "Năm", "Chỉ số", "Giá trị"])
financial_ratios_df["Giá trị"] = financial_ratios_df["Giá trị"].astype(str).str.replace("%", "")
financial_ratios_df["Giá trị"] = pd.to_numeric(financial_ratios_df["Giá trị"], errors='coerce')
financial_ratios_df = financial_ratios_df[financial_ratios_df["Năm"] != 0]

# Giữ nguyên giá trị NaN khi pivot
pivot_df = financial_ratios_df.pivot_table(index=["Mã", "Chỉ số"], columns="Năm", values="Giá trị")

# Định dạng lại cột năm
pivot_df.columns = [''.join(c if c.isdigit() else '' for c in str(a)) if isinstance(a, int) else a for a in pivot_df.columns]
# Định dạng lại cột
pivot_df.reset_index(inplace=True)

# Lưu kết quả vào file CSV mà không thay thế NaN thành 0
pivot_df.to_csv('financial_ratios.csv', index=False, na_rep="NaN")