import streamlit as st
import pandas as pd
import pdfplumber

st.title("📦 SKU 對照工具 (PDF → Excel)")

# 上傳 PDF
pdf_file = st.file_uploader("上傳 PDF (SKU 清單)", type="pdf")
# 上傳 Excel 對照表
excel_file = st.file_uploader("上傳 Excel (對照表)", type="xlsx")

if pdf_file and excel_file:
    # ===== 擷取 PDF SKU =====
    skus = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    if "-" in line:   # 簡單判斷 SKU 格式
                        skus.append(line.strip())

    df_pdf = pd.DataFrame({"SKU": skus})

    # ===== 讀取 Excel 對照表 =====
    df_map = pd.read_excel(excel_file)

    # ===== 合併 (注意 Excel 的欄位名是「平臺SKU」) =====
    df = df_pdf.merge(df_map, left_on="SKU", right_on="平臺SKU", how="left")

    # ===== 排序邏輯 =====
    size_order = {
        "M": 1, "L": 2, "XL": 3, "2XL": 4, "3XL": 5,
        "4XL": 6, "5XL": 7, "6XL": 8, "7XL": 9, "8XL": 10, "10XL": 11
    }
    color_order = {
        "黑": 1, "白": 2, "灰": 3, "藍": 4, "卡其": 5, "棕紅": 6
    }

    def size_key(x):
        for s in size_order:
            if s in str(x):
                return size_order[s]
        return 999

    def color_key(x):
        for c in color_order:
            if c in str(x):
                return color_order[c]
        return 999

    if "自定義產品名稱" in df.columns:
        df["顏色排序"] = df["自定義產品名稱"].apply(color_key)
        df["尺寸排序"] = df["自定義產品名稱"].apply(size_key)

        # 👉 先依顏色排序，再依尺寸排序
        df = df.sort_values(by=["顏色排序", "尺寸排序"]).drop(columns=["顏色排序", "尺寸排序"])

    # ===== 顯示結果 =====
    st.subheader("📊 對照後結果（已依顏色 + 尺寸分群排序）")
    st.dataframe(df)

    # 提供下載
    @st.cache_data
    def convert_df(df):
        return df.to_excel(index=False, engine="openpyxl")

    st.download_button(
        label="📥 下載 Excel",
        data=convert_df(df),
        file_name="SKU對照結果.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
