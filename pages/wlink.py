import streamlit as st
import requests
import json

# Dictionary containing username and password details
detail = {'jazeera': 'mKq6Tt', 'thaismile': '59RG1d'}

def worldlink(username, password):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7,ne-NP;q=0.6,ne;q=0.5',
        'authorization': '',
        'content-type': 'application/json',
        'origin': 'https://customer-portal.worldlink.com.np',
        'priority': 'u=1, i',
        'referer': 'https://customer-portal.worldlink.com.np/',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }

    json_data = {
        'username': username,
        'password': password,
    }

    response = requests.post('https://customerportal-api.worldlink.com.np/v1/auth/login', headers=headers, json=json_data)
    json_authorization = json.loads(response.text)['response']['access_token']

    headers['Authorization'] = f'Bearer {json_authorization}'

    data = requests.get('https://customerportal-api.worldlink.com.np/v1/customer/internet_subscription', headers=headers)
    json_response = json.loads(data.text)
    return json_response['response']['remaining_days']

def wlink_page():
    st.title("WorldLink Subscription Checker")

    selected_account = st.selectbox("Select an account", list(detail.keys()))

    if st.button("Check Remaining Days"):
        username = selected_account
        password = detail[selected_account]
        remaining_days = worldlink(username, password)
        st.write(f"Remaining days for {username}: {remaining_days}")

def wlink_main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.error("You must be logged in to view this page.")
        st.stop()
    wlink_page()


if __name__ == "__main__":
    wlink_main()
