import os
import re
import json
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import streamlit as st
from io import BytesIO
from zipfile import ZipFile

def ird_detail_download(output_name, pan, username, password, fromdate, todate, fiscal_year):
    os.makedirs(output_name, exist_ok=True)
    current_path = os.path.join(os.getcwd(), output_name)

    base_url = st.secrets["ird"]
    url = f'{base_url}/taxpayer/app.html#'
    c = requests.Session()

    try:
        token_data = bs(c.get(url).text, 'html.parser')
        token = token_data.find_all('script')[1]['src'].replace('app.js?_dc=', "")
        st.write("Token obtained successfully.")
    except Exception as e:
        st.error(f"Error obtaining token: {e}")
        st.write("Traceback details:", exc_info=True)
        return None, None

    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
    }

    try:
        r = c.post(
            f'{base_url}/Handlers/E-SystemServices/Taxpayer/TaxPayerValidLoginHandler.ashx',
            data={'pan': pan, 'TPName': username, 'TPPassword': password, 'formToken': 'a', 'pIP': '45.123.221.48'},
            headers=header
        )
        if r.status_code != 200:
            st.error(f"Login request failed with status code {r.status_code}. Response: {r.text}")
            return None, None
        st.write("Login successful.")
    except Exception as e:
        st.error(f"Error during login: {e}")
        st.write("Traceback details:", exc_info=True)
        return None, None

    def vat():
        try:
            with st.spinner('Fetching VAT data...'):
                response = c.get(f'{base_url}/Handlers/VAT/VatReturnsHandler.ashx?method=GetVatReturnList')
                response.raise_for_status()
                table_data = bs(response.text, 'lxml')
                time.sleep(5)
                datas = table_data.find_all('p')
                d = datas[0].text
                match = re.search('root:(.*),message', d).group(1)
                res = json.loads(match)
                df_vat = pd.DataFrame(res)
                st.write("VAT data fetched successfully.")
                return df_vat
        except Exception as e:
            st.error(f"Error fetching VAT data: {e}")
            st.write("Traceback details:", exc_info=True)
            return pd.DataFrame({"SubmissionNo": ["No Data"], "Taxyear": ["No Data"], "Period": ["No Data"]})

    def it():
        try:
            with st.spinner('Fetching IT data...'):
                url = f'{base_url}/Handlers/IncomeTax/D01/AssessmentSADoneHandler.ashx?method=GetListAssess'
                response = c.post(url, headers=header, data={'pan': pan, 'formToken': 'a'})
                response.raise_for_status()
                table_data = bs(response.text, 'lxml')
                datas = table_data.find_all('p')
                d = datas[0].text
                match = re.search('root:(.*),message', d).group(1)
                res = json.loads(match)
                df_it = pd.DataFrame(res)
                st.write("IT data fetched successfully.")
                return df_it
        except Exception as e:
            st.error(f"Error fetching IT data: {e}")
            st.write("Traceback details:", exc_info=True)
            return pd.DataFrame({'AssessmentNo': ["No Data"], 'FiscalYear': ["No Data"]})

    def tds():
        try:
            with st.spinner('Fetching TDS data...'):
                url = f'{base_url}/Handlers/TDS/GetTransactionHandler.ashx?method=GetWithholderRecs&_dc={token}&objWith=%7B%22WhPan%22%3A%22{pan}%22%2C%22FromDate%22%3A%22{fromdate}%22%2C%22ToDate%22%3A%22{todate}%22%7D&page=1&start=0&limit=25'
                response = c.get(url)
                response.raise_for_status()
                table_data = bs(response.text, 'lxml')
                time.sleep(5)
                datas = table_data.find_all('p')
                d = datas[0].text
                match = re.search('root:(.*),message', d).group(1)
                res = json.loads(match)
                df_tds = pd.DataFrame(res)
                st.write("TDS data fetched successfully.")
                return df_tds
        except Exception as e:
            st.error(f"Error fetching TDS data: {e}")
            st.write("Traceback details:", exc_info=True)
            return pd.DataFrame({'TranNo': ['No ETDS Details Obtained']})

    def annex10():
        try:
            with st.spinner('Fetching Annex 10 data...'):
                url = f'{base_url}/Handlers/RAS/PanCollectionHandler.ashx?method=GetPanAnnex10Vouchers&_dc={token}&Voucher=%7B%22Pan%22%3A%22{pan}%22%2C%22Fy%22%3A%2220{fiscal_year}%22%7D&formToken=a&page=1&start=0&limit=25'
                response = c.get(url)
                response.raise_for_status()
                table_data = bs(response.text, 'lxml')
                time.sleep(5)
                datas = table_data.find_all('p')
                d = datas[0].text
                match = re.search('root:(.*),message', d).group(1)
                res = json.loads(match)
                df_annex10 = pd.DataFrame(res)
                st.write("Annex 10 data fetched successfully.")
                return df_annex10
        except Exception as e:
            st.error(f"Error fetching Annex 10 data: {e}")
            st.write("Traceback details:", exc_info=True)
            return pd.DataFrame({"Data": ['No Annex 10 TDS Receivable Details Obtained']})

    progress_text = "Operation in progress. Please wait..."
    progress_bar = st.progress(0)

    df_vat = vat()
    progress_bar.progress(25)

    df_it = it()
    progress_bar.progress(50)

    df_tds = tds()
    progress_bar.progress(75)

    df_annex10 = annex10()
    progress_bar.progress(100)

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_vat.to_excel(writer, sheet_name='VAT')
        df_tds.to_excel(writer, sheet_name='TDS')
        df_annex10.to_excel(writer, sheet_name='Annex_10_Map')
        df_it.to_excel(writer, sheet_name='IT')

    excel_buffer.seek(0)

    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, 'w') as zip_file:
        for folder, subfolders, files in os.walk(current_path):
            for file in files:
                zip_file.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder, file), current_path))

    zip_buffer.seek(0)

    # Save buffers to session state
    st.session_state['excel_buffer'] = excel_buffer
    st.session_state['zip_buffer'] = zip_buffer

    return excel_buffer, zip_buffer

def ird_detail_download_page():
    st.title("IRD Detail Download")

    output_name = st.text_input("Enter Output Name")
    pan = st.text_input("Enter PAN")
    username = st.text_input("Enter Username")
    password = st.text_input("Enter Password", type="password")
    fromdate = st.date_input("From Date")
    todate = st.date_input("To Date")
    fiscal_year = st.text_input("Enter Fiscal Year")

    if st.button("Download IRD Details"):
        if output_name and pan and username and password and fromdate and todate and fiscal_year:
            excel_buffer, zip_buffer = ird_detail_download(
                output_name, pan, username, password, fromdate.strftime("%Y.%m.%d"), todate.strftime("%Y.%m.%d"), fiscal_year
            )
            if excel_buffer and zip_buffer:
                st.success("Download Complete! You can download the files below.")

    # Show download buttons if buffers are available in session state
    if 'excel_buffer' in st.session_state and 'zip_buffer' in st.session_state:
        st.download_button(
            label="Download Excel file",
            data=st.session_state['excel_buffer'],
            file_name=f'{output_name}_{fiscal_year}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        st.download_button(
            label="Download Zipped Documents",
            data=st.session_state['zip_buffer'],
            file_name=f'{output_name}.zip',
            mime='application/zip'
        )

def ird_main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.error("You must be logged in to view this page.")
        st.stop()
    ird_detail_download_page()

if __name__ == "__main__":
    ird_main()
