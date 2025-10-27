import pandas as pd
import streamlit as st
from io import BytesIO
import os

# ---------------- Streamlit Page Setup ----------------
st.set_page_config(page_title="CSV/XLSX Comparator", layout="wide")
pd.set_option("styler.render.max_elements", 5_000_000)

developer_name = "Sumit"
developer_name2 = "Shruti"

col1, col2 = st.columns([1, 6])
with col1:
    st.markdown(f"**👤 {developer_name}**")
    st.markdown(f"**👤 {developer_name2}**")
with col2:
    st.title("📊 CSV / Excel File Comparator")

if "diff_df" not in st.session_state:
    st.session_state.diff_df = pd.DataFrame()

file_type = st.selectbox("Select File Type", ["CSV", "XLSX", "XLS"])
file1 = st.file_uploader(f"Upload First {file_type} File", type=[file_type.lower()])
file2 = st.file_uploader(f"Upload Second {file_type} File", type=[file_type.lower()])

df1, df2 = pd.DataFrame(), pd.DataFrame()

# ---------------- Load File Function (with chunking for speed) ----------------
def load_file(file, ftype):
    if ftype == "CSV":
        return pd.read_csv(file)  # For huge files, can add chunksize=50000 if needed
    else:
        return pd.read_excel(file, engine="openpyxl")

# ---------------- Load Files ----------------
if file1:
    df1 = load_file(file1, file_type)
    st.subheader("File 1 Preview")
    st.dataframe(df1.head(1000).style.set_table_styles(
        [{'selector': 'th', 'props': [('font-weight', 'bold')]}]
    ))

if file2:
    df2 = load_file(file2, file_type)
    st.subheader("File 2 Preview")
    st.dataframe(df2.head(1000).style.set_table_styles(
        [{'selector': 'th', 'props': [('font-weight', 'bold')]}]
    ))

# ---------------- Compare Button ----------------
if st.button("Compare Files"):
    if df1.empty or df2.empty:
        st.error("Please upload both files first!")
    elif list(df1.columns) != list(df2.columns):
        st.error("Column names do not match!")
    else:
        st.info("🔍 Comparing files, please wait...")
        progress = st.progress(0)

        # ✅ Align the sizes
        max_len = max(len(df1), len(df2))
        df1 = df1.reindex(range(max_len)).reset_index(drop=True)
        df2 = df2.reindex(range(max_len)).reset_index(drop=True)

        # ✅ Fast vectorized comparison
        diff_mask = (df1 != df2) & ~(df1.isna() & df2.isna())

        # ✅ Build result efficiently
        diff_df = df1.copy()
        for col in df1.columns:
            diff_col = diff_mask[col]
            diff_df.loc[diff_col, col] = df1[col].astype(str) + " → " + df2[col].astype(str)

        # ✅ Keep only changed rows
        diff_df = diff_df.loc[diff_mask.any(axis=1)]

        st.session_state.diff_df = diff_df
        progress.progress(100)

        if diff_df.empty:
            st.info("✅ No differences found!")
        else:
            st.success(f"✅ Found {len(diff_df)} differing rows!")

# ---------------- Display Differences ----------------
if not st.session_state.diff_df.empty:
    st.subheader("Differences (showing first 500 rows)")
    def highlight_diff(val):
        return "background-color: #ffcccc" if "→" in str(val) else ""
    st.dataframe(
        st.session_state.diff_df.head(500).style.applymap(highlight_diff)
    )

    # ---------------- Download Button ----------------
    output = BytesIO()
    st.session_state.diff_df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    st.download_button(
        label="📥 Download All Differences",
        data=output,
        file_name="differences.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
