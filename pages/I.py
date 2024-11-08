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
    current_path = os.getcwd() + '/' + output_name + '/'

    url = "{st.secrets['ird']}/taxpayer/app.html#"
    c = requests.Session()

    token_data = bs(c.get(url).text, 'html.parser')
    token = token_data.find_all('script')[1]['src'].replace('app.js?_dc=', "")
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}

    r = c.post(
        '{st.secrets['ird']}/Handlers/E-SystemServices/Taxpayer/TaxPayerValidLoginHandler.ashx',
        data={'pan': pan, 'TPName': username, 'TPPassword': password, 'formToken': 'a', 'pIP': '45.123.221.48'},
        headers=header)

    def vat():
        try:
            table_data = (bs(c.get(
                '{st.secrets['ird']}/Handlers/VAT/VatReturnsHandler.ashx?method=GetVatReturnList').text,
                             'lxml'))
            time.sleep(10)
            datas = table_data.find_all('p')
            d = datas[0].text
            match = re.search('root:(.*),message', d).group(1)
            res = json.loads(match)
            df_vat = pd.DataFrame(res)
            return df_vat
        except:
            result = {"SubmissionNo": ["No Data"], "Taxyear": ["No Data"], "Period": ["No Data"]}
            df_vat = pd.DataFrame(result)
            return df_vat

    def it():
        try:
            url = '{st.secrets['ird']}/Handlers/IncomeTax/D01/AssessmentSADoneHandler.ashx?method=GetListAssess'
            table_data = bs(c.post(url, headers=header, data={
                'start': '',
                'limit': '',
                'formType': '',
                'fiscalYear': '',
                'pan': pan,
                'submissionNo': '',
                'offCode': '',
                'fromDate': '',
                'toDate': '',
                'formToken': 'a'}).text, 'lxml')
            datas = table_data.find_all('p')
            d = datas[0].text
            match = re.search('root:(.*),message', d).group(1)
            res = json.loads(match)
            df_it = pd.DataFrame(res)
            return df_it
        except:
            result = {'AssessmentNo': ["No Data"], 'FiscalYear': ["No Data"]}
            df_it = pd.DataFrame(result)
            return df_it

    def tds():
        try:
            table_data = bs(c.get(
                '{st.secrets['ird']}/Handlers/TDS/GetTransactionHandler.ashx?method=GetWithholderRecs&_dc={}&objWith=%7B%22WhPan%22%3A%22{}%22%2C%22FromDate%22%3A%22{}%22%2C%22ToDate%22%3A%22{}%22%7D&page=1&start=0&limit=25'.format(
                    token, pan, fromdate, todate)).text, 'lxml')
            time.sleep(10)
            datas = table_data.find_all('p')
            d = datas[0].text
            match = re.search('root:(.*),message', d).group(1)
            res = json.loads(match)
            df_tds = pd.DataFrame(res)
            return df_tds
        except:
            result = {'TranNo': ['No ETDS Details Obtained']}
            df_tds = pd.DataFrame(result)
            return df_tds

    def annex10():
        try:
            url = '{st.secrets['ird']}/Handlers/RAS/PanCollectionHandler.ashx?method=GetPanAnnex10Vouchers&_dc={}&Voucher=%7B%22Pan%22%3A%22{}%22%2C%22Fy%22%3A%2220{}%22%7D&formToken=a&page=1&start=0&limit=25'.format(
                token, pan, fiscal_year)
            table_data = bs(c.get(url).text, 'lxml')
            time.sleep(10)
            datas = table_data.find_all('p')
            d = datas[0].text
            match = re.search('root:(.*),message', d).group(1)
            res = json.loads(match)
            df_annex10 = pd.DataFrame(res)
            return df_annex10
        except:
            result = {"Data": ['No Annex 10 TDS Receivable Details Obtained']}
            df_annex10 = pd.DataFrame(result)
            return df_annex10

    progress_text = "Operation in progress. Please wait..."
    progress_bar = st.progress(0)
    st.spinner(progress_text)

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
            st.session_state['excel_buffer'] = excel_buffer
            st.session_state['zip_buffer'] = zip_buffer
            st.success("Download Complete! You can download the files below.")

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
        else:
            st.error("Please provide all the required inputs")

def ird_main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.error("You must be logged in to view this page.")
        st.stop()
    ird_detail_download_page()
if __name__ == "__main__":
    ird_main()