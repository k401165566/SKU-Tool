import streamlit as st
import pandas as pd
import pdfplumber

st.title("📦 SKU 對照工具 (PDF → Excel)")

# 上傳 PDF
pdf_file = st.file_uploader("上傳 PDF (SKU 清單)", type="pdf")
# 上傳 Excel 對照表
excel_file = st.file_uploader("上傳 Excel (對照表)", type="xlsx")

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
    size_order = {
        "M": 1, "L": 2, "XL": 3, "2XL": 4, "3XL": 5, "4XL": 6,
        "5XL": 7, "6XL": 8, "7XL": 9, "8XL": 10, "9XL": 11, "10XL": 12
    }

    def size_key(x):
        return size_order.get(str(x), 999)

    color_order = {"黑": 1, "白": 2, "灰": 3, "藍": 4, "紅": 5, "綠": 6}

    def color_key(x):
        return color_order.get(str(x), 999)

    if "顏色" in df.columns and "尺寸" in df.columns:
        df = df.sort_values(
            by=["顏色", "尺寸"],
            key=lambda col: col.map(
                lambda x: color_key(x) if col.name == "顏色" else size_key(x)
            )
        )

    # 顯示表格
    st.dataframe(df)

    # 下載結果
    @st.cache_data
    def convert_df(df):
        return df.to_excel(index=False, engine="openpyxl")

    st.download_button(
        label="📥 下載 Excel",
        data=convert_df(df),
        file_name="sku_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
