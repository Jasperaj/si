import streamlit as st
from pages.connectips_page import connectips_main
from pages.M import MBL_main
from pages.H import HBL_main
from pages.wlink import wlink_main
from pages.NEA import nea_main
from pages.vatreturn import vat_main
from pages.I import ird_main
from pages.bank_reco import bank_main
#from pages.jazeera_login import jazeera_main
from pages.fonepay_app import fonepay_main

# Placeholder for user credentials
USER_CREDENTIALS = {
    st.secrets["USERNAME"]: st.secrets["PASSWORD"],  # Replace with actual username and password
}


def login():
    st.title("Login")
    
    # Login form
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.experimental_rerun()  # Force a rerun to update the UI
        else:
            st.error("Invalid username or password")

def main_page():
    if not st.session_state.get("logged_in"):
        st.error("You are not logged in. Please log in to access this page.")
        return  # Prevents rendering the main page content if not logged in

    st.sidebar.title("Navigation")
    
    # Sidebar navigation
    page = st.sidebar.selectbox("Choose a page", ["Dashboard", "Main Menu", "ConnectIPS", "MBL", "W-Link" ,"NEA", "VAT Return","Other Pages"])
    
    if page == "Dashboard":
        dashboard_page()  # Call the dashboard page function
    elif page == "Home":
        st.title("Home Page")
        st.write("Welcome to the Home Page!")
    elif page == "ConnectIPS":
        connectips_main()
    elif page == "MBL":
        MBL_main()
    elif page == "W-link":
        wlink_main()
    elif page == "NEA":
        nea_main()
    elif page == "VAT Return":
        vat_main()
    elif page == "Bank Reco":
        bank_main()
    elif page == "Fonepay":
        fonepay_main()        
    elif page == "Jazeera Login":
        pass
        #jazeera_main()
    elif page == "Other Pages":
        st.title("Other Pages")
        st.write("Welcome to Other Pages!")

def main():
    # Initialize the session state for 'logged_in' if not already present
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # Check if user is logged in or not
    if not st.session_state.logged_in:
        hide_sidebar_style = """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
        """
        st.markdown(hide_sidebar_style, unsafe_allow_html=True)
        login()
    else:
        main_page()

if __name__ == "__main__":
    main()

