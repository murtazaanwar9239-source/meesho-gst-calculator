 import streamlit as st

st.title("Meesho GST Return Calculator")
st.write("Apni Meesho sales report (.xlsx ya .csv) yahan upload karein:")

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    st.success("File successfully upload ho gayi hai! GST calculation logic jaldi hi yahan dikhega.")
