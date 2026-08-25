import streamlit as st
import plotly.graph_objects as go


import os 

from streamlit_option_menu import option_menu
from src.fe.styles import SIDEBAR_STYLES, COUNTRY_COLOR, COASTLINE_COLOR, BACKGROUND_COLOR, OCEAN_COLOR

# SIDEBAR
def setup_sidebar(pages,
                  main_page):
    with st.sidebar:
        col1, col2, col3 = st.columns([0.2, 2.4, 0.2])
        with col2:
            st.image(f"{os.getcwd()}/images/logo.jpg", use_container_width=True)
        
        # Initialize session state for page if it doesn't exist
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = main_page
        
        choose = option_menu("", 
                            pages,
                            default_index=pages.index(st.session_state.selected_page),
                            styles=SIDEBAR_STYLES)
        
        if choose != st.session_state.selected_page:
            st.session_state.selected_page = choose
            st.rerun()  
    
    return st.session_state.selected_page


# Globe figure
def build_world_figure(background_color=BACKGROUND_COLOR, 
                       ocean_color=OCEAN_COLOR, 
                       coastline_color=COASTLINE_COLOR, 
                       country_color=COUNTRY_COLOR, 
                       lats=None, 
                       lons=None, 
                       labels=None):
    
    fig = go.Figure()

    if lats and lons:
        fig.add_trace(go.Scattergeo(
            lon=lons,
            lat=lats,
            mode='markers',
            marker=dict(
                size=10,
                symbol='diamond',
                color='red',
                line=dict(width=1, color='white')
            ),
            text=labels if labels else [f"Lat: {lat}, Lon: {lon}" for lat, lon in zip(lats, lons)],
            hoverinfo='text',
            name='Vessels'
        ))
    else:    
        fig.add_trace(go.Scattergeo(
            lon=[0],
            lat=[0],
            mode='markers',
            marker=dict(size=0, opacity=0),
            hoverinfo='skip',
            showlegend=False
        ))

    fig.update_layout(
        geo=dict(
            showland=True,
            landcolor=background_color,
            showocean=True,
            oceancolor=ocean_color,
            showcountries=True,
            countrycolor=country_color,
            countrywidth=1.5,
            showcoastlines=True,
            coastlinecolor=coastline_color,
            projection=dict(
                type='orthographic',
                scale=0.9,
                rotation=dict(lon=50, lat=21, roll=0)
            ),
            showframe=False,
            lataxis=dict(showgrid=False),
            lonaxis=dict(showgrid=False),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        dragmode='pan',
        autosize=True
    )
    return fig