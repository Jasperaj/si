import pandas as pd
import json
import requests
import re
import xml.etree.ElementTree as ET
import streamlit as st
from io import BytesIO

def fetch_ledger_data(url, from_date, to_date, ledger_name):
    xml = f'''
    <ENVELOPE>
    <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
    </HEADER>
    <BODY>
    <EXPORTDATA>
    <REQUESTDESC>
    <REPORTNAME>Ledger Vouchers</REPORTNAME>
    <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
    <EXPLODEFLAG>No</EXPLODEFLAG>
    <EXPLODENARRFLAG>Yes</EXPLODENARRFLAG>
    <SHOWNARRATION>Yes</SHOWNARRATION>
    <SVFROMDATE>{from_date}</SVFROMDATE>
    <SVTODATE>{to_date}</SVTODATE>
    <LEDGERNAME>{ledger_name}</LEDGERNAME>
    </STATICVARIABLES>
    </REQUESTDESC>
    </EXPORTDATA>
    </BODY>
    </ENVELOPE>
    '''
    response = requests.post(url, data=xml)
    return ET.fromstring(response.text.encode("UTF-8"))

def process_ledger_data(root):
    column_head = ['Date', 'Ledger Account', 'Voucher Type', 'Debit', 'Credit', 'Voucher Date', 'Narration']
    voucher_models = []

    for x in root.iter():
        for date, party_name, name, info, vchtype, debit, credit in zip(
                x.iter('DSPVCHDATE'), x.iter('DSPVCHLEDACCOUNT'), x.iter('DSPVCHTYPE'),
                x.iter('DSPVCHDRAMT'), x.iter('DSPVCHCRAMT'), x.iter('DSPVCHDATE'),
                x.iter('VCHLEDNARREXPLOSION')):
            voucher_models.append(
                (date.text, party_name.text, name.text, info.text, vchtype.text, debit.text, credit.text))

    df = pd.DataFrame(voucher_models, columns=column_head)

    df['Date'] = df['Voucher Date'].fillna(method='ffill')
    df['Date'] = pd.to_datetime(df['Date'])
    df['Date'] = df['Date'].dt.strftime('%Y%m%d')
    df.drop(columns=['Voucher Date'], inplace=True)
    df['Debit'] = pd.to_numeric(df['Debit'])
    df['Credit'] = pd.to_numeric(df['Credit'])
    df['Amount'] = df[['Debit', 'Credit']].sum(axis=1)
    df['Date_Amount'] = df['Date'] + '_' + df['Amount'].astype(str)

    def extract_reference(narration):
        words = narration.split()
        for word in words:
            if re.search(r'\d', word):
                return word
        return None

    df['Ref. No.'] = df['Narration'].apply(extract_reference).astype(str)

    return df

def bank_reconciliation_page():
    st.title("Bank Reconciliation")

    url = st.text_input("Enter Tally URL", "http://localhost:9000/")
    from_date = st.date_input("Enter From Date")
    to_date = st.date_input("Enter To Date")
    ledger_name = st.text_input("Enter Ledger Name", "MBL -NPR  0400990684100012 -WE")

    if st.button("Fetch Ledger Data"):
        if url and from_date and to_date and ledger_name:
            from_date_str = from_date.strftime("%Y%m%d")
            print(from_date_str)
            to_date_str = to_date.strftime("%Y%m%d")

            with st.spinner("Fetching Ledger Data..."):
                root = fetch_ledger_data(url, from_date_str, to_date_str, ledger_name)
                ledger_df = process_ledger_data(root)

            st.success("Data Fetch Complete!")
            st.dataframe(ledger_df)

            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                ledger_df.to_excel(writer, index=False, sheet_name='Ledger Data')
            excel_buffer.seek(0)

            if st.button("Download Excel File"):
                st.download_button(
                    label="Download Ledger Data",
                    data=excel_buffer,
                    file_name='ledger_data.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        else:
            st.error("Please provide all the required inputs")

def bank_main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.error("You must be logged in to view this page.")
        st.stop()
    bank_reconciliation_page()

if __name__ == "__main__":
    bank_main()
