import pyotp
from datetime import datetime, timedelta
import requests
import json
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

# Bank details dictionary
bank_details = {
    "HBL": ["0701", st.secrets["od"]],
    "MBL": ["1501", st.secrets["m_tg"]]
}

def get_code():
    secret = {
        'Name': '{}@'.format(st.secrets["cips_username"]),
        'Secret': st.secrets['cips_secret'],
        'Issuer': 'corproatePAY',
        'Type': 'totp'
    }
    otp = pyotp.TOTP(secret['Secret'])
    return otp.now()

def login_to_api():
    url = 'https://apicpay.connectips.com/login/temp'
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }
    data = {
        'username': st.secrets["cips_username"],
        'password': st.secrets["cips_password"],
        'corporateCode': st.secrets["cips_code"]
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Initial login failed with status code {response.status_code}: {response.text}")
        return None

def second_login():
    login_response = login_to_api()

    if not login_response:
        return None

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Basic MTIxMGRhZDRjbGllbnRpZDljYTE0bGl2ZTc1YjExOTE6MGFiZjNkZjBmMjRzZWNyZXQyMGZhZGQ0bGl2ZTkxYzA=',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }

    data = {
        'username': st.secrets["cips_username"],
        'password': st.secrets["cips_password"],
        'corporateCode': st.secrets["cips_code"],
        'qrCode': get_code(),
        'grant_type': 'password',
    }

    response = requests.post('https://apicpay.connectips.com/oauth/token', headers=headers, data=data)
    if response.status_code == 200:
        response_json = response.json()
        return response_json['access_token']
    else:
        st.error(f"Second login step failed with status code {response.status_code}: {response.text}")
        return None

def bank_login(bank_code, access_token):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    json_data = {
        'bankCode': bank_code,
        'corporateCode': st.secrets["cips_code"],
        'username': st.secrets["cips_username"],
        'password': st.secrets["cips_bankpassword"],
    }

    response = requests.post('https://apicpay.connectips.com/login/bank', headers=headers, json=json_data)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Bank login failed with status code {response.status_code}: {response.text}")
        return None

def check_balance(bank_code, bank_acc_no, access_token):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': f'Bearer {access_token}'
    }
    json_data = {
        'accountNumber': bank_acc_no,
        'bankCode': bank_code,
    }

    response = requests.post('https://apicpay.connectips.com/banks/user/account/balance', headers=headers, json=json_data)
    if response.status_code == 200:
        response_json = response.json()
        return response_json['responseData']['availableBalance']
    else:
        st.error(f"Balance check failed with status code {response.status_code}: {response.text}")
        return None

def pending_approval(bank_code, access_token, from_date, to_date):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    service_types = ['FUND_TRANSFER', 'BILL_PAYMENT']
    urls = ['https://apicpay.connectips.com/cips/transaction/pendings', 'https://apicpay.connectips.com/ips/billpay/pendings']
    df = pd.DataFrame()
    transaction_id = []

    for url in urls:
        for service_type in service_types:
            json_data = {
                'bankCode': bank_code,
                'fromDate': from_date.strftime("%Y-%m-%d"),
                'toDate': to_date.strftime("%Y-%m-%d"),
                'serviceType': service_type,
            }

            response = requests.post(url, headers=headers, json=json_data)
            if response.status_code == 200:
                response_json = response.json()
                if 'responseData' in response_json and response_json['responseData']:
                    transaction_id += response_json['responseData']
                    df_temp = pd.DataFrame(response_json['responseData'])
                    df = pd.concat([df, df_temp], ignore_index=True)
            else:
                st.error(f"Pending approval check failed with status code {response.status_code}: {response.text}")

    df_detail = pd.DataFrame(columns=['batchDetailId', 'Transfer Bank', 'Transfer Party', 'Transfer Account No'])

    for x in transaction_id:
        detail_url = f'https://apicpay.connectips.com/cips/transactions/{x["batchDetailId"]}'
        final = requests.get(detail_url, headers=headers)
        if final.status_code == 200:
            final_json = final.json().get('responseData', [])
            if final_json:
                final_json = final_json[0]
                batchid = x['batchDetailId']
                transfer_bank = final_json['creditorBankName']
                transfer_party = final_json['creditorAccountName']
                transfer_acc = final_json['creditorAccountNumber']
                new_row = pd.DataFrame([[batchid, transfer_bank, transfer_party, transfer_acc]], columns=df_detail.columns)
                df_detail = pd.concat([df_detail, new_row], ignore_index=True).drop_duplicates()
        else:
            st.error(f"Transaction detail fetch failed with status code {final.status_code}: {final.text}")

    if not df.empty and not df_detail.empty:
        try:
            df = df.merge(df_detail, on='batchDetailId', how='left').drop_duplicates()
        except Exception as e:
            st.error(f"Error merging dataframes: {e}")

    columns = [
        'cipsWaitingTransactionDetailId', 'batchDetailId', 'batchId', 'serviceName', 'batchAmount',
        'debtorAccountNumber', 'debtorAccountName', 'createdBy', 'createdAt', 'batchRemarks',
        'Transfer Bank', 'Transfer Party', 'Transfer Account No'
    ]

    return df[columns] if not df.empty else pd.DataFrame(columns=columns), df_detail

def approve(transaction_id, bank_code, access_token):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    json_data = {
        'bankCode': bank_code,
        'cipsWaitingTransactionDetailIds': [transaction_id],
        'otpCode': get_code(),
    }

    response = requests.post('https://apicpay.connectips.com/cips/transaction/approve', headers=headers, json=json_data)
    if response.status_code == 200:
        response_data = response.json()
        result = response_data['responseStatus']
        remark = response_data['responseMessage']
        return result, remark
    else:
        st.error(f"Approval failed with status code {response.status_code}: {response.text}")
        return None, None

def approve_all(df, bank_code, access_token):
    results = []
    for x in df['cipsWaitingTransactionDetailId']:
        result, remark = approve(x, bank_code, access_token)
        results.append((x, result, remark))
    return results

def get_details(bank_code, access_token, from_date, to_date):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    json_data = {
        'fromDate': from_date.strftime("%Y-%m-%d"),
        'toDate': to_date.strftime("%Y-%m-%d"),
        'bankCode': bank_code,
        'channelCode': 'CIPS',
        'pageable': {
            'currentPage': 1,
            'rowPerPage': 100,
        },
    }

    response = requests.post('https://apicpay.connectips.com/report/txn', headers=headers, json=json_data)
    if response.status_code == 200:
        response_json = response.json()
        details = response_json['responseData']['reports']
        df = pd.DataFrame(details)
        return df, df[['transactionDate', 'transactionDetailId', 'batchAmount', 'txnRemarks', 'creditReasonDesc', 'batchId', 'transactionAmount']]
    else:
        st.error(f"Details fetch failed with status code {response.status_code}: {response.text}")
        return pd.DataFrame(), pd.DataFrame()

def download_advice_pdf(detailid, filename, access_token):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    json_data = {
        'channelCode': 'CIPS',
        'transactionDetailId': detailid,
    }

    response = requests.post('https://apicpay.connectips.com/report/download/advice', headers=headers, json=json_data)
    if response.status_code == 200:
        with open(f'{filename}.pdf', 'wb') as f:
            f.write(response.content)
        with open(f'{filename}.pdf', 'rb') as file:
            st.download_button(
                label=f"Download {filename}.pdf",
                data=file,
                file_name=f"{filename}.pdf",
                mime='application/pdf'
            )
    else:
        st.error(f"Advice PDF download failed with status code {response.status_code}: {response.text}")

# Define the ConnectIPS page
def connectips_page():
    st.title("Bank Balance Checker")

    # Initialize session state for buttons
    if 'access_token' not in st.session_state:
        st.session_state['access_token'] = None

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if 'bank_balance_fetched' not in st.session_state:
        st.session_state['bank_balance_fetched'] = False

    if 'pending_approvals_fetched' not in st.session_state:
        st.session_state['pending_approvals_fetched'] = False

    if 'details_fetched' not in st.session_state:
        st.session_state['details_fetched'] = False

    # Ensure variables are initialized properly
    bank_code = None
    bank_acc_no = None

    # Button to perform initial login
    if st.button("Login ConnectIPS"):
        st.write("Logging in to API...")
        access_token = second_login()
        if access_token:
            st.write("Logged in successfully!")
            st.session_state['access_token'] = access_token
            st.session_state['logged_in'] = True
        else:
            st.error("Login failed. Please check your credentials.")

    # Ensure access_token is available before showing further options
    if st.session_state['logged_in']:
        bank_name = st.selectbox("Select Bank", options=list(bank_details.keys()))
        if bank_name:
            bank_code, bank_acc_no = bank_details[bank_name]

        from_date = st.date_input("From Date", value=(datetime.now() - timedelta(days=3)))
        to_date = st.date_input("To Date", value=datetime.now())

        if st.button("Get Bank Balance"):
            bank_code, bank_acc_no = bank_details[bank_name]
            access_token = st.session_state['access_token']
            st.write("Logging in to Bank...")
            bank_login_response = bank_login(bank_code, access_token)
            if bank_login_response:
                st.write("Checking balance...")
                balance = check_balance(bank_code, bank_acc_no, access_token)
                if balance is not None:
                    st.write(f"Available Balance for {bank_name}: {balance}")
                    st.session_state['bank_balance_fetched'] = True
                else:
                    st.error("Failed to fetch bank balance.")
            else:
                st.error("Bank login failed.")

        if st.session_state['bank_balance_fetched']:
            if st.button("Fetch Pending Approvals"):
                bank_code, bank_acc_no = bank_details[bank_name]
                access_token = st.session_state['access_token']
                st.write("Fetching pending approvals...")
                pending_df, pending_details_df = pending_approval(bank_code, access_token, from_date, to_date)
                if not pending_df.empty:
                    st.write("Pending Approvals:")
                    st.dataframe(pending_df)
                    st.session_state['pending_df'] = pending_df
                    st.session_state['pending_approvals_fetched'] = True
                else:
                    st.write("No pending approvals found.")

        if st.session_state['pending_approvals_fetched']:
            pending_df = st.session_state.get('pending_df', pd.DataFrame())
            selected_rows = st.multiselect("Select transactions to approve", pending_df.index)
            if st.button("Approve Selected"):
                for idx in selected_rows:
                    transaction_id = pending_df.loc[idx, 'cipsWaitingTransactionDetailId']
                    result, remark = approve(transaction_id, bank_code, st.session_state['access_token'])
                    st.write(f"Transaction ID {transaction_id} - Result: {result}, Remark: {remark}")

            if st.button("Approve All"):
                results = approve_all(pending_df, bank_code, st.session_state['access_token'])
                for transaction_id, result, remark in results:
                    st.write(f"Transaction ID {transaction_id} - Result: {result}, Remark: {remark}")

        if st.session_state['bank_balance_fetched']:
            if st.button("Get Details"):
                bank_code = bank_details[bank_name][0]
                access_token = st.session_state['access_token']
                st.write("Fetching details of approved payments...")
                details_df, selected_details_df = get_details(bank_code, access_token, from_date, to_date)
                if not details_df.empty:
                    st.write("Approved Payments Details:")
                    st.dataframe(details_df)
                    st.session_state['details_df'] = details_df
                    st.session_state['details_fetched'] = True
                else:
                    st.write("No approved payment details found.")

        if st.session_state['details_fetched']:
            details_df = st.session_state.get('details_df', pd.DataFrame())
            selected_detail_rows = st.multiselect("Select details to download", details_df.index)
            if st.button("Download Selected Details"):
                for idx in selected_detail_rows:
                    detailid = details_df.loc[idx, 'transactionDetailId']
                    filename = f"Connectips_report_{detailid}"
                    download_advice_pdf(detailid, filename, st.session_state['access_token'])

            if st.button("Download All Details"):
                for idx, row in details_df.iterrows():
                    detailid = row['transactionDetailId']
                    filename = f"Connectips_report_{detailid}"
                    download_advice_pdf(detailid, filename, st.session_state['access_token'])

# Main function to run the ConnectIPS page
def connectips_main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.error("You must be logged in to view this page.")
        st.stop()
    connectips_page()

if __name__ == "__main__":
    connectips_main()
