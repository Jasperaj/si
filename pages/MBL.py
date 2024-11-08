import streamlit as st
import requests
import json
import pandas as pd
import datetime
import io
from io import BytesIO
import xlsxwriter


bank_acc = {'j9': st.secrets["m_j9"], 'tg': st.secrets["m_tg"], 'tg usd': st.secrets["m_tgusd"], 'j9 usd': st.secrets["m_j9usd"]}

def mbl_login():
    cookies = {
        '_ga': 'GA1.1.1543921064.1646386040',
        'TSc87c1f13027': '080b7d1ee8ab2000f4d98dbee7aca2afa86bc217262cdff3f21d11449e1918e626bc9f02d57e05f0086bf6833411300005c6a938357b385b0f61a0b49eea43a1e9bc43fd577db39f70bc7715776a9f3ff6557874c5a9c54ee9a446dcf5ce248c',
        '_ga_L889FR8VW9': 'GS1.1.1714969954.65.1.1714970774.0.0.0',
    }

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7,ne-NP;q=0.6,ne;q=0.5',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://ibank.machbank.com',
        'Referer': 'https://ibank.machbank.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    json_data = {
        'username': st.secrets["m_username"],
        'password': st.secrets["m_password"],
        'gRecaptchaResponse': '',
    }

    response = requests.post(
        'https://ibank.machbank.com/expressBanking-client-web/api/Customer/auth',
        cookies=cookies,
        headers=headers,
        json=json_data,
    )

    if response.status_code == 200:
        if 'Authorization' in response.headers:
            auth = response.headers['Authorization']
            st.session_state.logged_in = True
            st.session_state.auth_token = auth
            st.session_state.cookies = cookies
        else:
            st.error("Authorization header not found in response.")
            st.session_state.logged_in = False
    else:
        st.error(f"Login failed with status code: {response.status_code}")
        st.error(response.text)
        st.session_state.logged_in = False
    return headers

def view_statement(bank_name, to_date, from_date, headers):
    json_data = {
        'accountNumber': bank_acc[bank_name],
        'accountingEntry': 'ALL',
        'toDate': to_date,
        'fromDate': from_date,
    }

    response = requests.post(
        'https://ibank.machbank.com/expressBanking-client-web/api/Account/AcStatement',
        cookies=st.session_state.cookies,
        headers=headers,
        json=json_data,
    )

    data = json.loads(response.text)

    # Check if data is a list of dictionaries
    if isinstance(data, list) and all(isinstance(i, dict) for i in data):
        df = pd.DataFrame(data)
        st.write(df)
    else:
        st.error("Unexpected data format received.")
        st.write(data)

def set_extract(bank_name, to_date, from_date):
    json_data = {
        'fromDate': from_date,
        'toDate': to_date,
        'accountNumber': bank_acc[bank_name],
        'accountingEntry': 'ALL',
    }

    response = requests.post(
        'https://ibank.machbank.com/expressBanking-client-web/api/Account/downloadAcStatement/EXCEL',
        cookies=st.session_state.cookies,
        headers=st.session_state.headers,
        json=json_data,
    )
    return response

def download_statement(bank_name, to_date, from_date):
    save_name = 'bank_statement_{}-{}.xlsx'.format(from_date, to_date)
    response = set_extract(bank_name, to_date, from_date)
    
    with open(save_name, 'wb') as f:
        f.write(response.content)
    
    with open(save_name, 'rb') as f:
        st.download_button(label='Download Bank Statement', data=f, file_name=save_name)

def format_statement(bank_name, to_date, from_date):
    response = set_extract(bank_name, to_date, from_date)
    data = io.BytesIO(response.content)
    df = pd.read_excel(data)
    print(df)

    # Cleaning and formatting the DataFrame
    df = df.iloc[9:]
    df.columns = df.iloc[0]
    df = df.iloc[1:]
    df.dropna(axis=1, how='all', inplace=True)

    mask = df['Date'].str.contains('Record') | df['Date'].str.contains('Total Records :')
    df = df.drop(df.index[mask])

    df.fillna('0', inplace=True)
    df['Debit'] = df['Debit'].apply(lambda x: int(x.replace(',', '')) if isinstance(x, str) else x)
    df['Credit'] = df['Credit'].apply(lambda x: int(x.replace(',', '')) if isinstance(x, str) else x)
    df['Balance'] = df['Balance'].apply(lambda x: int(x.replace(',', '')) if isinstance(x, str) else x)

    save_name = '{}_bank_statement_{}-{}.xlsx'.format(bank_name, to_date, from_date)
    df.to_excel(save_name)

    with open(save_name, 'rb') as f:
        st.download_button(label='Download Formatted Bank Statement', data=f, file_name=save_name)

    return df

def combine(to_date, from_date):
    save_name = 'combined_bank_statement_{}-{}.xlsx'.format(from_date, to_date)
    
    writer = pd.ExcelWriter(save_name, engine='xlsxwriter')

    format_statement('j9', to_date, from_date).to_excel(writer, sheet_name='J9')
    format_statement('tg', to_date, from_date).to_excel(writer, sheet_name='TG')
    format_statement('tg usd', to_date, from_date).to_excel(writer, sheet_name='TG USD')
    format_statement('j9 usd', to_date, from_date).to_excel(writer, sheet_name='J9 USD')

    writer.close()

    with open(save_name, 'rb') as f:
        st.download_button(label='Download Combined Bank Statements', data=f, file_name=save_name)

    st.success("Download Complete !!!")


# Main function to render the MBL page
def MBL_page():
    st.title("MBL Bank Statement Manager")
    
    # Streamlit inputs for date range
    from_date = st.date_input("From Date", datetime.date(2024, 1, 1)).strftime('%Y-%m-%d')
    to_date = st.date_input("To Date", datetime.date.today()).strftime('%Y-%m-%d')

    if 'auth_token' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        headers = mbl_login()
        st.session_state.headers = headers

    if st.button("Login"):
         mbl_login()

    if st.session_state.logged_in:
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7,ne-NP;q=0.6,ne;q=0.5',
            'Authorization': st.session_state.auth_token,
            'Connection': 'keep-alive',
            'Referer': 'https://ibank.machbank.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        st.write("## View Bank Statement")
        bank_name = st.selectbox("Select Bank Account", list(bank_acc.keys()))
        if st.button("View Statement"):
            view_statement(bank_name, to_date, from_date, headers)

        st.write("## Download Bank Statement")
        if st.button("Download Statement"):
            download_statement(bank_name, to_date, from_date)

        st.write("## Format and Download Bank Statement")
        if st.button("Format and Download Statement"):
            format_statement(bank_name, to_date, from_date)

        st.write("## Combine Bank Statements into Single Excel File")
        if st.button("Combine Statements"):
            combine(to_date, from_date)

            
# MBL main function
def MBL_main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.error("You must be logged in to view this page.")
        st.stop()
    MBL_page()

if __name__ == "__main__":
    MBL_main()
