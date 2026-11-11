import streamlit as st
import pandas as pd
import zipfile
import io

st.set_page_config(page_title="Meesho GST Pro Calculator", layout="wide")

st.title("🛍️ Meesho GST Return Pro Calculator")
st.write("अपनी Meesho सेल्स और रिटर्न रिपोर्ट्स (ZIP, Excel, या CSV) एक साथ अपलोड करें और GSTR-1 की पूरी रिपोर्ट तैयार करें।")

# 1. Seller State Selection
seller_state = st.selectbox(
    "अपनी State (जहाँ से आप बिज़नेस चलाते हैं) चुनें:",
    ["DELHI", "UTTAR PRADESH", "MAHARASHTRA", "GUJARAT", "HARYANA", "RAJASTHAN", "BIHAR", "WEST BENGAL", "KARNATAKA", "TAMIL NADU", "MADHYA PRADESH", "PUNJAB", "OTHER"]
)

# 2. Multiple File Uploader (Supporting ZIP, XLSX, CSV)
uploaded_files = st.file_uploader(
    "Meesho फाइलें अपलोड करें (एक या एक से ज़्यादा ZIP, XLSX, CSV फाइलें चुन सकते हैं)", 
    type=["zip", "xlsx", "xls", "csv"], 
    accept_multiple_files=True
)

def read_single_file(file_obj, file_name):
    """किसी भी ZIP, Excel या CSV फाइल से डेटा निकालने के लिए फंक्शन"""
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

if uploaded_files:
    all_dataframes = []
    
    try:
        for uploaded_file in uploaded_files:
            extracted_dfs = read_single_file(uploaded_file, uploaded_file.name)
            all_dataframes.extend(extracted_dfs)
            
        if all_dataframes:
            # सभी फाइलों के डेटा को एक साथ जोड़ना (Merge)
            df = pd.concat(all_dataframes, ignore_index=True)
            st.success(f"कुल {len(uploaded_files)} फाइल(ओं) का डेटा सफलतापूर्वक मर्ज और प्रोसेस हो गया है!")
            
            # कॉलम के नाम साफ करना
            df.columns = df.columns.str.strip().str.lower()
            
            # ज़रूरी कॉलम चेक करना
            required_cols = ['total_taxable_value', 'tax_amount', 'gst_rate', 'customer_state']
            if all(col in df.columns for col in required_cols):
                
                # डेटा को सही फॉर्मेट (Numbers) में बदलना
                df['total_taxable_value'] = pd.to_numeric(df['total_taxable_value'], errors='coerce').fillna(0)
                df['tax_amount'] = pd.to_numeric(df['tax_amount'], errors='coerce').fillna(0)
                df['gst_rate'] = pd.to_numeric(df['gst_rate'], errors='coerce').fillna(0)
                df['customer_state'] = df['customer_state'].astype(str).str.strip().str.upper()
                
                # अगर quantity और hsn_code कॉलम मौजूद हैं तो उन्हें भी साफ करें
                if 'quantity' in df.columns:
                    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
                else:
                    df['quantity'] = 1
                    
                if 'hsn_code' in df.columns:
                    df['hsn_code'] = df['hsn_code'].astype(str).str.replace('.0', '', regex=False).str.strip()
                else:
                    df['hsn_code'] = 'N/A'

                # 3. Gross Sales vs Returns (RTO) का अलग हिसाब
                sales_df = df[df['total_taxable_value'] > 0]
                returns_df = df[df['total_taxable_value'] < 0]
                
                gross_sales = sales_df['total_taxable_value'].sum()
                total_returns = abs(returns_df['total_taxable_value'].sum())
                net_taxable_sales = df['total_taxable_value'].sum()

                st.subheader("📈 सेल्स और रिटर्न का विवरण (Sales vs Returns)")
                s_col1, s_col2, s_col3 = st.columns(3)
                s_col1.metric("Gross Sales (कुल बिक्री)", f"₹ {gross_sales:,.2f}")
                s_col2.metric("Total Returns (वापसी / RTO)", f"- ₹ {total_returns:,.2f}")
                s_col3.metric("Net Taxable Turnover (शुद्ध बिक्री)", f"₹ {net_taxable_sales:,.2f}")

                st.divider()

                # 4. IGST vs CGST/SGST कैलकुलेशन
                df['is_igst'] = df['customer_state'] != seller_state.upper()
                
                total_igst = df[df['is_igst']]['tax_amount'].sum()
                total_cgst_sgst = df[~df['is_igst']]['tax_amount'].sum()
                total_cgst = total_cgst_sgst / 2
                total_sgst = total_cgst_sgst / 2

                st.subheader("💰 कुल टैक्स समरी (GSTR-1 & 3B)")
                t_col1, t_col2, t_col3, t_col4 = st.columns(4)
                t_col1.metric("Net Taxable Value", f"₹ {net_taxable_sales:,.2f}")
                t_col2.metric("Total IGST (अन्य राज्य)", f"₹ {total_igst:,.2f}")
                t_col3.metric("Total CGST (केंद्रीय टैक्स)", f"₹ {total_cgst:,.2f}")
                t_col4.metric("Total SGST (राज्य टैक्स)", f"₹ {total_sgst:,.2f}")

                st.divider()

                # 5. State-Wise Breakdown Table
                st.subheader("📍 राज्य के अनुसार GST विवरण (State-Wise Summary)")
                state_summary = df.groupby(['customer_state', 'gst_rate']).agg(
                    Taxable_Value=('total_taxable_value', 'sum'),
                    Tax_Amount=('tax_amount', 'sum')
                ).reset_index()
                state_summary.columns = ['Customer State', 'GST Rate (%)', 'Net Taxable Value (₹)', 'Total Tax (₹)']
                st.dataframe(state_summary, use_container_width=True)

                # 6. HSN-Wise Summary (GSTR-1 Table 12 के लिए)
                st.subheader("📦 HSN कोड के अनुसार विवरण (HSN-Wise Summary)")
                hsn_summary = df.groupby(['hsn_code', 'gst_rate']).agg(
                    Total_Quantity=('quantity', 'sum'),
                    Taxable_Value=('total_taxable_value', 'sum'),
                    Tax_Amount=('tax_amount', 'sum')
                ).reset_index()
                hsn_summary.columns = ['HSN Code', 'GST Rate (%)', 'Net Quantity', 'Net Taxable Value (₹)', 'Total Tax (₹)']
                st.dataframe(hsn_summary, use_container_width=True)

                st.divider()

                # 7. Visual Chart (टॉप 10 राज्यों की बिक्री का ग्राफ)
                st.subheader("📊 टॉप राज्यों की बिक्री का ग्राफ (Top States by Net Sales)")
                chart_data = df.groupby('customer_state')['total_taxable_value'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(chart_data)

                st.divider()

                # 8. Download Ready-Made Excel Report Button
                st.subheader("📥 तैयार रिपोर्ट डाउनलोड करें")
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # पहली शीट: Overview Summary
                    summary_data = pd.DataFrame({
                        'Description': ['Gross Sales', 'Total Returns', 'Net Taxable Turnover', 'Total IGST', 'Total CGST', 'Total SGST'],
                        'Amount (INR)': [gross_sales, -total_returns, net_taxable_sales, total_igst, total_cgst, total_sgst]
                    })
                    summary_data.to_excel(writer, sheet_name='Overall_Summary', index=False)
                    
                    # दूसरी शीट: State-Wise Data
                    state_summary.to_excel(writer, sheet_name='State_Wise_GSTR1', index=False)
                    
                    # तीसरी शीट: HSN-Wise Data
                    hsn_summary.to_excel(writer, sheet_name='HSN_Wise_Table12', index=False)
                
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 पूरी GSTR-1 रिपोर्ट डाउनलोड करें (Excel)",
                    data=excel_data,
                    file_name="Meesho_GSTR1_Ready_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:
                st.error("Error: अपलोड की गई फाइलों में ज़रूरी कॉलम नहीं मिले।")
                st.write("Missing columns:", [col for col in required_cols if col not in df.columns])
        else:
            st.warning("अपलोड की गई ZIP फाइल के अंदर कोई Excel या CSV डेटा नहीं मिला।")
            
    except Exception as e:
        st.error(f"डेटा प्रोसेस करने में समस्या आई: {e}")
