import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import streamlit as st
from datetime import datetime  # Import the datetime module
def nea(payer, from_date, to_date):
    bill_payer = {
        'UTTAM': {
            'location': "NAXAL",
            'sc_no': '007.18.033',
            'consumer_id': '102758'
        },
        'J9': {
            'location': "NAXAL",
            'sc_no': '010.02.403',
            'consumer_id': '101432'
        }
    }

    NEA_location = bill_payer.get(payer).get('location')
    sc_no = bill_payer.get(payer).get('sc_no')
    consumer_id = bill_payer.get(payer).get('consumer_id')

    cookies = {
        'ASPSESSIONIDQUAACSDT': 'MFEDEKPCBEGGOBDBPJOPGGPN',
    }

    headers = {
        'authority': 'www.neabilling.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }

    list_details = requests.get('https://www.neabilling.com/viewonline/', cookies=cookies, headers=headers)

    data = bs(list_details.text, 'lxml')
    table_data = data.find_all('option')

    dict_table = {'Area': 'Code'}
    for table in table_data:
        dict_table[table.text] = table['value']

    location_code = dict_table.get(NEA_location)

    data = {
        'NEA_location': location_code,
        'sc_no': sc_no,
        'consumer_id': consumer_id,
        'Fromdatepicker': from_date,
        'Todatepicker': to_date,
    }

    response = requests.post('https://www.neabilling.com/viewonline/viewonlineresult/', cookies=cookies, headers=headers, data=data)

    soup = bs(response.text, 'html.parser')

    # Extracting the table rows
    rows = soup.find_all('tr')[5:]  # Skipping initial rows that don't contain data

    table_data = []
    for row in rows:
        cells = row.find_all(['td', 'th'])
        row_data = [cell.get_text(strip=True) for cell in cells]
        table_data.append(row_data)

    # Formatting the extracted data
    headers = ["SNo", "STATUS", "DUE BILL OF", "BILL DATE", "CONSUMED UNITS", "BILL AMT", "REBATE", "RATE", "PAYABLE AMOUNT", "PAID AMOUNT", "PAID VIA MERCHANT", "MERCHANT PARTNER TXN ID", "PAID DATE"]
    table_data.insert(0, headers)

    # Creating a DataFrame
    df = pd.DataFrame(table_data[1:], columns=headers)

    return df

def nea_bill_check_page():
    st.title("NEA Bill Check")

    payer = st.selectbox("Select Payer", ["UTTAM", "J9"])
    from_date = st.date_input("From Date", datetime(2023, 1, 23))
    to_date = st.date_input("To Date", datetime(2024, 1, 28))

    if st.button("Check Bill"):
        df = nea(payer, from_date.strftime("%m/%d/%Y"), to_date.strftime("%m/%d/%Y"))
        st.dataframe(df)

def nea_main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.error("You must be logged in to view this page.")
        st.stop()
    nea_bill_check_page()


if __name__ == "__main__":
    nea_main()
