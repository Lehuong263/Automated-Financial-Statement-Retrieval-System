from vnstock import Company
from weasyprint import HTML
import os

def get_company_info(ticker):
    """ Lấy thông tin doanh nghiệp từ Vnstock"""
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

        company_info = {
            "Company Name": profile["company_name"].values[0] if "company_name" in profile else "N/A",
            "Mã CK": ticker,
            "Sàn niêm yết": overview["exchange"].values[0] if "exchange" in overview else "N/A",
            "Năm thành lập": overview["established_year"].values[0] if "established_year" in overview else "N/A",
            "Trang web": overview["website"].values[0] if "website" in overview else "N/A",
            "Tóm tắt công ty": profile["company_profile"].values[0] if "company_profile" in profile else "Không có thông tin.",
            "Lịch sử phát triển": history_formatted if history_formatted else "<ul><li>Không có thông tin.</li></ul>",
            "Chiến lược kinh doanh": strategy_formatted if strategy_formatted else "<ul><li>Không có thông tin.</li></ul>"
        }

        return company_info
    except Exception as e:
        print(f"⚠️ Lỗi khi lấy dữ liệu: {e}")
        return None

def export_to_pdf(company_data, filename="company_info.pdf"):
    """ Xuất thông tin công ty ra PDF với WeasyPrint """
    html_template = f"""
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        
            body {{
                font-family: 'Roboto', sans-serif;
                font-size: 14px;  /* Tăng kích thước font chữ nội dung lên một chút */
                padding: 10px;
                background-color: #f4f4f4;
            }}
            .container {{
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                color: #004080;
                text-align: right;
                font-size: 18px; /* Tiêu đề giữ nguyên */
                border-bottom: 2px solid #004080;
                padding-bottom: 6px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 8px 0;
            }}
            th, td {{
                border: 1px;
                padding: 6px;
                text-align: left;
                font-size: 12px;  /* Tăng kích thước nội dung */
            }}
            th {{
                background-color: #004080;
                color: white;
                font-size: 14px;  /* Tiêu đề giữ nguyên */
            }}
            tr {{
                border-bottom: 1px solid #cccccc; /* Viền mỏng giữa các dòng */
            }}
            tr:nth-child(even) {{
                background-color: #e0e0e0; /* Dòng chẵn có nền xám nhạt */
            }}
            .summary h2 {{
                font-size: 14px;
                background-color: #004080;
                color: white;
                padding: 5px;
                border-radius: 4px;
                margin-bottom: 4px;
            }}
            p, ul {{
                margin: 3px 0;
                padding-left: 12px;
                font-size: 12px;  /* Tăng kích thước nội dung */
                text-align: justify;
                line-height: 1.4;
            }}
            .small-title {{
                font-size: 14px;
                font-weight: bold;
                color: #004080;
                text-transform: uppercase;
                margin-top: 6px;
            }}
            .two-columns {{
                display: flex;
                justify-content: space-between;
            }}
            .column {{
                width: 48%;
            }}
        </style>

    </head>
    <body>
        <div class="container">
            <h1>{filename.replace(".pdf", "").replace("_", " ")}</h1>

            <div class="two-columns">
                <div class="column">
                    <table>
                        <tr>
                            <th colspan="2">THÔNG TIN CHUNG</th>
                        </tr>
                        <tr>
                            <td><strong>Tên công ty</strong></td>
                            <td>{company_data.get("Company Name", "N/A")}</td>
                        </tr>
                        <tr>
                            <td><strong>Mã chứng khoán</strong></td>
                            <td>{company_data.get("Mã CK", "N/A")}</td>
                        </tr>
                        <tr>
                            <td><strong>Sàn niêm yết</strong></td>
                            <td>{company_data.get("Sàn niêm yết", "N/A")}</td>
                        </tr>
                        <tr>
                            <td><strong>Năm thành lập</strong></td>
                            <td>{company_data.get("Năm thành lập", "N/A")}</td>
                        </tr>
                    </table>
                </div>

                <div class="column">
                    <table>
                        <tr>
                            <th colspan="2">THÔNG TIN DOANH NGHIỆP</th>
                        </tr>
                        <tr>
                            <td><strong>Ngành ICB - Cấp 1</strong></td>
                            <td>{company_data.get("Ngành ICB - Cấp 1", "N/A")}</td>
                        </tr>
                        <tr>
                            <td><strong>Ngành ICB - Cấp 2</strong></td>
                            <td>{company_data.get("Ngành ICB - Cấp 2", "N/A")}</td>
                        </tr>
                        <tr>
                            <td><strong>Ngành ICB - Cấp 3</strong></td>
                            <td>{company_data.get("Ngành ICB - Cấp 3", "N/A")}</td>
                        </tr>
                        <tr>
                            <td><strong>Trang web</strong></td>
                            <td><a href="{company_data.get('Trang web', '#')}" style="color: blue; text-decoration: none;">
                                {company_data.get("Trang web", "N/A")}</a></td>
                        </tr>
                    </table>
                </div>
            </div>

            <div class="summary">
                <h2 class="small-title">Tóm tắt công ty</h2>
                <p>{company_data.get("Tóm tắt công ty", "Không có thông tin.")}</p>
            </div>

            <div class="summary">
                <h2 class="small-title">Lịch sử phát triển</h2>
                {company_data.get("Lịch sử phát triển", "<p>Không có thông tin.</p>")}
            </div>

            <div class="summary">
                <h2 class="small-title">Chiến lược kinh doanh</h2>
                {company_data.get("Chiến lược kinh doanh", "<p>Không có thông tin.</p>")}
            </div>
        </div>
    </body>
    </html>
    """

    output_path = os.path.join("reports", filename)
    HTML(string=html_template).write_pdf(output_path)
    print(f"✅ PDF đã được lưu tại: {output_path}")

if __name__ == "__main__":
    ticker = input("Nhập mã cổ phiếu: ").upper()
    company_data = get_company_info(ticker)

    if company_data:
        export_to_pdf(company_data, f"Company_Info_{ticker}.pdf")
    else:
        print("⚠️ Không có dữ liệu.")
