# Import necessary libraries
import streamlit as st
import pandas as pd
import os

# Set the path for the Excel file
excel_path = r"D:\OneDrive - Curves colors\Desktop\steamlit_app\data\si-master-sheet-8182.xlsx"

# Try to load the sheets
try:
    # Load each sheet into a DataFrame
    df_gsa_validity = pd.read_excel(excel_path, sheet_name="GSA Agreement & Validity")
    df_issued_bg = pd.read_excel(excel_path, sheet_name="Issued Bank Guarantee")
    df_received_bg = pd.read_excel(excel_path, sheet_name="Bank Guarantee Received")
    df_mbl_bg = pd.read_excel(excel_path, sheet_name="MBL Non Funded Limit")
    df_hbl_bg = pd.read_excel(excel_path, sheet_name="HBL Non Funded Limit ")

    # Create tabs for each sheet
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["GSA Agreement", "Issued BG", "Received BG", "MBL BG", "HBL BG"])

    # Function to add a filter and display filtered DataFrame
    def display_filtered_dataframe(df, tab_name):
        st.header(f"{tab_name} Data")

        # Filter options
        filter_column = st.selectbox(f"Select column to filter in {tab_name}", df.columns)
        unique_values = df[filter_column].dropna().unique()
        filter_value = st.selectbox(f"Filter {filter_column} by", unique_values)

        # Apply filter
        filtered_df = df[df[filter_column] == filter_value]
        st.dataframe(filtered_df)

    # Display filtered DataFrame for each tab
    with tab1:
        display_filtered_dataframe(df_gsa_validity, "GSA Agreement & Validity")

    with tab2:
        display_filtered_dataframe(df_issued_bg, "Issued BG")

    with tab3:
        display_filtered_dataframe(df_received_bg, "Received BG")

    with tab4:
        display_filtered_dataframe(df_mbl_bg, "MBL BG")

    with tab5:
        display_filtered_dataframe(df_hbl_bg, "HBL BG")

except FileNotFoundError:
    st.error("The specified Excel file was not found in the folder.")
except Exception as e:
    st.error(f"An error occurred: {e}")
