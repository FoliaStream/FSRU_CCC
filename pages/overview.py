import streamlit as st
import pandas as pd

import os 
import yaml

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
        vessel_image = f"{os.getcwd()}/db/input/fleet_img/{vessel_imo}.jpg"
        
        # Display image
        if os.path.exists(vessel_image):
            st.image(vessel_image, use_container_width=True)
        else:
            st.warning("Image not found")

        st.write(f"**IMO:** {vessel_imo}")
        st.write(f"**Name:** {vessel_name}")
    else:
        st.info("Click on a marker to see vessel details")


# Filters
    # age
    # hub distance
    # fleet
    # continent
    # capacity