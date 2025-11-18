import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import sys

# === SETUP CHROME DRIVER ===
CHROMEDRIVER_PATH = r"C:\browser_drivers\chromedriver\chromedriver.exe"
options = Options()
options.add_argument('--headless')  # Bỏ dòng này nếu muốn xem trình duyệt chạy
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(service=ChromeService(CHROMEDRIVER_PATH), options=options)

# === HÀM TIỆN ÍCH ===
def get_elements_value(items):
    result = []
    for x in items:
        val = x.text.strip().replace(',', '')
        if val.replace('.', '', 1).isdigit():
            result.append(float(val))
        else:
            result.append(val)
    return result

def year_col_process(driver, col):
    xpath = f"//*[@id='tableContent']/tbody/tr/td[{col}]"
    return driver.find_elements(By.XPATH, xpath)

def get_report_url(ticker, year):
    return f"https://s.cafef.vn/bao-cao-tai-chinh/{ticker}/BSheet/{year}/0/0/0/bao-cao-tai-chinh-cong-ty.chn"

def get_bs_data(driver, ticker, from_year, to_year):
    year = to_year
    data = {}
    criteria_names = {}
    run = True

    while run:
        url = get_report_url(ticker, year)
        print(f"🔗 {ticker} - Truy cập: {url}")
        driver.get(url)
        time.sleep(2)

        # Lấy tên chỉ tiêu (1 lần duy nhất)
        if 'criteria' not in criteria_names:
            names = year_col_process(driver, 1)
            criteria_names['Chỉ tiêu'] = get_elements_value(names)

        # Lấy các cột theo năm
        year_cells = driver.find_elements(By.XPATH, "//*[@id='tblGridData']/tbody/tr/td")
        index_cols = {}
        i = 1
        for item in year_cells:
            txt = item.text.strip()
            if txt.isnumeric():
                index_cols[txt] = i
            i += 1

        index_cols = dict(sorted(index_cols.items(), reverse=True))
        y = 0
        for key in index_cols:
            col = index_cols[key]
            items = year_col_process(driver, col)
            data[key] = get_elements_value(items)
            print(f"📊 Năm: {key}")
            y = int(key)
            if y == from_year:
                run = False
                break
        year = y - 1

    data = dict(sorted(data.items()))
    merged = criteria_names | data
    return pd.DataFrame(merged)

# === LẤY MÃ CỔ PHIẾU TỪ THAM SỐ DÒNG LỆNH ===
if len(sys.argv) > 1:
    ticker = sys.argv[1]  # Nhận mã cổ phiếu từ tham số dòng lệnh
else:
    ticker = "POW"  # Mã mặc định nếu không có tham số

# === ĐỌC DANH SÁCH MÃ ===
FROM_YEAR = 2019
TO_YEAR = 2024

# === CÀO DỮ LIỆU TỪNG MÃ ===
try:
    print(f"\n🚀 Đang xử lý: {ticker}")
    df = get_bs_data(driver, ticker, FROM_YEAR, TO_YEAR)
    filename = f"D:/Python Project/10_diem - Copy/data/bs_them/{ticker}_BS_{FROM_YEAR}_{TO_YEAR}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"✅ Đã lưu: {filename}")
except Exception as e:
    print(f"❌ Lỗi với {ticker}: {e}")

# === ĐÓNG TRÌNH DUYỆT ===
driver.quit()
