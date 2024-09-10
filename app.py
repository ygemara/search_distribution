import streamlit as st
import pandas as pd
import requests
from io import StringIO

def make_api_call(site, start_date, end_date, api_key, country, endpoint_type):
    base_url = "https://api.similarweb.com/v1/website"
    if endpoint_type == "Desktop":
        endpoint = "traffic-sources/search-visits-distribution"
    else:
        endpoint = "mobile-traffic-sources/search-visits-distribution"
    
    headers = {"x-sw-source":"streamlit_kw"}
    
    url = f"{base_url}/{site}/{endpoint}?api_key={api_key}&start_date={start_date}&end_date={end_date}&country={country}&main_domain_only=false&format=json"
    
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching data for {site} (country: {country}): {response.status_code}")
        st.text(f"Response content: {response.text}")
        return None

def process_data(data, site, country):
    if not data:
        return pd.DataFrame()
    
    df = pd.json_normalize(data["data"])
    df['site'] = site
    df['country'] = country
    df['date'] = pd.to_datetime(df['date'])
    df['date'] = df['date'].dt.strftime('%Y-%m')
    return df

st.title("SimilarWeb API Data Fetcher")

# Input for API key
api_key = st.text_input("Enter your SimilarWeb API Key")

# Endpoint selection
endpoint_type = st.radio("Select device type", ["Desktop", "Mobile", "Both"])

# Input for sites
input_type = st.radio("Input type", ["Single site", "List of sites", "File upload"])

if input_type == "Single site":
    sites = [st.text_input("Enter a website URL")]
elif input_type == "List of sites":
    sites = st.text_area("Enter websites (one per line)").split('\n')
else:
    uploaded_file = st.file_uploader("Choose a file with websites (one per line)", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, header=None)
        sites = df[0].tolist()
    else:
        sites = []

sites = [site.strip() for site in sites if site.strip()]

# Input for countries
countries = st.text_area("Enter country codes (one per line)", "us").split('\n')
countries = [country.strip() for country in countries if country.strip()]

# Other inputs
start_date = st.text_input("Start date (YYYY-MM)", "2023-01")
end_date = st.text_input("End date (YYYY-MM)", "2023-03")

if st.button("Fetch Data"):
    if not api_key or not sites or not endpoint_type or not countries:
        st.warning("Please fill in all required fields.")
    else:
        all_data = []
        
        with st.spinner("Fetching data... Please wait."):
            for site in sites:
                for country in countries:
                    endpoints_to_fetch = ["Desktop", "Mobile"] if endpoint_type == "Both" else [endpoint_type]
                    
                    for endpoint in endpoints_to_fetch:
                        data = make_api_call(site, start_date, end_date, api_key, country, endpoint)
                        
                        if data:
                            df = process_data(data, site, country)
                            df['device'] = endpoint
                            df = df[["site", "country", "device", "date", "total_search_visits", "visits_distribution.branded_visits", "visits_distribution.non_branded_visits"]]
                            df = df.rename(columns=lambda x: x.split(".")[-1])
                            all_data.append(df)
        
        st.success("Data fetching completed!")
        
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            st.write(final_df)
            
            csv = final_df.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name="similarweb_data.csv",
                mime="text/csv",
            )
        else:
            st.warning("No data was retrieved. Please check your inputs and try again.")
