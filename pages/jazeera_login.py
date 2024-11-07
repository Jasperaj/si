import requests
from bs4 import BeautifulSoup as bs
import streamlit as st

def fetch_jazeera_balance(username, password):
    with requests.Session() as c:
        url = r'https://webapp.jazeeraairways.com/Default.aspx?'
        header = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}
        status = c.get(url)
        data = bs(status.text, 'html.parser')

        # Find the hidden token required for login
        view_state = data.find('input', attrs={'name': '__VIEWSTATE'})['value']
        view_generator = data.find('input', attrs={'name':'__VIEWSTATEGENERATOR'})['value']
        event_valid = data.find('input', attrs={'name':'__EVENTVALIDATION'})['value']

        # Login to the website
        r = c.post(url, data={
            'ctl00_ToolkitScriptManager1_HiddenField': "",
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': view_state,
            '__VIEWSTATEGENERATOR': view_generator,
            '__EVENTVALIDATION': event_valid,
            'ctl00$ContentPlaceHolder1$ddlDomain': 'EXT',
            'ctl00$ContentPlaceHolder1$txtUserName': username,
            'ctl00$ContentPlaceHolder1$txtPassword': password,
            'ctl00$ContentPlaceHolder1$btnLogin': 'Login'
        }, headers=header)

        r = c.get('https://webapp.jazeeraairways.com/Main.aspx')
        soup = bs(r.text, 'html.parser')

        balance = soup.find('span', attrs={'id':'ctl00_ContentPlaceHolder1_lblAgCrAmount'}).text
        return balance

def jazeera_balance_page():
    st.title("Jazeera Balance Checker")

    username = 'NPSITS'
    password = 'J9Soc24'

    if st.button("Fetch Balance"):
        if username and password:
            with st.spinner("Fetching Jazeera Balance..."):
                try:
                    balance = fetch_jazeera_balance(username, password)
                    st.success("Balance fetched successfully!")
                    st.write(f"Jazeera Balance: {balance}")

                    if st.button("Download Balance Data"):
                        balance_data = f"Jazeera Balance: {balance}"
                        st.download_button(
                            label="Download Balance",
                            data=balance_data,
                            file_name="jazeera_balance.txt",
                            mime="text/plain"
                        )
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.error("Please provide both username and password")

def jazeera_main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.error("You must be logged in to view this page.")
        st.stop()
    jazeera_balance_page()

if __name__ == "__main__":
    jazeera_main()
