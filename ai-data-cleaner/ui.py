import streamlit as st
import pandas as pd
import requests
import io

st.set_page_config(layout="wide")
st.title("AI Data Cleaner")

uploaded_file = st.file_uploader("Upload CSV", type="csv")
user_instructions = st.text_area("Cleaning Instructions", "Drop duplicate rows. Fill missing age values with the column mean. Fill missing name and occupation values with 'Unknown'.")

if uploaded_file:
    df_before = pd.read_csv(uploaded_file)
    
    if st.button("Clean Data"):
        uploaded_file.seek(0)
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
        data = {"instructions": user_instructions}
        
        with st.spinner("Processing data..."):
            response = requests.post("http://127.0.0.1:8000/clean", files=files, data=data)
        
        if response.status_code == 200:
            df_after = pd.read_csv(io.BytesIO(response.content))
            
            st.success("Data cleaning completed successfully.")
            
            rows_removed = len(df_before) - len(df_after)
            missing_before = int(df_before.isnull().sum().sum())
            missing_after = int(df_after.isnull().sum().sum())
            filled_count = missing_before - missing_after
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Duplicates Removed", rows_removed)
            m2.metric("Missing Values Filled", filled_count)
            m3.metric("Final Missing Values", missing_after)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Before Cleaning")
                st.dataframe(df_before)
                if 'age' in df_before.columns:
                    st.write("Age Distribution Before")
                    st.bar_chart(df_before['age'])
                
            with col2:
                st.subheader("After Cleaning")
                st.dataframe(df_after)
                if 'age' in df_after.columns:
                    st.write("Age Distribution After")
                    st.bar_chart(df_after['age'])
            
            st.download_button("Download Clean Data", response.content, "clean_data.csv", mime="text/csv")
        else:
            st.error("Error processing file")