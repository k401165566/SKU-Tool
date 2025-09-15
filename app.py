import streamlit as st
import pandas as pd
import pdfplumber

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
                    if "-" in line:  # 只抓 SKU 格式
                        skus.append(line.strip())

    df_pdf = pd.DataFrame({"SKU": skus})

    # ========== 讀取 Excel ==========
    df_map = pd.read_excel(excel_file, engine="openpyxl")

    # 標準化欄位名稱（去掉空格）
    df_map.columns = df_map.columns.str.strip()

    # 在畫面上顯示 Excel 的欄位名稱（方便檢查）
    st.write("Excel 欄位名稱：", df_map.columns.tolist())

    # 嘗試合併 (Excel 第一欄通常是「平臺SKU」)
    if "平臺SKU" in df_map.columns:
        df = df_pdf.merge(df_map, left_on="SKU", right_on="平臺SKU", how="left")
    else:
        st.error("❌ 找不到『平臺SKU』欄位，請確認 Excel 標題名稱")
        st.stop()

    # ========== 排序邏輯 ==========
    size_order = {"M": 1, "L": 2, "XL": 3, "2XL": 4, "3XL": 5,
                  "4XL": 6, "5XL": 7, "6XL": 8, "7XL": 9,
                  "8XL": 10, "9XL": 11, "10XL": 12}

    def size_key(x):
        return size_order.get(str(x), 999)

    color_order = {"黑": 1, "白": 2, "灰": 3, "藍": 4, "卡其": 5, "棕": 6}

    def color_key(x):
        for c in color_order:
            if str(x).startswith(c):
                return color_order[c]
        return 999

    if "自定義產品名稱" in df.columns:
        df["顏色"] = df["自定義產品名稱"].str.extract(r'(黑|白|灰|藍|卡其|棕)')
        df["尺寸"] = df["自定義產品名稱"].str.extract(r'([0-9]*XL|M|L)')

        df = df.sort_values(by=["顏色", "尺寸"],
                            key=lambda col: col.map(lambda x: color_key(x) if col.name == "顏色" else size_key(x)))

    # ========== 顯示 & 下載 ==========
    st.dataframe(df)

    # 輸出 Excel
    st.download_button(
        label="⬇ 下載結果 Excel",
        data=df.to_excel(index=False, engine="openpyxl"),
        file_name="result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
