import streamlit as st
from nepse import Nepse
import pandas as pd

def main():
    # Initialize the Nepse client
    nepse = Nepse()
    nepse.setTLSVerification(False)  # Temporary measure; handle SSL verification appropriately in production

    # Define a function to fetch and display the company list
    def display_company_list():
        st.header("Company List")
        company_list = nepse.getCompanyList()
        df = pd.DataFrame(company_list)
        st.dataframe(df)

    # Define a function to fetch and display the market summary
    def display_market_summary():
        st.markdown("### Market Summary")
        nepse = Nepse()
        nepse.setTLSVerification(False)

        # Fetch the market summary
        summary = nepse.getSummary()
        summary_dict = {item['detail']: item['value'] for item in summary}

        # Display the market summary using columns
        col1, col2 = st.columns(2)

        # First column items
        with col1:
            st.markdown("**TOTAL TURNOVER RS:**")
            st.write(f"{summary_dict.get('Total Turnover Rs:', 'N/A'):,}")
            
            st.markdown("**TOTAL TRANSACTIONS:**")
            st.write(f"{summary_dict.get('Total Transactions', 'N/A'):,}")
            
            st.markdown("**TOTAL MARKET CAPITALIZATION RS:**")
            st.write(f"{summary_dict.get('Total Market Capitalization Rs:', 'N/A'):,}")

        # Second column items
        with col2:
            st.markdown("**TOTAL TRADED SHARES:**")
            st.write(f"{summary_dict.get('Total Traded Shares', 'N/A'):,}")
            
            st.markdown("**TOTAL SCRIPS TRADED:**")
            st.write(f"{summary_dict.get('Total Scrips Traded', 'N/A'):,}")
            
            st.markdown("**TOTAL FLOAT MARKET CAPITALIZATION RS:**")
            st.write(f"{summary_dict.get('Total Float Market Capitalization Rs:', 'N/A'):,}")
            
        # Define a function to fetch and display the NEPSE index
    def display_nepse_index():
        st.markdown("### NEPSE Index 📈")
        nepse = Nepse()
        nepse.setTLSVerification(False)

        # Fetch the NEPSE index data
        nepse_index_data = nepse.getNepseIndex()
        df = pd.DataFrame(nepse_index_data)


        # Extract the NEPSE Index row and display it at the top
        nepse_index_row = df[df['index'] == 'NEPSE Index']
        if not nepse_index_row.empty:
            st.markdown("#### NEPSE Index Overview")
            st.metric(
                label="NEPSE Index",
                value=f"{nepse_index_row['currentValue'].values[0]:,.2f}",
                delta=f"{nepse_index_row['change'].values[0]:,.2f} ({nepse_index_row['perChange'].values[0]:,.2f}%)"
                # Removed delta_color to use the default behavior
            )

        # Display the complete table below the highlighted NEPSE Index
        st.markdown("### Detailed NEPSE Indices")
        # Rename columns based on the provided image's data structure
        df_display = df[['index', 'currentValue', 'change', 'perChange']].rename(
            columns={
                'index': 'Symbol',
                'currentValue': 'Current',
                'change': 'Chng',
                'perChange': 'Chng %'
            }
        )

        # Style function for highlighting positive in green and negative in red
        def highlight_change(val):
            """Highlight positive values in green and negative values in red."""
            if isinstance(val, (int, float)):
                if val > 0:
                    return 'color: green'
                elif val < 0:
                    return 'color: red'
            return ''

        # Apply styling to the DataFrame
        st.markdown(
            df_display.style
            .applymap(highlight_change, subset=['Chng', 'Chng %'])
            .format({'Current': '{:,.2f}', 'Chng': '{:,.2f}', 'Chng %': '{:,.2f}'})
            .set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'center'), ('background-color', '#e6f2ff')]},
                {'selector': 'td', 'props': [('text-align', 'center')]}
            ])
            .hide_index()
            .to_html(),
            unsafe_allow_html=True
        )

    # Function to style the gainers and losers
    def style_dataframe(df):
        def highlight_positive(val):
            """Highlight positive values in green and negative values in red."""
            if isinstance(val, (int, float)):
                if val > 0:
                    return 'color: green'
                elif val < 0:
                    return 'color: red'
            return ''

        return (df.style
                .applymap(highlight_positive, subset=['Pt. Change', '% Change'])
                .format({'LTP': '{:,.2f}', 'Pt. Change': '{:,.2f}', '% Change': '{:,.2f}'})
                .set_table_styles([
                    {'selector': 'th', 'props': [('text-align', 'center'), ('background-color', '#e6f2ff')]},
                    {'selector': 'td', 'props': [('text-align', 'center')]}
                ])
                .hide_index()
                .to_html())

    # Define a function to fetch and display the top gainers and top losers
    def display_top_gainers_and_losers():
        st.markdown("### Top Gainers and Losers")

        # Create tabs for Top Gainers and Top Losers
        tab1, tab2 = st.tabs(["Top Gainers", "Top Losers"])

        # Top Gainers tab
        with tab1:
            top_gainers = nepse.getTopGainers()
            df_gainers = pd.DataFrame(top_gainers)[['symbol', 'ltp', 'pointChange', 'percentageChange']].rename(
                columns={
                    'symbol': 'Symbol',
                    'ltp': 'LTP',
                    'pointChange': 'Pt. Change',
                    'percentageChange': '% Change'
                }
            )
            st.markdown(style_dataframe(df_gainers), unsafe_allow_html=True)

        # Top Losers tab
        with tab2:
            top_losers = nepse.getTopLosers()
            df_losers = pd.DataFrame(top_losers)[['symbol', 'ltp', 'pointChange', 'percentageChange']].rename(
                columns={
                    'symbol': 'Symbol',
                    'ltp': 'LTP',
                    'pointChange': 'Pt. Change',
                    'percentageChange': '% Change'
                }
            )
        st.markdown(style_dataframe(df_losers), unsafe_allow_html=True)

    # Define a function to fetch and display live market data
    def display_live_market():
        st.header("Live Market Data")
        
        # Fetch live market data
        live_market = nepse.getLiveMarket()
        df = pd.DataFrame(live_market)

        # Remove unwanted columns
        columns_to_remove = ['securityId', 'indexId', 'lastUpdatedDateTime']
        df = df.drop(columns=columns_to_remove, errors='ignore')

        # Rearrange columns as specified
        desired_order = [
            'symbol', 'lastTradedPrice', 'percentageChange', 'lastTradedVolume',
            'totalTradeQuantity', 'totalTradeValue', 'openPrice', 'highPrice',
            'lowPrice', 'averageTradePrice', 'previousClose', 'securityName'
        ]
        # Select only the columns that exist in the DataFrame to avoid KeyErrors
        existing_columns = [col for col in desired_order if col in df.columns]
        df = df[existing_columns]

        # Highlight rows where percentageChange is positive
        def highlight_positive_change(row):
            if row['percentageChange'] > 0:
                return ['color: green'] * len(row)
            else:
                return ['color: black'] * len(row)

        # Apply styling to the DataFrame
        st.dataframe(
            df.style.apply(highlight_positive_change, axis=1)
            .format({
                'openPrice': '{:,.2f}',
                'highPrice': '{:,.2f}',
                'lowPrice': '{:,.2f}',
                'totalTradeValue': '{:,.2f}',
                'lastTradedPrice': '{:,.2f}',
                'previousClose': '{:,.2f}',
                'averageTradePrice': '{:,.2f}',
                'ltp': '{:,.2f}',
                'change': '{:,.2f}',
                'percentageChange': '{:,.2f}',
                'volume': '{:,}',
                'totalTrades': '{:,}'
            })
            .set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'center'), ('background-color', '#e6f2ff')]},
                {'selector': 'td', 'props': [('text-align', 'center')]}
            ])
        )
    # Define a function to fetch and display the daily NEPSE index graph
    def display_daily_nepse_index_graph():
        st.header("Daily NEPSE Index Graph")
        graph_data = nepse.getDailyNepseIndexGraph()
        df = pd.DataFrame(graph_data)
        st.line_chart(df.set_index('date')['index'])

    # Define a function to fetch and display the daily scrip price graph
    def display_daily_scrip_price_graph():
        st.header("Daily Scrip Price Graph")
        symbol = st.text_input("Enter Scrip Symbol:")
        if symbol:
            graph_data = nepse.getDailyScripPriceGraph(symbol)
            df = pd.DataFrame(graph_data)
            st.line_chart(df.set_index('date')['close'])

    # Streamlit sidebar for navigation
    st.sidebar.title("NEPSE Data Dashboard")
    options = {
        "NEPSE Index": display_nepse_index,
        "Live Market Data": display_live_market,
        "Top Gainers and Losers": display_top_gainers_and_losers,
        "Market Summary": display_market_summary,
        "Company List": display_company_list,
        "Daily NEPSE Index Graph": display_daily_nepse_index_graph,
        "Daily Scrip Price Graph": display_daily_scrip_price_graph,
    }

    selection = st.sidebar.radio("Select a view:", list(options.keys()))
    options[selection]()

if __name__ == "__main__":
    main()
