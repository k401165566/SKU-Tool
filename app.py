import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
from io import BytesIO

st.title("📦 SKU 對照工具 (PDF → Excel)")

# 上傳檔案
pdf_file = st.file_uploader("上傳 PDF (SKU 清單)", type=["pdf"])
excel_file = st.file_uploader("上傳 Excel (對照表)", type=["xlsx"])

# 尺寸排序順序
size_order = ["M","L","XL","2XL","3XL","4XL","5XL","6XL","7XL","8XL","9XL","10XL"]
size_priority = {s: i for i, s in enumerate(size_order)}

# 商品排序優先
product_priority = ["TA00", "TA01", "TA03", "TB00", "TB103"]
def product_key(name):
    for i, p in enumerate(product_priority):
        if name.startswith(p):
            return (i, name)
    return (len(product_priority), name)

# 排序 key
def parse_sort_keys(name):
    product_match = re.match(r"([A-Z]+\d+)", name)
    product = product_match.group(1) if product_match else name
    color_match = re.search(r"(黑|白|灰|藍|粉|綠|卡其|棕紅|煙灰|深灰|淺灰|深藍|淺藍)", name)
    color = color_match.group(1) if color_match else ""
    size_match = re.search(r"(\d+XL|\d+|M|L|XL)$", name)
    size = size_match.group(1) if size_match else ""
    prod_key = product_key(product)
    if size in size_priority:
        size_key = size_priority[size]
    else:
        try:
            size_key = int(size)
        except:
            size_key = 999
    return (*prod_key, color, size_key)

if pdf_file and excel_file:
    # 讀 PDF
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text("text")
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    records = []
    for i in range(0, len(lines), 3):
        if i + 2 < len(lines):
            records.append([lines[i], lines[i+1], lines[i+2]])
    pdf_df = pd.DataFrame(records, columns=["系統編號", "SKU", "商品名稱"])

    # 讀對照表
    map_df = pd.read_excel(excel_file, header=1)

    # 合併
    merged = pdf_df.merge(map_df, left_on="SKU", right_on="平臺 SKU", how="left")
    result = merged[["SKU", "自定義產品名稱"]].rename(columns={"自定義產品名稱": "名稱"})

    # 排序
    result_sorted = result.sort_values(
        by=result["名稱"].apply(parse_sort_keys).tolist()
    ).reset_index(drop=True)

    st.write("✅ 排序後結果：", result_sorted)

    # 下載 Excel
    output = BytesIO()
    result_sorted.to_excel(output, index=False)
    st.download_button(
        label="📥 下載排序後 Excel",
        data=output.getvalue(),
        file_name="SKU對照_排序後.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
