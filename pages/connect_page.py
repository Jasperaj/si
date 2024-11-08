# Add this function to save generated file content to session state
def save_file_to_session_state(key, content):
    if key not in st.session_state:
        st.session_state[key] = content

# Update the download functions to store data in the session state
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
        # Save the PDF content to session state
        save_file_to_session_state(f'{filename}_content', response.content)

        # Provide a Streamlit download button using the saved content
        st.download_button(
            label=f"Download {filename}.pdf",
            data=st.session_state[f'{filename}_content'],
            file_name=f"{filename}.pdf",
            mime='application/pdf'
        )
    else:
        st.error(f"Failed to download advice PDF for {detailid}. Status code: {response.status_code}")

# Ensure download buttons are always visible in the session state
def display_download_buttons(details_df):
    for idx, row in details_df.iterrows():
        detailid = row['transactionDetailId']
        filename = f"Connectips_report_{detailid}"

        # Display download button for each file if content exists in session state
        if f'{filename}_content' in st.session_state:
            st.download_button(
                label=f"Download {filename}.pdf",
                data=st.session_state[f'{filename}_content'],
                file_name=f"{filename}.pdf",
                mime='application/pdf'
            )

def connectips_page():
    st.title("Bank Balance Checker")

    # Ensure session state keys are initialized
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

    # Main login and operations logic
    if st.button("Login ConnectIPS"):
        st.write("Logging in to API...")
        access_token = second_login()
        if access_token:
            st.write("Logged in successfully!")
            st.session_state['access_token'] = access_token
            st.session_state['logged_in'] = True
        else:
            st.error("Login failed. Please check your credentials.")

    if st.session_state['logged_in']:
        bank_name = st.selectbox("Select Bank", options=list(bank_details.keys()))
        if bank_name:
            bank_code, bank_acc_no = bank_details[bank_name]

        from_date = st.date_input("From Date", value=(datetime.now() - timedelta(days=3)))
        to_date = st.date_input("To Date", value=datetime.now())

        if st.button("Get Bank Balance"):
            access_token = st.session_state['access_token']
            st.write("Logging in to Bank...")
            if bank_login(bank_code, access_token):
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
                access_token = st.session_state['access_token']
                st.write("Fetching pending approvals...")
                pending_df, _ = pending_approval(bank_code, access_token, from_date, to_date)
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

        if st.session_state['bank_balance_fetched']:
            if st.button("Get Details"):
                access_token = st.session_state['access_token']
                st.write("Fetching details of approved payments...")
                details_df, _ = get_details(bank_code, access_token, from_date, to_date)
                if not details_df.empty:
                    st.write("Approved Payments Details:")
                    st.dataframe(details_df)
                    st.session_state['details_df'] = details_df
                    st.session_state['details_fetched'] = True
                else:
                    st.write("No approved payment details found.")

        if st.session_state['details_fetched']:
            details_df = st.session_state.get('details_df', pd.DataFrame())
            if st.button("Download All Details"):
                for idx, row in details_df.iterrows():
                    detailid = row['transactionDetailId']
                    filename = f"Connectips_report_{detailid}"
                    download_advice_pdf(detailid, filename, st.session_state['access_token'])

            # Display download buttons for already downloaded files
            display_download_buttons(details_df)

def connectips_main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.error("You must be logged in to view this page.")
        st.stop()
    connectips_page()

if __name__ == "__main__":
    connectips_main()
