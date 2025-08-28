import requests
import pandas as pd
import streamlit as st
import plotly.express as px

from plots import plot_price_volume_chart

st.title('Stock Analysis App')

# Sample data for autocomplete suggestions

st.header("Search a stock ticker from NIFTY 500 from NSE")

base_api_url = 'http://127.0.0.1:8000'
search_api_url = f'{base_api_url}/search'
fetch_api_url = f'{base_api_url}/fetch'
transcript_all_api_url = f'{base_api_url}/transcript/all'
transcript_api_url = f'{base_api_url}/transcript'
summary_api_url = f'{base_api_url}/summary'

search_query = st.text_input("Search:", value="", key="search_input")
search_api_query_url = f'{search_api_url}?query={search_query}'
resp = requests.get(search_api_query_url)
ticker_list = resp.json()

if search_query and ticker_list:
    selected_ticker = st.selectbox(
        "Ticker Suggestions:",
        options=ticker_list,
        index=0,  # Default to the first suggestion
        key="autocomplete_select_ticker",
    )
    if selected_ticker:
        st.write(f"**{selected_ticker}: Latest 5 days of stock price**")
        fetch_api_query_url = f'{fetch_api_url}?ticker={selected_ticker}'
        resp = requests.get(fetch_api_query_url)
        sdp_list = resp.json()
        sdp_df = pd.DataFrame(sdp_list)
        sdp_df = sdp_df[['ticker', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']]
        sdp_df['date'] = pd.to_datetime(sdp_df['date']).dt.date
        sdp_df = sdp_df.sort_values('date').reset_index(drop=True)
        st.write(sdp_df.tail().iloc[::-1].reset_index(drop=True))

        st.write(f"**{selected_ticker}: Price-Volume Daily Chart**")
        fig = plot_price_volume_chart(sdp_df)
        st.plotly_chart(fig)

        st.write(f"**{selected_ticker}: Transcripts summary available**")
        transcript_all_api_query_url = f'{transcript_all_api_url}?ticker={selected_ticker}'
        resp = requests.get(transcript_all_api_query_url)
        quarter_list = sorted(resp.json(), reverse=True)

        if len(quarter_list) > 0:
            selected_quarter = st.selectbox(
                "Available quarters:",
                options=quarter_list,
                index=0,  # Default to the first suggestion
                key="autocomplete_select_quarter",
            )

            if selected_quarter:
                transcript_api_query_url = f'{transcript_api_url}?ticker={selected_ticker}&quarter={selected_quarter}'
                resp = requests.get(transcript_api_query_url)
                st_list = resp.json()
                st_df = pd.DataFrame(st_list)

                st.download_button(
                    "Download transcript in csv",
                    st_df.to_csv(index=False).encode('utf-8'),
                    f"{selected_ticker}_{selected_quarter}_transcript.csv",
                    "text/csv",
                    key='download-transcript-csv'
                )

                if "summary_fetched" not in st.session_state:
                    st.session_state["summary_fetched"] = False
                
                if st.session_state["summary_fetched"] and ((st.session_state["ticker"] != selected_ticker) or (st.session_state["quarter"] != selected_quarter)):
                    st.session_state["summary_fetched"] = False

                if st.session_state['summary_fetched'] or st.button("Fetch Summary"):
                    summary_api_query_url = f'{summary_api_url}?ticker={selected_ticker}&quarter={selected_quarter}'
                    resp = requests.get(summary_api_query_url)
                    summary_dict = resp.json()
                    st.session_state["ticker"] = selected_ticker
                    st.session_state["quarter"] = selected_quarter
                    st.session_state["summary_fetched"] = True
                    
                    summary_key_list = [k for k in summary_dict.keys() if k not in ["ticker", "quarter"]]
                    selected_summary_key = st.selectbox(
                        "Choose summary metric:",
                        options=summary_key_list,
                        index=0,  # Default to the first suggestion
                        key="autocomplete_select_summary_metric",
                    )

                    if selected_summary_key:
                        st.write(summary_dict[selected_summary_key])
        else:
            st.write("No transcripts available.")
elif search_query and not ticker_list:
    st.write("No matching suggestions found.")
else:
    st.write("Start typing to see suggestions.")
