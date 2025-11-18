from vnstock import Company
import os
import pandas as pd

# Định nghĩa thư mục dữ liệu
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "financial")


def load_csv_data():
    data_frames = {}

    # Kiểm tra nếu thư mục không tồn tại -> báo lỗi rõ ràng
    if not os.path.exists(DATA_DIR):
        print(f"⚠️ LỖI: Thư mục dữ liệu không tồn tại: {DATA_DIR}")
        return {}

    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            file_path = os.path.join(DATA_DIR, file)
            try:
                df = pd.read_csv(file_path)
                data_frames[file] = df
                print(f"✅ Đã tải {file}")
            except Exception as e:
                print(f"⚠️ Lỗi khi tải {file}: {e}")

    return data_frames
def get_company_info(ticker, csv_data):
    """ Lấy thông tin doanh nghiệp từ Vnstock và bổ sung dữ liệu ngành ICB từ CSV """
    try:
        company = Company(ticker)

        # Lấy dữ liệu từ API
        overview = company.overview()
        profile = company.profile()

        history_raw = profile["history_dev"].values[0] if "history_dev" in profile else "Không có thông tin."
        history_list = history_raw.split(";")
        history_formatted = "<ul>" + "".join(f"<li>{event.strip()}</li>" for event in history_list if event.strip()) + "</ul>"

        strategy_raw = profile["business_strategies"].values[0] if "business_strategies" in profile else "Không có thông tin."
        strategy_list = strategy_raw.split(";")
        strategy_formatted = "<ul>" + "".join(f"<li>{event.strip()}</li>" for event in strategy_list if event.strip()) + "</ul>"

        # Mặc định giá trị N/A
        icb_level_1, icb_level_2, icb_level_3 = "N/A", "N/A", "N/A"

        # Tìm thông tin ngành ICB từ CSV (ví dụ từ BCTC.csv hoặc file chứa "Ngành ICB")
        for file_name, df in csv_data.items():
            if "Mã" in df.columns and "Ngành ICB - cấp 1" in df.columns:
                df["Mã"] = df["Mã"].astype(str).str.upper()
                row = df[df["Mã"] == ticker]
                if not row.empty:
                    print(f"✅ Dòng tìm thấy trong {file_name}:")
                    print(row[["Mã", "Ngành ICB - cấp 1", "Ngành ICB - cấp 2", "Ngành ICB - cấp 3"]].head())
                    icb_level_1 = row["Ngành ICB - cấp 1"].values[0] if "Ngành ICB - cấp 1" in row else "N/A"
                    icb_level_2 = row["Ngành ICB - cấp 2"].values[0] if "Ngành ICB - cấp 2" in row else "N/A"
                    icb_level_3 = row["Ngành ICB - cấp 3"].values[0] if "Ngành ICB - cấp 3" in row else "N/A"
                    print(f"✅ Đã tìm thấy dữ liệu ngành ICB trong {file_name}")
                    break

        company_info = {
            "Company Name": profile["company_name"].values[0] if "company_name" in profile else "N/A",
            "Mã CK": ticker,
            "Sàn niêm yết": overview["exchange"].values[0] if "exchange" in overview else "N/A",
            "Năm thành lập": overview["established_year"].values[0] if "established_year" in overview else "N/A",
            "Ngành ICB - Cấp 1": icb_level_1,
            "Ngành ICB - Cấp 2": icb_level_2,
            "Ngành ICB - Cấp 3": icb_level_3,
            "Trang web": overview["website"].values[0] if "website" in overview else "N/A",
            "Tóm tắt công ty": profile["company_profile"].values[0] if "company_profile" in profile else "Không có thông tin.",
            "Lịch sử phát triển": history_formatted if history_formatted else "<ul><li>Không có thông tin.</li></ul>",
            "Chiến lược kinh doanh": strategy_formatted if strategy_formatted else "<ul><li>Không có thông tin.</li></ul>"
        }

        return company_info
    except Exception as e:
        print(f"⚠️ Lỗi khi lấy dữ liệu từ Vnstock: {e}")
        return None

if __name__ == "__main__":
    csv_data = load_csv_data()
    ticker = input("Nhập mã cổ phiếu: ").upper()
    company_data = get_company_info(ticker, csv_data)

    print("\n✅ **Dữ liệu từ CSV:**")
    for file_name in csv_data.keys():
        print(f"- {file_name}")

    print("\n✅ **Thông tin công ty:**")
    for key, value in company_data.items():
        print(f"{key}: {value}")