# pages/forex_today.py
import streamlit as st
import pandas as pd

def forex_main():
    st.title("💱 Forex Rates Today")

    if st.button("Get Today's Forex Rates"):
        with st.spinner("Fetching forex rates..."):
            df = get_forex_rates()
            if not df.empty:
                st.success("Forex rates fetched successfully.")
                st.dataframe(df)
            else:
                st.warning("Failed to fetch forex rates.")

def get_forex_rates():
    try:
        tables = pd.read_html('https://www.nrb.org.np/forex/')
        df = tables[1]
        return df
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    forex_main()
