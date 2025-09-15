import streamlit as st
import pandas as pd
import pdfplumber

st.title("📦 SKU 對照工具 (PDF ➝ Excel)")

# 上傳 PDF
pdf_file = st.file_uploader("上傳 PDF (SKU 清單)", type=["pdf"])
# 上傳 Excel 對照表
excel_file = st.file_uploader("上傳 Excel (對照表)", type=["xlsx"])

if pdf_file and excel_file:
    # 讀取 PDF
    skus = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    if "-" in line:  # 簡單判斷 SKU 格式
                        skus.append(line.strip())

    df_pdf = pd.DataFrame({"SKU": skus})

    # 讀取對照表
    df_map = pd.read_excel(excel_file)

    # 合併
    df = df_pdf.merge(df_map, on="SKU", how="left")

    # ========= 排序邏輯 =========
    size_order = {"M": 1, "L": 2, "XL": 3, "2XL": 4, "3XL": 5, "4XL": 6,
                  "5XL": 7, "6XL": 8, "7XL": 9, "8XL": 10, "9XL": 11, "10XL": 12}
    def size_key(x):
        return size_order.get(str(x), 999)

    color_order = {"黑": 1, "白": 2, "灰": 3, "藍": 4, "卡": 5, "棕": 6}
    def color_key(x):
        return color_order.get(str(x), 999)

    product_order = ["TA00", "TA01", "TA03", "TB00", "TB103"]
    def product_key(x):
        for i, p in enumerate(product_order):
            if str(x).startswith(p):
                return i
        return 999

    if "名稱" in df.columns:
        # 拆出 商品 / 顏色 / 尺寸
        df["商品名稱"] = df["名稱"].str.extract(r"(^[A-Z]+\d+)")
        df["顏色"] = df["名稱"].str.extract(r"(黑|白|灰|藍|卡|棕)")
        df["尺寸"] = df["名稱"].str.extract(r"(M|L|XL|2XL|3XL|4XL|5XL|6XL|7XL|8XL|9XL|10XL)")

        df = df.sort_values(
            by=["商品名稱", "顏色", "尺寸"],
            key=lambda col: (
                col.map(product_key) if col.name == "商品名稱" else
                col.map(color_key) if col.name == "顏色" else
                col.map(size_key)
            )
        )

    # ========= 排序結束 =========

    # 下載結果
    st.dataframe(df)

    @st.cache_data
    def convert_excel(df):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button(
        label="📥 下載 Excel",
        data=convert_excel(df),
        file_name="result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
