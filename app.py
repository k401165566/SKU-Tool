import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO

st.title("📦 SKU 對照工具 (PDF ➝ Excel)")

# 上傳 PDF
pdf_file = st.file_uploader("上傳 PDF (SKU 清單)", type="pdf")

# 上傳 Excel 對照表
excel_file = st.file_uploader("上傳 Excel (對照表)", type="xlsx")

if pdf_file and excel_file:
    # ========== 讀取 PDF ==========
    skus = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    if "-" in line:  # 抓 SKU 格式
                        skus.append(line.strip())

    df_pdf = pd.DataFrame({"SKU": skus})

    # ========== 讀取 Excel ==========
    df_map = pd.read_excel(excel_file, engine="openpyxl")
    df_map.columns = df_map.columns.str.strip()  # 去掉多餘空格
    st.write("Excel 欄位名稱：", df_map.columns.tolist())

    # ✅ 確認欄位
    if "平臺 SKU" not in df_map.columns or "自定義產品名稱" not in df_map.columns:
        st.error("❌ Excel 必須包含『平臺 SKU』與『自定義產品名稱』欄位")
        st.stop()

    # 合併
    df = df_pdf.merge(df_map, left_on="SKU", right_on="平臺 SKU", how="left")

    # ========== 拆顏色 + 尺寸 ==========
    df["顏色"] = df["自定義產品名稱"].str.extract(r'(黑|白|灰|藍|卡其|棕)')
    df["尺寸"] = df["自定義產品名稱"].str.extract(r'([0-9]*XL|M|L)')

    # ========== 排序邏輯 ==========
    size_order = {"M": 1, "L": 2, "XL": 3, "2XL": 4, "3XL": 5,
                  "4XL": 6, "5XL": 7, "6XL": 8, "7XL": 9,
                  "8XL": 10, "9XL": 11, "10XL": 12}

    color_order = {"黑": 1, "白": 2, "灰": 3, "藍": 4, "卡其": 5, "棕": 6}

    def size_key(x):
        return size_order.get(str(x), 999)

    def color_key(x):
        return color_order.get(str(x), 999)

    df = df.sort_values(
        by=["顏色", "尺寸"],
        key=lambda col: col.map(lambda x: color_key(x) if col.name == "顏色" else size_key(x))
    )

    # ========== 分群顯示 ==========
    for color in df["顏色"].dropna().unique():
        st.subheader(f"🎨 {color}")
        st.dataframe(df[df["顏色"] == color][["SKU", "自定義產品名稱", "顏色", "尺寸"]])

    # ========== 下載 ==========
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    st.download_button(
        label="⬇ 下載結果 Excel",
        data=output.getvalue(),
        file_name="result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
