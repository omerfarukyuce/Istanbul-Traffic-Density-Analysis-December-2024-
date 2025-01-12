import pandas as pd
import streamlit as st
import pydeck as pdk
import altair as alt

# Load and process data
traffic = pd.read_csv("traffic_density_202412.csv")
traffic['DATE_TIME'] = pd.to_datetime(traffic['DATE_TIME'])

# Calculate average values by GEOHASH
average = traffic.groupby("GEOHASH").mean(numeric_only=True)
average.columns = ["LATITUDE", "LONGITUDE", "MINIMUM SPEED", "MAXIMUM SPEED", "AVERAGE SPEED", "NUMBER OF VEHICLES"]

# App Title and Description
st.title("Istanbul Traffic Density Analysis")
st.markdown("This application visualizes traffic data from Istanbul using interactive maps and detailed analytics.")

st.dataframe(average)

# Sidebar filters
st.sidebar.header("Filters")
selected_geohash = st.sidebar.selectbox("Choose a GEOHASH:", average.index)
start_date = st.sidebar.date_input("Start Date", traffic['DATE_TIME'].min().date())
end_date = st.sidebar.date_input("End Date", traffic['DATE_TIME'].max().date())

# Filter data by date
filtered_data = traffic[(traffic['DATE_TIME'].dt.date >= start_date) &
                        (traffic['DATE_TIME'].dt.date <= end_date)]

# Display selected GEOHASH data on a map
st.subheader(f"Data for Selected Region ({selected_geohash})")
selected_data = average.loc[[selected_geohash]]
st.map(selected_data)

# Detailed view of the selected GEOHASH
st.subheader("Details for Selected Region")
st.dataframe(selected_data)

# Interactive map showing all GEOHASH traffic density
st.subheader("Traffic Density Map")

def get_color(number_of_vehicles):
    if number_of_vehicles > 100:
        return [255, 0, 0, 160]  # Red
    elif 50 <= number_of_vehicles <= 100:
        return [255, 255, 0, 160]  # Yellow
    else:
        return [0, 255, 0, 160]  # Green

filtered_geo_data = filtered_data.groupby("GEOHASH").mean(numeric_only=True).reset_index()
filtered_geo_data.columns = ["GEOHASH", "LATITUDE", "LONGITUDE", "MINIMUM SPEED", "MAXIMUM SPEED", "AVERAGE SPEED", "NUMBER OF VEHICLES"]
filtered_geo_data['COLOR'] = filtered_geo_data['NUMBER OF VEHICLES'].apply(get_color)

st.pydeck_chart(pdk.Deck(
    initial_view_state=pdk.ViewState(
        latitude=filtered_geo_data["LATITUDE"].mean(),
        longitude=filtered_geo_data["LONGITUDE"].mean(),
        zoom=10,
        pitch=50,
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=filtered_geo_data,
            get_position='[LONGITUDE, LATITUDE]',
            get_color='COLOR',
            get_radius=200,
            pickable=True,
        )
    ],
))

# Filter data based on user selected GEOHASH
filtered_geohash_data = traffic[traffic['GEOHASH'] == selected_geohash]

# Notify user if no data is available for the selected GEOHASH
if filtered_geohash_data.empty:
    st.sidebar.warning(f"No data available for GEOHASH: {selected_geohash}")
else:
    # Summary statistics
    avg_vehicles = filtered_geohash_data['NUMBER_OF_VEHICLES'].mean()
    avg_speed = filtered_geohash_data['AVERAGE_SPEED'].mean()
    min_speed = filtered_geohash_data['MINIMUM_SPEED'].min()
    max_speed = filtered_geohash_data['MAXIMUM_SPEED'].max()

    # Summary statistics to show in sidebar
    st.sidebar.subheader(f"Summary Statistics for GEOHASH: {selected_geohash}")
    st.sidebar.write(f"Average Number of Vehicles: {avg_vehicles:.2f}")
    st.sidebar.write(f"Average Speed: {avg_speed:.2f} km/h")
    st.sidebar.write(f"Minimum Speed: {min_speed:.2f} km/h")
    st.sidebar.write(f"Maximum Speed: {max_speed:.2f} km/h")

# Time Series Chart
st.subheader(f"Traffic Trends for {selected_geohash}")
if not filtered_geohash_data.empty:
    time_series_chart = alt.Chart(filtered_geohash_data).mark_line().encode(
        x='DATE_TIME:T',
        y='NUMBER_OF_VEHICLES:Q',
        tooltip=['DATE_TIME:T', 'NUMBER_OF_VEHICLES:Q']
    ).properties(
        width=700,
        height=400
    )
    st.altair_chart(time_series_chart, use_container_width=True)
else:
    st.write("No time series data available for this GEOHASH.")

# Data Download Option
st.sidebar.download_button(
    label="Download Filtered Data",
    data=filtered_geo_data.to_csv(index=False),
    file_name='filtered_traffic_data.csv',
    mime='text/csv',
)
# Top Traffic Regions
st.sidebar.subheader("Top Traffic Regions")
top_regions = filtered_geo_data.sort_values(by='NUMBER OF VEHICLES', ascending=False).head(10)
st.sidebar.write(top_regions[['GEOHASH', 'NUMBER OF VEHICLES']])

# Min Traffic Regions (Excluding NUMBER OF VEHICLES == 1)
st.sidebar.subheader("Bot Traffic Regions(Values Expect 1)")
filtered_regions = filtered_geo_data[filtered_geo_data['NUMBER OF VEHICLES'] > 1]
top_regions = filtered_regions.sort_values(by='NUMBER OF VEHICLES', ascending=True).head(10)
st.sidebar.write(top_regions[['GEOHASH', 'NUMBER OF VEHICLES']])
