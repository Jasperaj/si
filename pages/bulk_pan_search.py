import streamlit as st
import time
import requests
import pandas as pd
import re
from bs4 import BeautifulSoup as bs

def convert_to_list(numbers_string):
    lines = numbers_string.split('\n')
    numbers_list = [int(line) for line in lines if line.strip().isdigit()]
    return numbers_list

def fetch_cookie_details(headers):
    r = requests.get(r'https://ird.gov.np/pan-search', headers=headers)
    cook = r.cookies._cookies
    bigserver = str(cook['ird.gov.np']['/']['BIGipServerIRD_Website'].value)
    xsrf = str(cook['ird.gov.np']['/']['XSRF-TOKEN'].value)
    ird_ses = str(cook['ird.gov.np']['/']['ird_session'].value)
    TS01 = str(cook['ird.gov.np']['/']['TS0144b6e1'].value)
    TS02 = str(cook['ird.gov.np']['/']['TS8de900db029'].value)
    return bigserver, xsrf, ird_ses, TS01, TS02, r.text

def fetch_token_and_sum_number(html_text):
    rn = bs(html_text, 'lxml')
    data = rn.find('div', {'id': 'mid'})
    num = re.findall(r'\d+', data.text)
    sum_number = sum(map(int, num))
    token = rn.find('input', {'id': '_token'})['value']
    return sum_number, token

st.title('PAN Details Extraction')

option = st.radio('How do you want to input PAN numbers?', ('Upload Excel File', 'Enter Manually'))

if option == 'Upload Excel File':
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, sheet_name="Party Name")
        bulkpan = df['Pan'].tolist()
else:
    numbers_string = st.text_area("Enter the PAN numbers, each on a new line")
    if numbers_string:
        bulkpan = convert_to_list(numbers_string)

if st.button('Fetch PAN Details'):
    if 'bulkpan' in locals():
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }

        bigserver, xsrf, ird_ses, TS01, TS02, html_text = fetch_cookie_details(headers)
        sum_number, token = fetch_token_and_sum_number(html_text)

        cookies = {
            'BIGipServerIRD_Website': bigserver,
            'XSRF-TOKEN': xsrf,
            'ird_session': ird_ses,
            'TS0144b6e1': TS01,
            'TS8de900db029': TS02,
        }

        headers.update({
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ta;q=0.8,ne;q=0.7',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://ird.gov.np',
            'Pragma': 'no-cache',
            'Referer': 'https://ird.gov.np/pan-search',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        })

        df = pd.DataFrame()

        for pan in bulkpan:
            data = {
                '_token': token,
                'pan': pan,
                'captcha': str(sum_number),
            }

            response = requests.post('https://ird.gov.np/statstics/getPanSearch', cookies=cookies, headers=headers, data=data)
            response_text = response.text

            try:
                res_total = eval(response_text.replace("root", "'root'").replace("null", "'null'").replace('false', "'False'").replace("message", "'message'").replace("success", "'success'").replace("total", "'total'"))
                if 'panDetails' in res_total:
                    pan_details = res_total['panDetails']
                    if isinstance(pan_details, list):
                        new_data = pd.DataFrame(pan_details)
                    elif isinstance(pan_details, dict):
                        new_data = pd.DataFrame([pan_details])
                    else:
                        new_data = pd.DataFrame(pan_details)
                    df = pd.concat([df, new_data], ignore_index=True)
                else:
                    st.write(f"'panDetails' key not found for PAN {pan}")

            except Exception as e:
                st.write(f"Error fetching details for PAN {pan}: {e}")

            time.sleep(2)

        st.write(df)
        df.to_excel('PAN-Details_Downloaded_v2.xlsx', sheet_name='Pan Updated')
        st.success('Data fetched successfully! File saved as PAN-Details_Downloaded_v2.xlsx')

