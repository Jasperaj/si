import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Function to load data
@st.cache_data(ttl=60)
def fetch_flight_data():
    # Define cookies and headers for the request
    cookies = {
        '_gid': 'GA1.3.635490386.1730857905',
        'october_session': 'eyJpdiI6IlArMG5teXJtZVg5ZmhyNG9NY05STEE9PSIsInZhbHVlIjoidzZYQUwrS3dYVVlJemRLa0JGYUp0STcrZEk4R3NqN1J6ZXBaalVvSVwvb1BzZmdFOFFqbWVZUDNrVjVPTURTOWRKNERMTktFamVoaUtNSFFxeDBVUzZBPT0iLCJtYWMiOiJhODJlZDJlNTcwYzA4NWU0MjlmMWI5OWY4ZmMwZTAyNjY0Zjg3ZWM2YmI0MmU3ODY5ODdjYzM3NmUyOTY1NzNjIn0%3D',
        '_ga_7Y4Y8EDM00': 'GS1.1.1730857905.1.1.1730858000.60.0.0',
        '_ga': 'GA1.3.1761389800.1730857905',
        '_gat_gtag_UA_135387528_1': '1',
    }

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://www.tiairport.com.np/all-flights',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    }

    response = requests.get('https://www.tiairport.com.np/flight_details_2', cookies=cookies, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        df_arrivals = pd.DataFrame(data['data']['arrivals'])
        df_departures = pd.DataFrame(data['data']['departure'])
        
        # Format date columns in 12-hour format
        for df in [df_arrivals, df_departures]:
            df['STASTD_DATE'] = pd.to_datetime(df['STASTD_DATE']).dt.strftime('%I:%M %p')
            df['ETAETD_date'] = pd.to_datetime(df['ETAETD_date']).dt.strftime('%I:%M %p')
        
        return df_arrivals, df_departures
    else:
        st.error("Failed to fetch flight details.")
        return None, None

# Function to filter and prioritize airlines
def filter_and_prioritize(df, priority_airlines, airline_filter):
    if airline_filter:
        df = df[df['Airline'].str.contains(airline_filter, case=False)]
    priority_df = df[df['Airline'].isin(priority_airlines)]
    other_df = df[~df['Airline'].isin(priority_airlines)]
    return pd.concat([priority_df, other_df])

# Load data
st.title("Airport Flight Details")

# Refresh button
if st.button("Refresh Data"):
    st.cache_data.clear()

df_arrivals, df_departures = fetch_flight_data()

# Priority airlines
priority_airlines = ["Jazeera", "Thai Airways", "Sichuan Airlines", "Bhutan Airlines"]

# If data is loaded successfully
if df_arrivals is not None and df_departures is not None:
    # Headline area for delayed, just landed, and cancelled flights
    st.subheader("Flight Status Updates")
    recent_landed_time = datetime.now() - timedelta(minutes=15)
    
    for df, label in [(df_arrivals, "Arrival"), (df_departures, "Departure")]:
        # Check for status conditions and create alerts
        alerts = []
        if 'FlightStatus' in df.columns:
            if 'ETAETD_date' in df.columns:
                df['ETAETD_date'] = pd.to_datetime(df['ETAETD_date'], errors='coerce')
                alerts_df = df[(df['FlightStatus'].isin(['DELAYED', 'CANCELLED'])) |
                               ((df['FlightStatus'] == 'LANDED') & (df['ETAETD_date'] >= recent_landed_time))]
            else:
                alerts_df = df[df['FlightStatus'].isin(['DELAYED', 'CANCELLED'])]
            
            if not alerts_df.empty:
                st.markdown(f"**{label} Alerts:**")
                for idx, row in alerts_df.iterrows():
                    st.write(f"{row['Airline']} - {row['Flight']} : {row['FlightStatus']}")

    # Search for airlines
    airline_filter = st.text_input("Search by Airline", "").strip()

    # Tabs for Arrivals, Departures, and Recent Updates
    tab1, tab2, tab3 = st.tabs(["Arrivals", "Departures", "Recent Update"])
    
    with tab1:
        st.header("Arrivals")
        prioritized_arrivals = filter_and_prioritize(df_arrivals, priority_airlines, airline_filter)
        
        # Sub-tabs for grouped priority airlines and complete data sorted
        subtab1, subtab2, subtab3 = st.tabs(["Priority Airlines", "All Arrivals (Sorted)", "Arrival Airline-wise"])
        
        # Show grouped priority airlines data in "Priority Airlines" sub-tab
        with subtab1:
            st.subheader("Priority Airlines Arrivals")
            for airline, flights in prioritized_arrivals[prioritized_arrivals['Airline'].isin(priority_airlines)].groupby('Airline'):
                st.subheader(f"Airline: {airline}")
                st.dataframe(flights.reset_index(drop=True))
        
        # Show complete sorted data in "All Arrivals (Sorted)" sub-tab
        with subtab2:
            st.subheader("All Arrivals (Sorted by Time)")
            sorted_arrivals = prioritized_arrivals.sort_values(by='STASTD_DATE').reset_index(drop=True)
            st.dataframe(sorted_arrivals)

        with subtab3:
            st.subheader("All Arrivals (Airline-wise)")
            airline_sorted_arrivals = prioritized_arrivals.sort_values(by='Airline').reset_index(drop=True)
            for airline, flights in airline_sorted_arrivals.groupby('Airline'):
                st.subheader(f"Airline: {airline}")
                st.dataframe(flights.reset_index(drop=True))
            

    with tab2:
        st.header("Departures")
        prioritized_departures = filter_and_prioritize(df_departures, priority_airlines, airline_filter)
        
        # Sub-tabs for grouped priority airlines and complete data sorted
        subtab1, subtab2, subtab3 = st.tabs(["Priority Airlines", "All Departures (Sorted)", "Departure Airline-wise"])
        
        # Show grouped priority airlines data in "Priority Airlines" sub-tab
        with subtab1:
            st.subheader("Priority Airlines Departures")
            for airline, flights in prioritized_departures[prioritized_departures['Airline'].isin(priority_airlines)].groupby('Airline'):
                st.subheader(f"Airline: {airline}")
                st.dataframe(flights.reset_index(drop=True))
        
        # Show complete sorted data in "All Departures (Sorted)" sub-tab
        with subtab2:
            st.subheader("All Departures (Sorted by Time)")
            sorted_departures = prioritized_departures.sort_values(by='STASTD_DATE').reset_index(drop=True)
            st.dataframe(sorted_departures)

        with subtab3:
            st.subheader("All Departures Airline wise")
            airline_sorted_departures = prioritized_departures.sort_values(by='Airline').reset_index(drop=True)
            for airline, flights in airline_sorted_departures.groupby('Airline'):
                st.subheader(f"Airline: {airline}")
                st.dataframe(flights.reset_index(drop=True))
    
    with tab3:
        st.header("Recent Update - Last Hour Landings")
        recent_time = datetime.now() - timedelta(hours=1)
        recent_departures = df_departures[
            (df_departures['FlightStatus'] == 'Landed') & 
            (pd.to_datetime(df_departures['ETAETD_date'], errors='coerce') >= recent_time)
        ]
        if not recent_departures.empty:
            st.dataframe(recent_departures.reset_index(drop=True))
        else:
            st.write("No recent landings in the last hour.")
