import streamlit as st
from nepse import Nepse

# Initialize the Nepse instance
nepse = Nepse()
nepse.setTLSVerification(False)  # This is temporary, until Nepse sorts its SSL certificate problem

# Streamlit app title
st.title("Data Viewer")

# Function to get NEPSE index data
def get_nepse_index_data():
    data = nepse.getNepseIndex()
    target_id = 'NEPSE Index'
    result = next((item for item in data if item.get('index') == target_id), None)
    return result['currentValue']

# Button to load the data
if st.button("Load Index Data"):
    index_data = get_nepse_index_data()
    
    if index_data:
        st.subheader("Index Data")
        st.write(index_data)
    else:
        st.warning("No data found with ID = Index")


