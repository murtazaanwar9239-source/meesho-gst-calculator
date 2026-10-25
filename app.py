import streamlit as st
import pandas as pd

st.set_page_config(page_title="Meesho GST Calculator", layout="wide")

st.title("🛍️ Meesho GST Return Calculator")
st.write("Apni Meesho sales report upload karein aur GSTR-1 ke liye ready-made summary payein.")

# Seller State Input (Taake CGST/SGST aur IGST alag ho sake)
seller_state = st.selectbox(
    "Apni State (Jahan se aap business chalate hain) select karein:",
    ["DELHI", "UTTAR PRADESH", "MAHARASHTRA", "GUJARAT", "HARYANA", "RAJASTHAN", "BIHAR", "WEST BENGAL", "KARNATAKA", "TAMIL NADU", "OTHER"]
)

# File Uploader
uploaded_file = st.file_uploader("Meesho Excel Sheet Upload Karein (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Excel read karna
        df = pd.read_excel(uploaded_file)
        st.success("File kamyabi se upload aur read ho gayi hai!")
        
        # Column names ko clean karna (Spaces hatane ke liye)
        df.columns = df.columns.str.strip().str.lower()
        
        # Required columns check karna
        required_cols = ['total_taxable_value', 'tax_amount', 'gst_rate', 'customer_state']
        if all(col in df.columns for col in required_cols):
            
            # Khali values ko 0 karna aur numbers mein badalna
            df['total_taxable_value'] = pd.to_numeric(df['total_taxable_value'], errors='coerce').fillna(0)
            df['tax_amount'] = pd.to_numeric(df['tax_amount'], errors='coerce').fillna(0)
            df['gst_rate'] = pd.to_numeric(df['gst_rate'], errors='coerce').fillna(0)
            df['customer_state'] = df['customer_state'].astype(str).str.strip().str.upper()
            
            # Total Calculation
            total_taxable = df['total_taxable_value'].sum()
            total_tax = df['tax_amount'].sum()
            
            # IGST vs CGST/SGST Logic
            # Agar customer ki state seller ki state se alag hai toh IGST, nahi toh CGST+SGST
            df['is_igst'] = df['customer_state'] != seller_state.upper()
            
            total_igst = df[df['is_igst']]['tax_amount'].sum()
            total_cgst_sgst = df[~df['is_igst']]['tax_amount'].sum()
            total_cgst = total_cgst_sgst / 2
            total_sgst = total_cgst_sgst / 2
            
            # Main Dashboard Cards
            st.subheader("📊 GSTR-1 Sales & Tax Summary")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Taxable TurnOver", f"₹ {total_taxable:,.2f}")
            col2.metric("Total IGST", f"₹ {total_igst:,.2f}")
            col3.metric("Total CGST (Central)", f"₹ {total_cgst:,.2f}")
            col4.metric("Total SGST (State)", f"₹ {total_sgst:,.2f}")
            
            # State-wise Breakup Table (GST portal par bharne ke liye)
            st.subheader("📍 State-Wise GST Breakdown")
            state_summary = df.groupby(['customer_state', 'gst_rate']).agg(
                Total_Taxable_Value=('total_taxable_value', 'sum'),
                Total_Tax_Collected=('tax_amount', 'sum')
            ).reset_index()
            
            # Column names professional lagne ke liye rename karein
            state_summary.columns = ['Customer State', 'GST Rate (%)', 'Taxable Value (₹)', 'Tax Amount (₹)']
            st.dataframe(state_summary, use_container_width=True)
            
        else:
            st.error("Error: Is excel sheet mein zaroori columns nahi mil rahe hain. Kripya sahi Meesho report upload karein.")
            st.write("Missing columns:", [col for col in required_cols if col not in df.columns])
            
    except Exception as e:
        st.error(f"File process karne mein dikkat aayi: {e}")
