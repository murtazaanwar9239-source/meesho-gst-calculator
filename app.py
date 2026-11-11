import streamlit as st
import pandas as pd
import zipfile
import io

# Page Configuration
st.set_page_config(
    page_title="Meesho GST Pro Calculator",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern SaaS Look
st.markdown("""
<style>
    /* Main Background & Font */
    .main {
        background-color: #f8f9fa;
    }
    /* Custom Header Banner */
    .header-banner {
        background: linear-gradient(135deg, #9c27b0 0%, #e91e63 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(233, 30, 99, 0.2);
    }
    .header-banner h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
    }
    .header-banner p {
        margin: 0.5rem 0 0 0;
        font-size: 1.05rem;
        opacity: 0.9;
    }
    /* Stylish Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: transform 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    /* Custom Download Button */
    .stDownloadButton button {
        background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 1.5rem !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 10px rgba(76, 175, 80, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# Top Hero Banner
st.markdown("""
<div class="header-banner">
    <h1>🛍️ Meesho GST Return Pro Calculator</h1>
    <p>Apni Meesho Sales aur Return reports (ZIP, Excel, CSV) upload karein aur 1-click mein GSTR-1 summary tayar karein.</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for Controls
with st.sidebar:
    st.image("https://flaticon.com", width=70)
    st.header("⚙️ Settings & Upload")
    
    seller_state = st.selectbox(
        "1. Apni Business State Chunein:",
        ["DELHI", "UTTAR PRADESH", "MAHARASHTRA", "GUJARAT", "HARYANA", "RAJASTHAN", "BIHAR", "WEST BENGAL", "KARNATAKA", "TAMIL NADU", "MADHYA PRADESH", "PUNJAB", "OTHER"]
    )
    
    st.markdown("---")
    
    uploaded_files = st.file_uploader(
        "2. Meesho Reports Upload Karein:", 
        type=["zip", "xlsx", "xls", "csv"], 
        accept_multiple_files=True,
        help="Aap ek saath multiple ZIP, Excel ya CSV files upload kar sakte hain."
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** Forward (Sales) aur Reverse (Return) dono files ek saath upload karein taaki Net GST sahi calculate ho.")

def read_single_file(file_obj, file_name):
    dfs = []
    name_lower = file_name.lower()
    if name_lower.endswith('.zip'):
        with zipfile.ZipFile(file_obj) as z:
            for inner_name in z.namelist():
                if inner_name.lower().endswith(('.xlsx', '.xls')):
                    with z.open(inner_name) as f:
                        dfs.append(pd.read_excel(io.BytesIO(f.read())))
                elif inner_name.lower().endswith('.csv'):
                    with z.open(inner_name) as f:
                        dfs.append(pd.read_csv(io.BytesIO(f.read())))
    elif name_lower.endswith(('.xlsx', '.xls')):
        dfs.append(pd.read_excel(file_obj))
    elif name_lower.endswith('.csv'):
        dfs.append(pd.read_csv(file_obj))
    return dfs

# Main Dashboard Area
if not uploaded_files:
    # Empty State Welcome Screen
    st.markdown("### 👋 Swagat Hai! Shuru Karne Ke Liye:")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**Step 1: State Select Karein**\n\nLeft sidebar se apni registered GST state chunein.")
    with c2:
        st.info("**Step 2: Files Upload Karein**\n\nMeesho se download ki gayi `.zip` ya `.xlsx` files upload karein.")
    with c3:
        st.info("**Step 3: Report Download Karein**\n\nAutomatic calculated GSTR-1 Excel sheet download karein.")

else:
    all_dataframes = []
    try:
        with st.spinner("Aapki files process aur merge ho rahi hain..."):
            for uploaded_file in uploaded_files:
                extracted_dfs = read_single_file(uploaded_file, uploaded_file.name)
                all_dataframes.extend(extracted_dfs)
                
        if all_dataframes:
            df = pd.concat(all_dataframes, ignore_index=True)
            df.columns = df.columns.str.strip().str.lower()
            
            required_cols = ['total_taxable_value', 'tax_amount', 'gst_rate', 'customer_state']
            if all(col in df.columns for col in required_cols):
                
                # Data Cleaning
                df['total_taxable_value'] = pd.to_numeric(df['total_taxable_value'], errors='coerce').fillna(0)
                df['tax_amount'] = pd.to_numeric(df['tax_amount'], errors='coerce').fillna(0)
                df['gst_rate'] = pd.to_numeric(df['gst_rate'], errors='coerce').fillna(0)
                df['customer_state'] = df['customer_state'].astype(str).str.strip().str.upper()
                
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0) if 'quantity' in df.columns else 1
                df['hsn_code'] = df['hsn_code'].astype(str).str.replace('.0', '', regex=False).str.strip() if 'hsn_code' in df.columns else 'N/A'

                # Calculations
                sales_df = df[df['total_taxable_value'] > 0]
                returns_df = df[df['total_taxable_value'] < 0]
                
                gross_sales = sales_df['total_taxable_value'].sum()
                total_returns = abs(returns_df['total_taxable_value'].sum())
                net_taxable_sales = df['total_taxable_value'].sum()

                df['is_igst'] = df['customer_state'] != seller_state.upper()
                total_igst = df[df['is_igst']]['tax_amount'].sum()
                total_cgst_sgst = df[~df['is_igst']]['tax_amount'].sum()
                total_cgst = total_cgst_sgst / 2
                total_sgst = total_cgst_sgst / 2

                # Prepare Summaries
                state_summary = df.groupby(['customer_state', 'gst_rate']).agg(
                    Taxable_Value=('total_taxable_value', 'sum'),
                    Tax_Amount=('tax_amount', 'sum')
                ).reset_index()
                state_summary.columns = ['Customer State', 'GST Rate (%)', 'Net Taxable Value (₹)', 'Total Tax (₹)']

                hsn_summary = df.groupby(['hsn_code', 'gst_rate']).agg(
                    Total_Quantity=('quantity', 'sum'),
                    Taxable_Value=('total_taxable_value', 'sum'),
                    Tax_Amount=('tax_amount', 'sum')
                ).reset_index()
                hsn_summary.columns = ['HSN Code', 'GST Rate (%)', 'Net Quantity', 'Net Taxable Value (₹)', 'Total Tax (₹)']

                # Excel Generation
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    summary_data = pd.DataFrame({
                        'Description': ['Gross Sales', 'Total Returns', 'Net Taxable Turnover', 'Total IGST', 'Total CGST', 'Total SGST'],
                        'Amount (INR)': [gross_sales, -total_returns, net_taxable_sales, total_igst, total_cgst, total_sgst]
                    })
                    summary_data.to_excel(writer, sheet_name='Overall_Summary', index=False)
                    state_summary.to_excel(writer, sheet_name='State_Wise_GSTR1', index=False)
                    hsn_summary.to_excel(writer, sheet_name='HSN_Wise_Table12', index=False)
                excel_data = output.getvalue()

                # Top Action Bar with Download Button
                col_title, col_btn = st.columns([3, 1])
                with col_title:
                    st.success(f"✅ {len(uploaded_files)} File(s) successfully processed!")
                with col_btn:
                    st.download_button(
                        label="📥 Download Excel Report",
                        data=excel_data,
                        file_name="Meesho_GSTR1_Ready_Report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                # Organized Tabs for Clean UI
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Tax & Sales Overview", "📍 State-Wise GSTR-1", "📦 HSN-Wise Summary", "📈 Visual Analytics"])

                with tab1:
                    st.markdown("#### 1. Sales vs Returns Breakdown")
                    s1, s2, s3 = st.columns(3)
                    s1.metric("Gross Sales (कुल बिक्री)", f"₹ {gross_sales:,.2f}")
                    s2.metric("Total Returns (RTO / वापसी)", f"- ₹ {total_returns:,.2f}")
                    s3.metric("Net Taxable Turnover", f"₹ {net_taxable_sales:,.2f}")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("#### 2. GST Liability Summary")
                    t1, t2, t3, t4 = st.columns(4)
                    t1.metric("Net Taxable Value", f"₹ {net_taxable_sales:,.2f}")
                    t2.metric("Total IGST (Out of State)", f"₹ {total_igst:,.2f}")
                    t3.metric("Total CGST (Central)", f"₹ {total_cgst:,.2f}")
                    t4.metric("Total SGST (State)", f"₹ {total_sgst:,.2f}")

                with tab2:
                    st.markdown("#### State-Wise Tax Details (GSTR-1 B2CS Table ke liye)")
                    st.dataframe(state_summary, use_container_width=True, hide_index=True)

                with tab3:
                    st.markdown("#### HSN Code Wise Summary (GSTR-1 Table 12 ke liye)")
