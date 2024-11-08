import streamlit as st
import requests
import pandas as pd
import toml
import plotly.express as px

# Load secrets from your datastore.toml file
st.secrets = toml.load("D:/OneDrive - Curves colors/Desktop/steamlit_app/pages/datastore.toml")

def main():
    st.title("Meroshare Dashboard")
    
    tab1, tab2 = st.tabs(["Portfolio Viewer", "IPO Application"])
    
    with tab1:
        portfolio_main()
    
    with tab2:
        ipo_application_main()

def login(dp, username, password):
    headers = {
        'User-Agent': 'Mozilla/5.0',
    }

    json_data = {
        'clientId': int(dp),
        'username': username,
        'password': password,
    }

    session = requests.Session()
    response = session.post('https://webbackend.cdsc.com.np/api/meroShare/auth/', headers=headers, json=json_data)
    if response.status_code != 200:
        st.error("Login failed. Please check your credentials.")
        return None, None

    new_token = response.headers.get("Authorization")
    if not new_token:
        st.error("Failed to retrieve authorization token.")
        return None, None

    headers['Authorization'] = new_token
    return session, headers

def portfolio_main():
    st.header("📈 Meroshare Portfolio Viewer")

    # Get the list of users from st.secrets
    users = st.secrets["all"].keys()
    user_selection = st.selectbox("Select a user:", users)

    if st.button("View Portfolio"):
        with st.spinner(f"Fetching portfolio for {user_selection}..."):
            try:
                # Retrieve login credentials for the selected user
                user_data = st.secrets["all"][user_selection]
                dp = user_data["dp"]
                username = user_data["username"]
                password = user_data["password"]

                # Login and fetch portfolio data
                session, headers = login(dp, username, password)
                if session is None:
                    return

                portfolio_df = fetch_portfolio(session, headers)
                if portfolio_df is not None:
                    st.success(f"Portfolio fetched successfully for {user_selection}.")
                    st.dataframe(portfolio_df)
                    generate_dashboard(portfolio_df)
                else:
                    st.error("Failed to fetch portfolio.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

def fetch_portfolio(session, headers):
    # Get user details
    mydetail = session.get('https://webbackend.cdsc.com.np/api/meroShare/ownDetail/', headers=headers)
    if mydetail.status_code != 200:
        st.error("Failed to retrieve user details.")
        return None

    mydetail = mydetail.json()
    demat = mydetail['demat']
    clientCode = mydetail['clientCode']

    # Fetch portfolio
    json_data = {
        'sortBy': 'script',
        'demat': [demat],
        'clientCode': clientCode,
        'page': 1,
        'size': 200,
        'sortAsc': True,
    }

    portfolio = session.post('https://webbackend.cdsc.com.np/api/meroShareView/myPortfolio/', headers=headers, json=json_data)
    if portfolio.status_code != 200:
        st.error("Failed to retrieve portfolio data.")
        return None

    portfolio_data = portfolio.json()
    df = pd.DataFrame(portfolio_data['meroShareMyPortfolio'])
    # Process the dataframe as needed
    return df

def generate_dashboard(df):
    # Ensure columns are numeric for calculations
    df['currentBalance'] = pd.to_numeric(df['currentBalance'], errors='coerce')
    df['lastTransactionPrice'] = pd.to_numeric(df['lastTransactionPrice'], errors='coerce')
    df['previousClosingPrice'] = pd.to_numeric(df['previousClosingPrice'], errors='coerce')

    # Handle any NaN values that may have resulted from conversion issues
    df = df.dropna(subset=['currentBalance', 'lastTransactionPrice', 'previousClosingPrice'])

    # Calculate the total portfolio values
    df['valueOfLastTransPrice'] = df['currentBalance'] * df['lastTransactionPrice']
    df['valueOfPrevClosingPrice'] = df['currentBalance'] * df['previousClosingPrice']

    total_current_value = df['valueOfLastTransPrice'].sum()
    total_previous_value = df['valueOfPrevClosingPrice'].sum()

    # Calculate the percentage change between current and previous values
    value_change_percentage = ((total_current_value - total_previous_value) / total_previous_value) * 100 if total_previous_value != 0 else 0

    # Determine color based on gain or loss
    if value_change_percentage > 0:
        change_color = 'green'
    elif value_change_percentage < 0:
        change_color = 'red'
    else:
        change_color = 'black'

    # Find top valued stock
    top_valued_stock = df.loc[df['valueOfLastTransPrice'].idxmax()]

    # Find lowest valued stock
    lowest_valued_stock = df.loc[df['valueOfLastTransPrice'].idxmin()]

    # Display portfolio summary in the app
    st.subheader("Portfolio Summary")
    st.write(
        f"**Total Current Portfolio Value:** "
        f"<span style='color:black;'>{total_current_value:,.2f}</span>",
        unsafe_allow_html=True
    )
    st.write(
        f"**Total Previous Portfolio Value:** "
        f"<span style='color:black;'>{total_previous_value:,.2f}</span>",
        unsafe_allow_html=True
    )
    st.write(
        f"**Change in Portfolio Value:** "
        f"<span style='color:{change_color};'>{value_change_percentage:.2f}%</span>",
        unsafe_allow_html=True
    )
    st.write(f"**Top Valued Stock:** {top_valued_stock['script']} - Value: {top_valued_stock['valueOfLastTransPrice']:,.2f}")
    st.write(f"**Lowest Valued Stock:** {lowest_valued_stock['script']} - Value: {lowest_valued_stock['valueOfLastTransPrice']:,.2f}")

    # Generate an interactive pie chart with Plotly
    st.subheader("Portfolio Distribution by Stock Value")
    fig = px.pie(
        df,
        values='valueOfLastTransPrice',
        names='script',
        title='Portfolio Distribution by Stock Value',
        hover_data={'valueOfLastTransPrice': ':,.2f'},
        labels={'valueOfLastTransPrice': 'Total Value'}
    )
    fig.update_traces(textinfo='percent', hovertemplate='<b>%{label}</b><br>Total Value: %{value:,.2f}<extra></extra>')

    st.plotly_chart(fig)

def ipo_application_main():
    st.header("💼 IPO Application")

    # Get the list of users from st.secrets
    users = st.secrets["all"].keys()
    user_selection = st.selectbox("Select a user for IPO application:", users)
    
    # Retrieve login credentials for the selected user
    user_data = st.secrets["all"][user_selection]
    dp = user_data["dp"]
    username = user_data["username"]
    password = user_data["password"]

    # IPO Application Section
    st.subheader("Apply for IPO")

    if st.button("Check Available IPOs"):
        with st.spinner(f"Fetching available IPOs for {user_selection}..."):
            try:
                # Login and create session
                session, headers = login(dp, username, password)
                if session is None:
                    return

                ipo_list = fetch_available_ipos(session, headers)
                if ipo_list is None or len(ipo_list) == 0:
                    st.info("No IPOs available at the moment.")
                    return

                # Display available IPOs
                ipo_options = [f"{ipo['companyShare']['name']} ({ipo['issueOpenDateBS']} - {ipo['issueCloseDateBS']})" for ipo in ipo_list]
                ipo_selection = st.selectbox("Select an IPO to apply for:", ipo_options)

                # Get the selected IPO details
                selected_ipo = ipo_list[ipo_options.index(ipo_selection)]

                max_qty = selected_ipo['maxKitta']
                min_qty = selected_ipo['minKitta']
                quantity = st.number_input(f"Enter quantity ({min_qty} - {max_qty}):", min_value=min_qty, max_value=max_qty, step=1)

                if st.button("Apply for Selected IPO"):
                    with st.spinner("Processing IPO application..."):
                        # Login again to ensure session is fresh
                        session, headers = login(dp, username, password)
                        if session is None:
                            return

                        result = apply_for_ipo(session, headers, selected_ipo, quantity, user_data)
                        if result:
                            st.success(f"Successfully applied for {quantity} shares of {selected_ipo['companyShare']['name']}.")
                        else:
                            st.error("Failed to apply for IPO.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Application Report Section
    st.subheader("Application Report")

    if st.button("View Application Report"):
        with st.spinner(f"Fetching application report for {user_selection}..."):
            try:
                # Login and create session
                session, headers = login(dp, username, password)
                if session is None:
                    return

                report_df = fetch_application_report(session, headers)
                if report_df is not None and not report_df.empty:
                    st.success("Application report fetched successfully.")
                    st.dataframe(report_df)
                else:
                    st.info("No application records found.")
            except Exception as e:
                st.error(f"An error occurred while fetching the application report: {e}")


def fetch_available_ipos(session, headers):
    response = session.get('https://webbackend.cdsc.com.np/api/meroShare/companyShare/applicableIssue/', headers=headers)
    if response.status_code != 200:
        st.error("Failed to fetch available IPOs.")
        return None
    ipo_list = response.json()['object']
    return ipo_list

def apply_for_ipo(session, headers, selected_ipo, quantity, user_data):
    # Fetch applicant details
    applicant_details = fetch_applicant_details(session, headers)
    if applicant_details is None:
        return False
    applicant_id = applicant_details['id']


    # For simplicity, select the first bank account
    bank_account = bank_accounts[0]
    bank_id = bank_account['bank']['id']
    account_number = bank_account['accountNumber']
    crn_number = bank_account['crnNumber']
    branch_id = bank_account['branch']['id']

    # Ensure transaction PIN is provided
    transaction_pin = user_data.get("transactionPIN")
    if not transaction_pin:
        st.error("Transaction PIN is missing in the datastore.toml file.")
        return False

    # Prepare application data
    application_data = {
        "companyShareId": selected_ipo['companyShareId'],
        "shareGroupId": selected_ipo['shareGroupId'],
        "applicantId": applicant_id,
        "bankId": bank_id,
        "bankAccountId": bank_account['id'],
        "accountBranchId": branch_id,
        "appliedKitta": int(quantity),
        "crnNumber": crn_number,
        "transactionPIN": transaction_pin,
    }

    # Send application request
    response = session.post('https://webbackend.cdsc.com.np/api/meroShare/applicantForm/share/apply', headers=headers, json=application_data)
    if response.status_code == 200:
        return True
    else:
        error_message = response.json().get('message', 'Unknown error')
        st.error(f"Failed to apply for IPO: {error_message}")
        return False

def fetch_applicant_details(session, headers):
    response = session.get('https://webbackend.cdsc.com.np/api/meroShare/applicantForm/detail/', headers=headers)
    if response.status_code != 200:
        st.error("Failed to fetch applicant details.")
        return None
    applicant_details = response.json()['applicant']
    return applicant_details



def fetch_application_report(session, headers):
    data = {
        "filterFieldParams": [
            {"key": "companyShare.companyIssue.companyISIN.script", "alias": "Scrip"},
            {"key": "companyShare.companyIssue.companyISIN.company.name", "alias": "Company Name"}
        ],
        "page": 1,
        "size": 200,
        "searchRoleViewConstants": "VIEW_APPLICANT_FORM_COMPLETE",
        "filterDateParams": [
            {"key": "appliedDate", "condition": "", "alias": "", "value": ""},
            {"key": "appliedDate", "condition": "", "alias": "", "value": ""}
        ]
    }

    response = session.post(
        'https://webbackend.cdsc.com.np/api/meroShare/applicantForm/active/search/',
        headers=headers, json=data)
    if response.status_code != 200:
        st.error("Failed to fetch application report.")
        return None

    report_data = response.json()
    applications = report_data.get('object', [])
    if not applications:
        return pd.DataFrame()  # Return empty DataFrame if no applications

    df = pd.DataFrame(applications)

    return df


if __name__ == "__main__":
    main()
