import streamlit as st
import streamlit.components.v1 as components
from utils.data_loader import load_csv_data, get_company_info
from utils.pdf_exporter import export_to_pdf
from jinja2 import Environment, FileSystemLoader
import os

# Khởi tạo Jinja2
template_dir = os.path.join(os.getcwd(), "templates")
env = Environment(loader=FileSystemLoader(template_dir))

st.set_page_config(page_title="BÁO CÁO TỔNG HỢP", layout="wide")
st.title("📊 BÁO CÁO TỔNG HỢP")

# --- Load dữ liệu CSV mỗi lần (có thể cache nếu lớn) ---
csv_data = load_csv_data()

# --- Giao diện nhập mã cổ phiếu ---
ticker = st.text_input("🔍 Nhập mã cổ phiếu:", value="AAA").strip().upper()

# --- Tạo biến session_state để lưu dữ liệu sau khi "Lấy thông tin" ---
if "company_info" not in st.session_state:
    st.session_state.company_info = None
if "ticker" not in st.session_state:
    st.session_state.ticker = None

# --- Nút lấy dữ liệu từ Vnstock ---
if st.button("Lấy thông tin"):
    with st.spinner("⏳ Đang lấy dữ liệu từ Vnstock..."):
        company_info = get_company_info(ticker, csv_data)

    if company_info:
        st.session_state.company_info = company_info
        st.session_state.ticker = ticker
    else:
        st.warning("⚠️ Không tìm thấy dữ liệu cho mã này.")

# --- Nếu đã có dữ liệu lưu từ session ---
if st.session_state.company_info:
    # Render template HTML bằng Jinja2
    template = env.get_template("streamlit_template.html")
    html = template.render(company=st.session_state.company_info, data=csv_data, ticker=st.session_state.ticker)

    # Hiển thị HTML đẹp
    components.html(html, height=1200, scrolling=True)

    # Nút xuất PDF
    if st.button("📄 Xuất PDF"):
        filename = f"report_{st.session_state.ticker}.pdf"
        pdf_path = export_to_pdf(st.session_state.company_info, csv_data, filename)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Tải PDF", f, file_name=filename, mime="application/pdf")
