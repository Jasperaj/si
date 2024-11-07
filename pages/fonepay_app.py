import streamlit as st
import requests
import pandas as pd
import time
from datetime import date

def fonepay_main():
    # Streamlit web app
    st.title('Fonepay Integration')

    # Sidebar for page navigation
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose the app mode", ["Fonepay"])

    # Fonepay Page
    if app_mode == "Fonepay":
        st.header('Fonepay Transaction Report')

        # User input for date range
        from_today = st.date_input("From Date")
        to_today = st.date_input("To Date")

        from_today_str = from_today.strftime("%Y-%m-%d")
        to_today_str = to_today.strftime("%Y-%m-%d")

        st.write(f"Date range: {from_today_str} to {to_today_str}")

        # Input for Fonepay login details with default values
        fonepay_username = st.text_input("Enter Fonepay Username:", value="finance2@rrgroup.com.np")
        fonepay_password = st.text_input("Enter Fonepay Password:", value="Astr@0201", type="password")

        # Login to Fonepay
        if st.button("Login to Fonepay"):
            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Authorization': 'null',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Origin': 'https://login.fonepay.com',
                'Referer': 'https://login.fonepay.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
            }
            json_data = {
                'username': fonepay_username,
                'password': fonepay_password,
                'secretKey': '',
                'otpCode': '',
                'recaptcha': '',
            }
            response = requests.post('https://merchantapi.fonepay.com/authentication/login', headers=headers, json=json_data)

            # Print response for debugging
            st.write("Response Status Code:", response.status_code)
            st.write("Response Content:", response.content.decode())

            if response.status_code in [200, 202]:
                new_token = response.headers.get("Authorization")
                st.success("Logged in successfully!")

                # Polling mechanism for status 202
                if response.status_code == 202:
                    st.write("Processing the request, please wait...")
                    time.sleep(5)  # Wait for 5 seconds before polling

                # Fetch transaction report
                headers['Authorization'] = new_token
                params = {
                    'pageNumber': '1',
                    'pageSize': '25',
                    'fromTransmissionDateTime': from_today_str,
                    'toTransmissionDateTime': to_today_str,
                }
                json_data = {
                    'id': None,
                    'type': None,
                }
                report_response = requests.post(
                    'https://merchantapi.fonepay.com/report/merchant-Settlement-report',
                    params=params,
                    headers=headers,
                    json=json_data,
                )

                st.write("Report Response Status Code:", report_response.status_code)
                st.write("Report Response Content:", report_response.content.decode())

                # Download transaction report
                download_response = requests.post(
                    'https://merchantapi.fonepay.com/report/download-merchant-payment-details-default',
                    params=params,
                    headers=headers,
                )

                download = eval(download_response.content.decode().replace('true', "'true'"))

                try:
                    new = download['searchedDataList']
                    data = pd.DataFrame(new)
                    data['transactionAmount'] = pd.to_numeric(data['transactionAmount'], errors='coerce')
                    desired_order = ['sessionNumber', 'transmissionDateTime', 'initiator', 'fonepayTransactionId', 'transactionAmount', 'remarks1', 'remarks2', 'refund']
                    data = data.reindex(columns=desired_order + list(data.columns.difference(desired_order)))
                    output_file = f'Fonepay_{from_today_str}_{to_today_str}.xlsx'
                    data.to_excel(output_file)
                    st.dataframe(data)  # Display interactive table
                    st.success(f"Data saved to {output_file}")

                    # Provide download link for the Excel file
                    with open(output_file, "rb") as f:
                        st.download_button(label="Download Excel file", data=f, file_name=output_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                except Exception as e:
                    st.error(f"Error processing data: {e}")
                    data = pd.DataFrame(["Empty for the day"])
                    output_file = f'Fonepay_{from_today_str}_{to_today_str}.xlsx'
                    data.to_excel(output_file)
                    st.dataframe(data)  # Display interactive table
                    st.warning("No data available for the selected date range.")
                    st.success(f"Data saved to {output_file}")

                    # Provide download link for the Excel file
                    with open(output_file, "rb") as f:
                        st.download_button(label="Download Excel file", data=f, file_name=output_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            else:
                st.error("Login failed! Please check your credentials.")

if __name__ == '__main__':
    fonepay_main()
