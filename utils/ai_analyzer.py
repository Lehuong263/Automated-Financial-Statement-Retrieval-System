import os
import pandas as pd
import re
from dotenv import load_dotenv
import google.generativeai as genai
# === Load API key ===
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.0-flash")

# === Basic Call + Formatting ===
def call_gemini(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Gemini error: {e}"

def clean_text(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def wrap_brief(title: str, text: str) -> str:
    html_text = text.replace("\n", "<br>")
    return f"""
    <div style="background: #f5f9fe; padding: 12px 16px; border-left: 4px solid #1a73e8; margin-top: 8px; border-radius: 6px; font-size: 13px;">
      <strong>{title}</strong><br>
      {html_text}
    </div>
    """

# === Static prompt templates ===
PROMPT_TEMPLATE_STATIC = {
    "balance_analysis": """Hãy phân tích biểu đồ sau về Cấu trúc tài sản của Công ty Masan (MSN), bao gồm:

- Tỷ lệ Nợ/Vốn chủ sở hữu (Nợ/VCSH)
- Tỷ lệ Vay (ngắn hạn + dài hạn) / Vốn chủ sở hữu (Vay/VCSH)

Dữ liệu từ năm 2020 đến 2024 đã được cung cấp trong biểu đồ.  
Yêu cầu:
- Nêu rõ xu hướng chính của tỷ lệ nợ và vay
- Đánh giá rủi ro tài chính nếu có
- Gợi ý nếu tỷ lệ đòn bẩy cao hay đang giảm dần
- Viết ngắn gọn trong 100-150 từ, chuyên nghiệp, có số liệu
""",
    "income_analysis": """Hãy phân tích biểu đồ Lãi và Lỗ của Công ty Masan (MSN), thể hiện:

- Doanh thu thuần
- Lợi nhuận từ hoạt động kinh doanh
- Lợi nhuận sau thuế
- Biên lợi nhuận thuần (%)

Từ năm 2020 đến 2024.  
Yêu cầu:
- Nhận xét xu hướng doanh thu, lợi nhuận, và biên lợi nhuận
- Phát hiện bất thường nếu có (lợi nhuận giảm dù doanh thu tăng,…)
- Nhận xét về hiệu quả hoạt động
- Viết ngắn gọn trong 150 từ, số liệu cụ thể, chuyên nghiệp
""",
    "cashflow_analysis": """Phân tích biểu đồ Lưu chuyển tiền tệ của Công ty Masan (MSN), bao gồm:

- Dòng tiền từ hoạt động kinh doanh (CFO)
- Dòng tiền đầu tư (CFI)
- Dòng tiền tài chính (CFF)
- Tiền và tương đương cuối kỳ

Từ năm 2020 đến 2024.  
Yêu cầu:
- Nhận xét dòng tiền hoạt động có ổn định không
- Dòng tiền đầu tư lớn có phải mở rộng?
- Dòng tiền tài chính có đang trả nợ hay vay thêm?
- Đánh giá khả năng tạo tiền thật từ hoạt động cốt lõi
- Giới hạn 150 từ, ngắn gọn, có số liệu
"""
}

# === Dynamic prompt generation from CSV ===
def generate_structure_prompt(df, ticker):
    df = df[df["Mã"] == ticker]
    if df.empty: return None
    ts = df.set_index("Năm")["TỔNG CỘNG TÀI SẢN"].to_dict()
    vcs = df.set_index("Năm")["VỐN CHỦ SỞ HỮU"].to_dict()
    no = df.set_index("Năm")["NỢ PHẢI TRẢ"].to_dict()
    tsn = df.set_index("Năm")["TÀI SẢN NGẮN HẠN"].to_dict()
    ptn = df.set_index("Năm")["Các khoản phải thu ngắn hạn"].to_dict()
    htk = df.set_index("Năm")["Hàng tồn kho, ròng"].to_dict()
    no_ngan = df.set_index("Năm")["Nợ ngắn hạn"].to_dict()
    vay = (df["Vay và nợ thuê tài chính ngắn hạn"] + df["Vay và nợ thuê tài chính dài hạn"]).tolist()
    vay_dict = dict(zip(df["Năm"], vay))
    return f"""
Phân tích cấu trúc tài sản của công ty {ticker.upper()} dựa trên:

- Tổng tài sản (tỷ VND): {ts}
- Vốn chủ sở hữu (tỷ VND): {vcs}
- Nợ phải trả (tỷ VND): {no}
- Tài sản ngắn hạn: {tsn}
- Khoản phải thu ngắn hạn: {ptn}
- Hàng tồn kho: {htk}
- Nợ ngắn hạn: {no_ngan}
- Tổng vay (ngắn + dài hạn): {vay_dict}

Yêu cầu:
- Phân tích xu hướng đòn bẩy tài chính (Nợ/VCSH, Vay/VCSH)
- Xem xét tăng trưởng tài sản có tương xứng với doanh thu không (tham khảo nếu cần)
- Phân tích các khoản phải thu, hàng tồn kho và nợ ngắn hạn nếu biến động lớn (nếu cần phải quan tâm, không thì bỏ qua)
- Viết chuyên nghiệp, giới hạn 150 từ
"""

def generate_income_prompt(df, ticker):
    df = df[df["Mã"] == ticker]
    if df.empty: return None
    dt = df.set_index("Năm")["Doanh thu bán hàng và cung cấp dịch vụ"].to_dict()
    lnkd = df.set_index("Năm")["Lợi nhuận thuần từ hoạt động kinh doanh"].to_dict()
    lnst = df.set_index("Năm")["Lợi nhuận sau thuế thu nhập doanh nghiệp"].to_dict()
    return f"""
Phân tích hiệu quả kinh doanh của công ty {ticker.upper()}:

- Doanh thu (tỷ VND): {dt}
- Lợi nhuận hoạt động kinh doanh (tỷ VND): {lnkd}
- Lợi nhuận sau thuế (tỷ VND): {lnst}

Yêu cầu:
- Nhận xét xu hướng doanh thu và lợi nhuận
- Phân tích hiệu quả hoạt động
- Ghi nhận bất thường nếu có
- Viết ngắn gọn, tối đa 150 từ, có số liệu
"""

def generate_cashflow_prompt(df, ticker):
    df = df[df["Mã"] == ticker]
    if df.empty: return None
    df = df.rename(columns={
        "Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh (TT)": "CFO",
        "Lưu chuyển tiền tệ ròng từ hoạt động đầu tư (TT)": "CFI",
        "Lưu chuyển tiền tệ từ hoạt động tài chính (TT)": "CFF",
        "Tiền và tương đương tiền cuối kỳ (TT)": "Cash"
    })
    cfo = df.set_index("Năm")["CFO"].to_dict()
    cfi = df.set_index("Năm")["CFI"].to_dict()
    cff = df.set_index("Năm")["CFF"].to_dict()
    cash = df.set_index("Năm")["Cash"].to_dict()
    return f"""
Phân tích dòng tiền của công ty {ticker.upper()} với dữ liệu:

- Dòng tiền hoạt động (CFO): {cfo}
- Dòng tiền đầu tư (CFI): {cfi}
- Dòng tiền tài chính (CFF): {cff}
- Tiền cuối kỳ: {cash}

Yêu cầu:
- Nhận xét khả năng tạo dòng tiền từ hoạt động
- Đánh giá hoạt động đầu tư, tài chính
- Viết chuyên nghiệp, ngắn gọn 100-150 từ
"""

# === Combined prompt generator ===
def generate_combined_prompt(part: str, prompt_static: str, prompt_data: str | None) -> str:
    if not prompt_data:
        return prompt_static.strip()

    return f"""
Hãy kết hợp cả dữ liệu và biểu đồ dưới đây để đưa ra một phân tích ngắn gọn, tối đa 150 từ.

--- Biểu đồ: ---
{prompt_static.strip()}

--- Dữ liệu thực tế: ---
{prompt_data.strip()}

Yêu cầu:
- Viết chuyên nghiệp, không văn nói
- Phân tích ngắn gọn, rõ ý, có số liệu minh họa
- Nhận xét điểm mạnh, điểm yếu và xu hướng chính
"""

def generate_combined_section_analysis(ticker, bcdkt_df, kqkd_df, lctt_df) -> dict:
    prompt_data_parts = {
        "balance_analysis": generate_structure_prompt(bcdkt_df, ticker),
        "income_analysis": generate_income_prompt(kqkd_df, ticker),
        "cashflow_analysis": generate_cashflow_prompt(lctt_df, ticker)
    }

    results = {}
    for key in ["balance_analysis", "income_analysis", "cashflow_analysis"]:
        static = PROMPT_TEMPLATE_STATIC[key]
        data_part = prompt_data_parts[key]
        full_prompt = generate_combined_prompt(key, static, data_part)

        raw = call_gemini(full_prompt)
        cleaned = clean_text(raw)
        results[key] = wrap_brief("📌 Nhận xét", cleaned)

    return results
def load_full_ratios_by_ticker(ticker: str) -> pd.DataFrame:
    path_all = r"D:/Python Project/10_diem - Copy/data/financial/financial_ratios.csv"
    path_ticker = fr"D:/Python Project/10_diem - Copy/data/calculate/{ticker}_financial_ratios.csv"
    df1, df2 = pd.DataFrame(), pd.DataFrame()
    try: df1 = pd.read_csv(path_all)
    except: pass
    try: df2 = pd.read_csv(path_ticker)
    except: pass
    df = pd.concat([df1, df2], ignore_index=True)
    if "Mã" in df.columns:
        df = df[df["Mã"] == ticker]

    df.drop(columns=["Mã"], errors="ignore", inplace=True)
    df.set_index("Chỉ số", inplace=True)

    return df
def generate_return_ratio_analysis(ticker: str) -> str:
    df = load_full_ratios_by_ticker(ticker)
    if df.empty:
        return wrap_brief("📌 Phân tích ROE, ROA, ROIC", "Không có dữ liệu.")
    try:
        roe = df.loc["ROE (%)"].round(1).to_dict()
        roa = df.loc["ROA (%)"].round(1).to_dict()
        roic = df.loc["ROIC (%)"].round(1).to_dict()
    except KeyError as e:
        return wrap_brief("📌 Phân tích ROE, ROA, ROIC", f"Dữ liệu thiếu: {e}")

    prompt = f"""
Bạn là chuyên gia tài chính. Phân tích hiệu quả sinh lời của công ty {ticker.upper()} từ 2020–2024 qua các chỉ số:

- ROE (%): {roe}
- ROA (%): {roa}
- ROIC (%): {roic}
   
Yêu cầu:
- Có nhìn vào biểu đồ để phân tích
- Viết nhận xét ngắn gọn, chuyên nghiệp (50-100 từ)
- Nhấn mạnh xu hướng: tăng/giảm bền vững hay đột biến
- ROE có vượt xa ROA không? → dùng đòn bẩy nhiều?
- ROIC có cao hơn chi phí vốn không?
- Nếu ROIC > chi phí vốn → công ty tạo giá trị thực
- Kết luận: hiệu quả tạo giá trị cho cổ đông/công ty
- Không lặp lại số liệu quá nhiều, tập trung vào ý nghĩa
 ** Giới hạn bắt buộc: **
    - Tối đa 110 từ

"""
    raw = call_gemini(prompt)
    return wrap_brief("📌 Phân tích ROE, ROA, ROIC", clean_text(raw))

def generate_activity_analysis(ticker: str) -> str:
    df = load_full_ratios_by_ticker(ticker)
    if df.empty:
        return wrap_brief("📌 Nhận xét chỉ số hoạt động", "Không có dữ liệu.")

    try:
        # df đã set_index("Chỉ số") rồi, nên truy cập trực tiếp
        data = {
            "Số ngày thu tiền": df.loc["Số ngày thu tiền bình quân"].round(1).to_dict(),
            "Số ngày tồn kho": df.loc["Số ngày tồn kho bình quân"].round(1).to_dict(),
            "Số ngày thanh toán": df.loc["Số ngày thanh toán bình quân"].round(1).to_dict(),
            "Chu kỳ tiền": df.loc["Chu kỳ tiền"].round(1).to_dict()
        }
    except KeyError as e:
        return wrap_brief("📌 Hiệu suất hoạt động", f"Dữ liệu thiếu: {e}")

    prompt = f'''
Bạn là chuyên gia tài chính. Dưới đây là các chỉ số hoạt động của công ty {ticker.upper()} từ 2020–2024:

- Số ngày thu tiền
- Số ngày tồn kho
- Số ngày thanh toán
- Chu kỳ tiền

Dữ liệu: {data}

Yêu cầu:
- Phân tích xu hướng từng chỉ số và ảnh hưởng đến chu kỳ tiền
- Đánh giá hiệu quả vận hành: khả năng thu hồi vốn, tồn kho, thanh toán
- Chu kỳ tiền = Thu tiền + Tồn kho - Thanh toán chứ không phải chu kỳ tiền mặt
- Nhận định liệu doanh nghiệp có đang cải thiện hiệu quả dòng tiền, hay đang có dấu hiệu kém hiệu quả
- Phân tích có so sánh giữa các năm, chỉ ra điểm bất thường nếu có
- Viết dưới dạng nhận xét chuyên nghiệp, rõ ràng
- Không lặp lại số liệu quá nhiều, tập trung vào ý nghĩa
- Đánh giá xu hướng cải thiện hay rủi ro
 ** Giới hạn bắt buộc: **
    - Tối đa 110 từ

'''
    raw = call_gemini(prompt)
    return wrap_brief("📌 Nhận xét chỉ số hoạt động", clean_text(raw))


def generate_dupont_analysis(ticker: str) -> str:
    df = load_full_ratios_by_ticker(ticker)
    if df.empty:
        return wrap_brief("📌 Nhận xét Dupont", "Không có dữ liệu.")

    try:
        data = {
            "ROE (%)": df.loc["ROE (%)"].round(1).to_dict(),
            "Biên lợi nhuận ròng (%)": df.loc["Biên lợi nhuận ròng (%)"].round(1).to_dict(),
            "Vòng quay tài sản": df.loc["Vòng quay tài sản"].round(2).to_dict(),
            "Đòn bẩy tài chính": df.loc["Đòn bẩy tài chính"].round(2).to_dict()
        }
    except KeyError as e:
        return wrap_brief("📌 Phân tích Dupont", f"Dữ liệu thiếu: {e}")

    prompt = f'''
Phân tích ROE theo mô hình Dupont cho công ty {ticker.upper()} giai đoạn 2020–2024:

- ROE (%)
- Biên lợi nhuận ròng
- Vòng quay tài sản
- Đòn bẩy tài chính
-Dữ liệu: {data}

Yêu cầu:
- Có nhìn vào biểu đồ để phân tích
- Viết 50-100 từ, chuyên nghiệp
- Diễn giải ROE được tạo bởi yếu tố nào mạnh nhất
- Có đang phụ thuộc vào đòn bẩy hay vận hành tốt?
- Không lặp lại số liệu quá nhiều, tập trung vào ý nghĩa
 ** Giới hạn bắt buộc: **
    - Tối đa 110 từ

'''
    raw = call_gemini(prompt)
    return wrap_brief("📌 Nhận xét Dupont", clean_text(raw))


def generate_profit_analysis(ticker: str) -> str:
    df = load_full_ratios_by_ticker(ticker)
    if df.empty:
        return wrap_brief("📌 Phân tích lợi nhuận", "Không có dữ liệu.")

    try:
        gpm = df.loc["Biên lợi nhuận gộp (%)"].round(1).to_dict()
        ebit = df.loc["Biên EBIT (%)"].round(1).to_dict()
        npm = df.loc["Biên lợi nhuận ròng (%)"].round(1).to_dict()
    except KeyError as e:
        return wrap_brief("📌 Phân tích lợi nhuận", f"Dữ liệu thiếu: {e}")

    prompt = f'''
Phân tích lợi nhuận của công ty {ticker.upper()} từ 2020 đến 2024 qua các chỉ số:
- lợi nhuận ròng
- Biên lợi nhuận gộp (%): {gpm}
- Biên EBIT (%): {ebit}
- Biên lợi nhuận ròng (%): {npm}

Yêu cầu:
- Có nhìn vào biểu đồ để phân tích
- Viết ngắn gọn (50-100từ), rõ ràng, ngôn ngữ chuyên nghiệp
- Phân tích xu hướng tăng trưởng lợi nhuận và hiệu quả hoạt động
- Đánh giá biên LN cải thiện có hợp lý không
- Có yếu tố nào cần lưu ý (biên LN ròng tăng nhưng EBIT chững lại…)
- Không lặp lại số liệu quá nhiều, tập trung vào ý nghĩa
 ** Giới hạn bắt buộc: **
    - Tối đa 110 từ
 - Giọng điệu chuyên nghiệp, tránh từ thừa thãi của các công cụ
'''
    raw = call_gemini(prompt)
    return wrap_brief("📌 Phân tích lợi nhuận", clean_text(raw))


def generate_final_conclusion_with_ai(ticker, bcdkt_df, kqkd_df, lctt_df):
    sections = generate_combined_section_analysis(ticker, bcdkt_df, kqkd_df, lctt_df)
    roe = generate_return_ratio_analysis(ticker)
    dupont = generate_dupont_analysis(ticker)
    activity = generate_activity_analysis(ticker)
    profit = generate_profit_analysis(ticker)

    # Ghép các phần lại làm prompt
    prompt = f"""
    {sections["balance_analysis"]}
    {sections["income_analysis"]}
    {sections["cashflow_analysis"]}
    {roe}
    {dupont}
    {profit}
    {activity}

Bây giờ bạn là chuyên gia phân tích tài chính. Hãy viết phần KẾT LUẬN báo cáo như hướng dẫn:
Dựa trên toàn bộ các phân tích trước đó bao gồm:
Phân tích báo cáo tài chính (cân đối kế toán, kết quả kinh doanh, lưu chuyển tiền tệ)
Hiệu quả sử dụng vốn (ROE, ROA, Dupont)
Khả năng sinh lời (biên lợi nhuận gộp, biên lợi nhuận ròng)
Hiệu suất hoạt động (vòng quay tài sản, quản lý hàng tồn kho, công nợ)
Phân tích kỹ thuật cơ bản (xu hướng giá, đường trung bình, kháng cự/hỗ trợ)
Phân tích ngành & vị thế doanh nghiệp
Nếu dữ liệu thiếu, hãy đề cập một cách khéo léo và vẫn đưa ra gợi ý.
    Dựa trên toàn bộ các phân tích trên, viết một đoạn KẾT LUẬN khoảng 500 chữ bao gồm:
    - Tóm tắt nhanh tình hình tài chính hiện tại của doanh nghiệp
    - Nhận định điểm mạnh, rủi ro
    - Khuyến nghị hành động: NÊN MUA / NẮM GIỮ / THEO DÕI / KHÔNG KHUYẾN NGHỊ
    - Văn phong rõ ràng, chuyên nghiệp, logic
    - Sử dụng ngôi thứ ba (Doanh nghiệp này... / Nhà đầu tư nên...).
    - Giới hạn bắt buộc : 500 chữ
    - Đừng có để dấu ** này nhìn rất mất thẩm mỹ
    """

    response = model.generate_content(prompt)
    response_text = response.text.strip()

    # 👇 Hậu xử lý HTML nếu AI không trả đúng format <p>
    if "<p>" not in response_text:
        paragraphs = [f"<p>{p.strip()}</p>" for p in response_text.split("\n") if p.strip()]
        response_text = "\n".join(paragraphs)

    return response_text
