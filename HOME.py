import streamlit as st

import os 
import yaml

from src.fe.support_functions import setup_sidebar
from src.fe.styles import HIDE_SIDEBAR_NAV


################
# --- SET UP ---
################

# --- PAGE CONFIG --- 
st.set_page_config(page_title="HOME", layout="wide")

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
# Navigation on click
if selected_page == "HOME":
    pass
elif selected_page == "TECHNOLOGY":
    st.switch_page("pages/technology.py")
elif selected_page == "OVERVIEW":
    st.switch_page("pages/overview.py")
elif selected_page == "SIMULATOR":
    st.switch_page("pages/simulator.py")


# --- LOGO-TITLE ---
col1,col2,col3 = st.columns([1,2,1])
with col2:
    st.image(f"{os.getcwd()}/LOGO.png")

st.divider()

# --- DESCRIPTION ---
col1, col2 = st.columns([1,1])
with col1:
    st.header("Welcome to FSRU for Wärtsilä!")
    st.info("""
        This web page aims to present the potential benefits of implementing Cryogenic Carbon Capture on FSRU vessels.  \n
        
        Get started by exploring the pages!  
        """)