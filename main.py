import streamlit as st
from streamlit_option_menu import option_menu
from pages.connectips_page import connectips_page
from pages.M import MBL_page

def main():
    with st.sidebar:
        selected = option_menu(
            "Main Menu", ["ConnectIPS", "MBL", "Other App"],
            icons=['house', 'gear'],
            menu_icon="cast", default_index=0
        )

    if selected == "ConnectIPS":
        connectips_page()
    elif selected == "MBL":
        MBL_page()
    elif selected == "Other Page":
        st.title("Other Page")
        st.write("This is another page.")

if __name__ == "__main__":
    main()
