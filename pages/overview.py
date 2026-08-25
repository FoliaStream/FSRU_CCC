import streamlit as st
import pandas as pd

import os 
import yaml

from datetime import datetime
from streamlit_plotly_events import plotly_events
from src.fe.support_functions import setup_sidebar, build_world_figure
from src.fe.styles import HIDE_SIDEBAR_NAV



################
# --- SET UP ---
################

# --- PAGE CONFIG --- 
st.set_page_config(page_title="OVERVIEW", layout="wide")

# --- STYLES ---
st.markdown(HIDE_SIDEBAR_NAV, unsafe_allow_html=True)

# --- CONFIG ---
with open(f"{os.getcwd()}/src/be/config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

# --- SIDEBAR & TITLE ---
selected_page = setup_sidebar(
    pages=config['pages'],
    main_page=config['main_page'])


# Navigation on click
if selected_page == "HOME":
    st.switch_page("HOME.py")
elif selected_page == "TECHNOLOGY":
    st.switch_page("pages/technology.py")
elif selected_page == "OVERVIEW":
    st.title(selected_page)
elif selected_page == "SIMULATOR":
    st.switch_page("pages/simulator.py")





# --- PAGE ---
data_fsru = pd.read_csv(f"{os.getcwd()}/db/input/csv/data_fsru.csv")
fsru_lats = list(data_fsru['Latitude'])
fsru_lons = list(data_fsru['Longitude'])
fsru_labs = [f"{x} - {y}" for x,y in zip(data_fsru['IMO'], data_fsru["NAME"])]
fsru_imgs = [f"{os.getcwd()}/db/images/{imo}.jpg" for imo in list(data_fsru['IMO'])]


col1, col2 = st.columns([2,1])

# Globe Column
with col1:
    globe = build_world_figure(lats=fsru_lats, lons=fsru_lons, labels=fsru_labs)
    selected_points = plotly_events(
            globe,
            click_event=True,
            select_event=False,
            hover_event=False,
            override_height=900,
            override_width="100%",
        )
    
# Image display column
with col2:
    st.subheader("Vessel Details")
    
    if selected_points:
        point_index = selected_points[0]['pointIndex']
        
        # Get vessel info using the index
        vessel_imo = data_fsru.iloc[point_index]['IMO']
        vessel_name = data_fsru.iloc[point_index]['NAME']
        vessel_capacity = data_fsru.iloc[point_index]['Capacity (m³)']
        vessel_age = data_fsru.iloc[point_index]['Age']
        vessel_country = data_fsru.iloc[point_index]['Country']
        vessel_area = data_fsru.iloc[point_index]['Area']
        vessel_emission = data_fsru.iloc[point_index]['Estimate CO2']
        vessel_image = f"{os.getcwd()}/db/input/fleet_img/{vessel_imo}.jpg"
        
        # Vessel name as header
        st.markdown(f"### {vessel_name}")
        
        # Use columns for better layout
        col1, col2 = st.columns(2)
        with col1:
            st.metric("IMO", vessel_imo)
            st.metric("Capacity (m³)", f"{vessel_capacity}")
            st.metric("Estimated CO2 (ton)", f"{int(vessel_emission)}")
        with col2:
            st.metric("Country", vessel_country)
            st.metric("Area", vessel_area)
            st.metric("Age", f"{vessel_age} years")
        
        # Display image
        if os.path.exists(vessel_image):
            st.image(vessel_image, use_container_width=True)
    else:
        st.info("Click on a marker to see vessel details")

st.divider()

# FILTERS
st.subheader("Filters")
col1, col2 = st.columns([1,2])

with col1:
    with st.container(border=True):
        # Store filter values in variables
        selected_fleet = st.selectbox('Fleet', options=["All"] + list(data_fsru['FLEET'].unique()))
        selected_country = st.selectbox('Country', options=["All"] + list(data_fsru['Country'].unique()))
        selected_area = st.selectbox('Area', options=["All"] + list(data_fsru['Area'].unique()))
        
        # Age slider
        min_age = int(data_fsru['Age'].min())
        max_age = int(data_fsru['Age'].max())
        age_range = st.select_slider(
            'Age', 
            options=range(min_age, max_age + 1), 
            value=(min_age, max_age)
        )
        
        # Capacity slider
        min_cap = int(data_fsru['Capacity (m³)'].min())
        max_cap = int(data_fsru['Capacity (m³)'].max())
        capacity_range = st.select_slider(
            'Capacity', 
            options=range(min_cap, max_cap + 1), 
            value=(min_cap, max_cap)
        )

with col2:
    # st.subheader("Fleet")
    
    # Apply filters
    filtered_data = data_fsru.copy()
    
    # Apply categorical filters
    if selected_fleet != "All":
        filtered_data = filtered_data[filtered_data['FLEET'] == selected_fleet]
    if selected_country != "All":
        filtered_data = filtered_data[filtered_data['Country'] == selected_country]
    if selected_area != "All":
        filtered_data = filtered_data[filtered_data['Area'] == selected_area]
    
    # Apply range filters
    filtered_data = filtered_data[
        (filtered_data['Age'] >= age_range[0]) & 
        (filtered_data['Age'] <= age_range[1]) &
        (filtered_data['Capacity (m³)'] >= capacity_range[0]) & 
        (filtered_data['Capacity (m³)'] <= capacity_range[1])
    ]
    
    # Show number of vessels
    st.metric("Vessels Found", len(filtered_data))
    
    # Display filtered dataframe
    if not filtered_data.empty:
        # Select columns to display
        display_columns = ['IMO', 'NAME', 'FLEET', 'Country', 'Area', 'Age', 'Capacity (m³)']
        st.dataframe(
            filtered_data[display_columns],
            use_container_width=True,
            height=375,
            column_config={
                "IMO": st.column_config.TextColumn("IMO"),
                "NAME": st.column_config.TextColumn("Vessel Name"),
                "FLEET": st.column_config.TextColumn("Fleet"),
                "Country": st.column_config.TextColumn("Country"),
                "Area": st.column_config.TextColumn("Area"),
                "Age": st.column_config.NumberColumn("Age (years)"),
                "Capacity (m³)": st.column_config.NumberColumn("Capacity (m³)", format="%d"),
            },
            hide_index=True
        )
    else:
        st.info("No vessels match the selected filters")