import getpass
import pandas as pd
import streamlit as st
from io import BytesIO
import os
import datetime as dt

# ---------------- Streamlit Page Setup ----------------
st.set_page_config(page_title="CSV/XLSX Comparator", layout="wide")


# ✅ Increase Pandas Styler render limit (fixes your error)
pd.set_option("styler.render.max_elements", 5_000_000)  # allow up to 5 million cells

developer_name = "Sumit"

# Create two columns: left for developer name, right for title
col1, col2 = st.columns([1, 6])

with col1:
    st.markdown(f"**👤 {developer_name}**")  # bold developer name top-left

with col2:
    st.title("📊 CSV / Excel File Comparator")

# ---------------- Session State Initialization ----------------
if "diff_df" not in st.session_state:
    st.session_state.diff_df = pd.DataFrame()

# ---------------- File Type Selection ----------------
file_type = st.selectbox("Select File Type", ["CSV", "XLSX", "XLS"])

# ---------------- File Upload ----------------
file1 = st.file_uploader(f"Upload First {file_type} File", type=[file_type.lower()])
file2 = st.file_uploader(f"Upload Second {file_type} File", type=[file_type.lower()])

df1, df2 = pd.DataFrame(), pd.DataFrame()

# ---------------- Load File 1 ----------------
if file1:
    if file_type == "CSV":
        df1 = pd.read_csv(file1)
    else:
        df1 = pd.read_excel(file1, engine="openpyxl")
    st.subheader("File 1 Preview")
    st.dataframe(df1.head(100))  # show only first 100 rows for performance

# ---------------- Load File 2 ----------------
if file2:
    if file_type == "CSV":
        df2 = pd.read_csv(file2)
    else:
        df2 = pd.read_excel(file2, engine="openpyxl")
    st.subheader("File 2 Preview")
    st.dataframe(df2.head(100))

# ---------------- Compare Button ----------------
if st.button("Compare Files"):
    if df1.empty or df2.empty:
        st.error("Please upload both files first!")
    elif list(df1.columns) != list(df2.columns):
        st.error("Column names do not match!")
    else:
        diff_rows = []
        max_len = max(len(df1), len(df2))
        for i in range(max_len):
            row1 = df1.iloc[i] if i < len(df1) else pd.Series([None]*len(df1.columns), index=df1.columns)
            row2 = df2.iloc[i] if i < len(df2) else pd.Series([None]*len(df2.columns), index=df2.columns)
            diff_row = []
            for col in df1.columns:
                val1, val2 = row1[col], row2[col]
                if pd.isna(val1) and pd.isna(val2):
                    diff_row.append(val1)
                elif val1 != val2:
                    diff_row.append(f"{val1} → {val2}")  # highlight difference
                else:
                    diff_row.append(val1)
            if any("→" in str(v) for v in diff_row):
                diff_rows.append(diff_row)

        st.session_state.diff_df = pd.DataFrame(diff_rows, columns=df1.columns)

        if st.session_state.diff_df.empty:
            st.info("✅ No differences found between the two files!")

# ---------------- Display Differences ----------------
if not st.session_state.diff_df.empty:
    st.subheader("Differences")

    def highlight_diff(val):
        if "→" in str(val):
            return "background-color: #ffcccc"
        return ""

    # ✅ Use styler limit fix and also prevent heavy UI lag by truncating view
    st.dataframe(st.session_state.diff_df.head(500).style.applymap(highlight_diff))

    # ---------------- Download Button ----------------
    output = BytesIO()
    st.session_state.diff_df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    st.download_button(
        label="📥 Download Differences",
        data=output,
        file_name="differences.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
