import streamlit as st
import pandas as pd

# Function to fetch and display data from a Google Sheets URL
def get_share_value(sheet_id, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url)
        df = df.fillna(0)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Function to save DataFrame as an HTML file
def save_dataframe_as_html(df, sheet_name):
    report_save = f"{sheet_name}.html"
    df.to_html(report_save)
    return report_save

# Main function for the Streamlit app
def share_value_viewer():
    st.title("Google Sheets Share Value Viewer")

    # Input fields for the Google Sheets ID and sheet name
    sheet_id = st.text_input("Enter the Google Sheets ID:", value="1cDf6tk7onFs3wNRHNWMoQ8wJsOMGg7uMHjziMxhjbek")
    sheet_name = st.text_input("Enter the Sheet Name:", value="NW")

    if st.button("Fetch and Display Data"):
        if sheet_id and sheet_name:
            df = get_share_value(sheet_id, sheet_name)
            if df is not None:
                st.write("Data from the Google Sheet:")
                st.dataframe(df)

                report_save = save_dataframe_as_html(df, sheet_name)
                with open(report_save, "rb") as file:
                    st.download_button(
                        label="Download as HTML",
                        data=file,
                        file_name=report_save,
                        mime="text/html"
                    )
        else:
            st.warning("Please enter both the Google Sheets ID and sheet name.")

# Run the app
if __name__ == "__main__":
    share_value_viewer()
