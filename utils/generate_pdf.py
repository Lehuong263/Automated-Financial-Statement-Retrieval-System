import subprocess

def get_input_dates():
    start_date = input("Nhập ngày bắt đầu để phân tích kỹ thuật (YYYY-MM-DD): ").strip()
    end_date = input("Nhập ngày kết thúc để phân tích kỹ thuật (YYYY-MM-DD): ").strip()
    return start_date, end_date
import sys

def generate_pdf_report():
    from data_loader import load_csv_data, get_company_info
    from pdf_exporter import export_to_pdf

    # Input ticker and dates only once
    ticker = input("Nhập mã cổ phiếu muốn xuất báo cáo PDF (Ví dụ: FPT): ").strip()
    start_date, end_date = get_input_dates()
    python_executable = sys.executable

    # Chạy file Web_scraping.py với tham số mã cổ phiếu
    print(f"🚀 Đang thu thập dữ liệu cho mã cổ phiếu: {ticker}")
    subprocess.run([python_executable, "D:/Python Project/10_diem - Copy/utils/Web_scraping.py", ticker])
    # Tìm file CSV mới được tạo
    csv_file_path = f"D:/Python Project/10_diem - Copy/data/bs_them/{ticker}_BS_2019_2024.csv"

    # Chạy file calculation.py để tính toán
    print(f" Đang tính toán chỉ số tài chính...")
    try:
        result = subprocess.run(
            [sys.executable, r"D:\Python Project\10_diem - Copy\utils\calculate.py",
             "D:/Python Project/10_diem - Copy/data/financial/KQKD.csv", csv_file_path, ticker],
            capture_output=True, text=True, encoding='utf-8', check=True
        )
        print(f"✅ Tính toán thành công:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Lỗi khi chạy calculation.py:\n{e.stderr}")
        sys.exit(1)
    from tongquan import export_tongquan_to_csv
    export_tongquan_to_csv(ticker)

    csv_data = load_csv_data()
    company_info = get_company_info(ticker, csv_data)

    if company_info and csv_data:
        pdf_path = export_to_pdf(company_info, csv_data, "final_report.pdf", start_date, end_date)
        print(f"✅ PDF đã được tạo tại: {pdf_path}")
    else:
        print("⚠️ Không có dữ liệu để xuất PDF.")
generate_pdf_report()