# Import necessary libraries
import streamlit as st
import pandas as pd
import os

# Set the path for the Excel file
tg_path = r"D:\Curves colors\Society Finance Group - Documents\THAI AIRWAYS ( TG )\TG BSP REPORT\BSP SUMMARY REPORT 02 (TG)-.xlsx"
j9_path = r"D:\Curves colors\Society Finance Group - Documents\THAI AIRWAYS ( TG )\TG BSP REPORT\BSP SUMMARY REPORT 02 (TG)-.xlsx"


# Try to load the sheets
try:
    # Load each sheet into a DataFrame
    df_tg = pd.read_excel(tg_path, sheet_name="GSA Agreement & Validity")
    df_j9 = pd.read_excel(j9_path, sheet_name="Issued Bank Guarantee")
    
    # Create tabs for each sheet
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["TG Sales Summary", "Jazeera Sales Summary"])

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
        display_filtered_dataframe(df_gsa_validity, "TG Sales Summary")

    with tab2:
        display_filtered_dataframe(df_issued_bg, "Jazeera Sales Summary")



except FileNotFoundError:
    st.error("The specified Excel file was not found in the folder.")
except Exception as e:
    st.error(f"An error occurred: {e}")
