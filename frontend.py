import requests
import pandas as pd
import streamlit as st

st.title('Stock Analysis App')

# Sample data for autocomplete suggestions

st.title("Search a stock ticker from NIFTY 500 from NSE")

base_api_url = 'http://127.0.0.1:8000'
search_api_url = f'{base_api_url}/search'
fetch_api_url = f'{base_api_url}/fetch'
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
        key="autocomplete_select",
    )
    if selected_ticker:
        st.write(f"You selected: {selected_ticker}")

        fetch_api_query_url = f'{fetch_api_url}?ticker={selected_ticker}'
        resp = requests.get(fetch_api_query_url)
        sdp_list = resp.json()
        sdp_df = pd.DataFrame(sdp_list)
        sdp_df = sdp_df[['ticker', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']]
        sdp_df['date'] = pd.to_datetime(sdp_df['date']).dt.date
        st.write(sdp_df)
        st.line_chart(sdp_df.set_index('date')['close'])
        # st.plotly_chart(sdp_df.set_index('date')['close'])
elif search_query and not ticker_list:
    st.write("No matching suggestions found.")
else:
    st.write("Start typing to see suggestions.")

# DATE_COLUMN = 'date/time'
# DATA_URL = ('https://s3-us-west-2.amazonaws.com/'
#             'streamlit-demo-data/uber-raw-data-sep14.csv.gz')

# @st.cache_data
# def load_data(nrows):
#     data = pd.read_csv(DATA_URL, nrows=nrows)
#     lowercase = lambda x: str(x).lower()
#     data.rename(lowercase, axis='columns', inplace=True)
#     data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
#     return data

# data_load_state = st.text('Loading data...')
# data = load_data(10000)
# data_load_state.text("Done! (using st.cache_data)")

# if st.checkbox('Show raw data'):
#     st.subheader('Raw data')
#     st.write(data)

# st.subheader('Number of pickups by hour')
# hist_values = np.histogram(data[DATE_COLUMN].dt.hour, bins=24, range=(0,24))[0]
# st.bar_chart(hist_values)

# # Some number in the range 0-23
# hour_to_filter = st.slider('hour', 0, 23, 17)
# filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]

# st.subheader('Map of all pickups at %s:00' % hour_to_filter)
# st.map(filtered_data)
