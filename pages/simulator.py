import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import os 
import yaml

from src.fe.support_functions import setup_sidebar, fsru_ccc_investment_model
from src.fe.styles import HIDE_SIDEBAR_NAV



################
# --- SET UP ---
################

# --- PAGE CONFIG --- 
st.set_page_config(page_title="SIMULATOR", layout="wide")

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
    st.switch_page("pages/overview.py")
elif selected_page == "SIMULATOR":
    st.title(selected_page)



# --- PAGE ---

###################
# --- LOAD DATA ---
###################

data_fsru = pd.read_csv(f"{os.getcwd()}/db/input/csv/data_fsru.csv")


################
# --- FILTERS ---
################


# Clean data_fsru columns to be safe
data_fsru.columns = [c.strip() for c in data_fsru.columns]

# --- VESSEL FILTERS ---
st.subheader("1. Vessel Profile Selection")
with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fleet_options = ["All"] + sorted(data_fsru['FLEET'].unique().tolist())
        fleet_filter = st.selectbox("Fleet Operator", fleet_options)
    
    if fleet_filter != "All":
        filtered_vessels = data_fsru[data_fsru['FLEET'] == fleet_filter]
    else:
        filtered_vessels = data_fsru

    vessel_options = [f"{row['IMO']} - {row['NAME']}" for _, row in filtered_vessels.iterrows()]
    vessel_labels = [f"{row['NAME']} ({row['FLEET']})" for _, row in filtered_vessels.iterrows()]
    
    with col2:
        selected_vessel = st.selectbox(
            "Select Vessel", 
            vessel_options, 
            format_func=lambda x: vessel_labels[vessel_options.index(x)] if x in vessel_options else x
        )
        
    vessel_imo = int(selected_vessel.split(" - ")[0])
    vessel_data = data_fsru[data_fsru['IMO'] == vessel_imo].iloc[0]
    
    with col3:
        # Display key baseline metrics
        is_eu_vessel = str(vessel_data['EU']).strip().lower() in ['yes', 'true', '1']
        eu_badge = "Inside EU Scope (100% Tax)" if is_eu_vessel else "Non-EU Scope (0% Tax)"
        st.markdown(f"**Regulatory Scope:**\n### {eu_badge}")
        
    with col4:
        st.metric(
            label="Baseline CO2 (100% Load)", 
            value=f"{vessel_data['Estimate CO2']:,.1f} t/yr",
            help="Calculated using stoichiometric factors from vessel fuel specification."
        )

# Display a mini metadata card
with st.expander("View Selected FSRU Structural Parameters", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"**Capacity:** {vessel_data.get('Capacity (m³)', 'N/A')} m³")
    c2.write(f"**Country of Station:** {vessel_data.get('Country', 'N/A')}")
    c3.write(f"**Age:** {vessel_data.get('Age', 'N/A')} years")
    c4.write(f"**Area of Operation:** {vessel_data.get('Area', 'N/A')}")

# --- INPUT PARAMETERS ---
st.subheader("2. CCC Retrofit & Market Assumptions")
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Investment Parameters**")
        ccc_capex = st.number_input(
            "CCC CAPEX (€ Million)", 
            min_value=0.1, 
            max_value=200.0, 
            value=15.0, 
            step=0.5,
            help="One-off capital expenditure for retrofitting Cryogenic Carbon Capture on the FSRU."
        )
        install_year = st.slider(
            "Retrofit Installation Year", 
            min_value=2026, 
            max_value=2040, 
            value=2028,
            help="Year in which the CCC system comes online and begins operation."
        )
        wacc = st.slider(
            "WACC / Discount Rate (%)", 
            min_value=1.0, 
            max_value=20.0, 
            value=8.0, 
            step=0.5,
            help="Weighted Average Cost of Capital used for discounting future cash flows in NPV calculation."
        ) / 100.0

    with col2:
        st.markdown("**Operational Parameters**")
        load_factor = st.slider(
            "Annual Load Factor (%)", 
            min_value=0.0, 
            max_value=100.0, 
            value=100.0, 
            step=1.0,
            help="Percentage of the year the FSRU operates at full capacity, directly scaling CO2 generated."
        ) / 100.0
        
        fuel_savings = st.slider(
            "CCC Fuel Savings Rate (%)", 
            min_value=0, 
            max_value=50, 
            value=22, 
            step=1,
            help="Energy/fuel savings realized through integrating cryogenic cold energy recovery of the CCC."
        ) / 100.0
        
        capture_rate = st.slider(
            "CCC Carbon Capture Rate (%)", 
            min_value=50, 
            max_value=100, 
            value=100, 
            step=5,
            help="Efficiency of the flue-gas CO2 capture system (combustion emissions only)."
        ) / 100.0

    with col3:
        st.markdown("**Regulatory & Market Toggles**")
        carbon_price = st.slider(
            "EU ETS Starting Carbon Price (€/t)", 
            min_value=0, 
            max_value=300, 
            value=80, 
            step=5,
            help="Starting price of European Allowance (EUA) carbon tax in 2026."
        )
        
        # --- NEW: CO2 Disposal / Storage Cost ---
        co2_disposal_cost = st.slider(
            "CO₂ Disposal / Storage Cost (€/tonne)",
            min_value=0,
            max_value=200,
            value=50,
            step=5,
            help="""
            Cost to permanently store or dispose of captured CO₂.
            Includes transport, injection, and monitoring.
            
            Examples:
            - Northern Lights (Norway): ~€25-50/tonne
            - Porthos (Netherlands): ~€30-60/tonne
            - US onshore storage: ~€20-40/tonne
            """
        )
        
        # Advanced Regulatory Toggles
        credit_captured_co2 = st.toggle(
            "Credit Captured CO2 Against Taxes", 
            value=True,
            help="Toggle whether regulators accept captured CO2 as reportable emissions reductions for EU ETS & FuelEU Maritime."
        )
        
        include_imo_nzf = st.toggle(
            "Include IMO Net-Zero Levy (Draft)", 
            value=False,
            help="If enabled, applies the draft global maritime carbon levy starting in 2028 (~$100/tCO2e)."
        )

# --- RUN FINANCIAL MODEL ---
results = fsru_ccc_investment_model(
    annual_co2_tonnes=vessel_data['Estimate CO2'],
    is_eu=is_eu_vessel,
    ccc_capex_eur=ccc_capex * 1_000_000.0,
    carbon_price_eur_per_t=carbon_price,
    fuel_savings_pct=fuel_savings,
    capture_rate_pct=capture_rate,
    installation_year=install_year,
    load_factor_pct=load_factor,
    discount_rate=wacc,
    credit_captured_co2=credit_captured_co2,
    include_imo_nzf=include_imo_nzf,
    co2_disposal_cost=co2_disposal_cost  # NEW
)

df_proj = results['projections']
m = results['metrics']

# --- DISPLAY KEY FINANCIAL RESULTS ---
st.subheader("3. Investment Feasibility Metrics")

# Render premium KPI Blocks matching Excel Dashboard
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# Detect if payback is achieved in the very first year of installation (Instant Payback)
payback_simple = m['Payback_Year']
payback_disc = m['Payback_Year_Discounted']
is_instant_simple = (payback_simple is not None and payback_simple == install_year)
is_instant_disc = (payback_disc is not None and payback_disc == install_year)

with kpi1:
    npv_val = m['NPV']
    npv_color = "green" if npv_val >= 0 else "red"
    st.markdown(
        f"<div style='background-color: #f1f8e9; padding: 15px; border-radius: 10px; border-left: 5px solid #4caf50;'>"
        f"<span style='color: #2e7d32; font-weight: bold; font-size: 14px;'>NET PRESENT VALUE (NPV)</span><br>"
        f"<span style='font-size: 24px; font-weight: bold; color: {npv_color};'>€{npv_val:,.0f}</span><br>"
        f"<span style='font-size: 11px; color: #555555;'>Discounted at {wacc*100:.1f}% WACC</span>"
        f"</div>",
        unsafe_allow_html=True
    )

with kpi2:
    irr_val = m['IRR']
    if irr_val is not None:
        if irr_val > 10.0:  # If bisection hit bound or IRR is mathematically extreme (>1000%)
            irr_str = f">1,000%"
        else:
            irr_str = f"{irr_val*100:.1f}%"
    elif is_instant_simple:
        irr_str = "Instant Payback"
    else:
        irr_str = "N/A"
        
    st.markdown(
        f"<div style='background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #2196f3;'>"
        f"<span style='color: #1565c0; font-weight: bold; font-size: 14px;'>INTERNAL RATE OF RETURN (IRR)</span><br>"
        f"<span style='font-size: 24px; font-weight: bold; color: #1565c0;'>{irr_str}</span><br>"
        f"<span style='font-size: 11px; color: #555555;'>Projected over 2026–2050</span>"
        f"</div>",
        unsafe_allow_html=True
    )

with kpi3:
    if payback_simple is None:
        pb_str = "Never"
    else:
        pb_simple_str = f"Instant ({payback_simple})" if is_instant_simple else str(payback_simple)
        pb_disc_str = f"Instant ({payback_disc})" if is_instant_disc else (str(payback_disc) if payback_disc is not None else "Never")
        pb_str = f"{pb_simple_str} / {pb_disc_str}"
        
    st.markdown(
        f"<div style='background-color: #fff8e1; padding: 15px; border-radius: 10px; border-left: 5px solid #ffb300;'>"
        f"<span style='color: #ff8f00; font-weight: bold; font-size: 14px;'>PAYBACK YEAR (SIMPLE/DISC)</span><br>"
        f"<span style='font-size: 24px; font-weight: bold; color: #ff8f00;'>{pb_str}</span><br>"
        f"<span style='font-size: 11px; color: #555555;'>Retrofit online in {install_year}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

with kpi4:
    tot_savings = m['Total_Savings']
    st.markdown(
        f"<div style='background-color: #f3e5f5; padding: 15px; border-radius: 10px; border-left: 5px solid #9c27b0;'>"
        f"<span style='color: #6a1b9a; font-weight: bold; font-size: 14px;'>TOTAL TCO SAVINGS BY 2050</span><br>"
        f"<span style='font-size: 24px; font-weight: bold; color: #6a1b9a;'>€{tot_savings:,.0f}</span><br>"
        f"<span style='font-size: 11px; color: #555555;'>Cumulative nominal avoidance</span>"
        f"</div>",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# --- DETAILED ANALYSIS TABS ---
tab1, tab2, tab3 = st.tabs(["TCO Trend & Payback Path", "Detailed Projections Data", "Physics & Regulatory Rules"])

with tab1:
    st.markdown("### Total Cost of Ownership (TCO) Comparison")
    
    # Generate Interactive Plotly Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_proj['Year'], 
        y=df_proj['Base_TCO'] / 1_000_000.0, 
        mode='lines+markers',
        name='Base Scenario (As-Is)',
        line=dict(color='#d32f2f', width=3),
        marker=dict(size=6)
    ))
    fig.add_trace(go.Scatter(
        x=df_proj['Year'], 
        y=df_proj['CCC_TCO'] / 1_000_000.0, 
        mode='lines+markers',
        name='CCC Retrofit Scenario',
        line=dict(color='#388e3c', width=3),
        marker=dict(size=6)
    ))
    
    # Highlight install year
    fig.add_vline(
        x=install_year, 
        line_width=2, 
        line_dash="dash", 
        line_color="#ff9800",
        annotation_text="CCC System Retrofitted", 
        annotation_position="top left"
    )
    
    fig.update_layout(
        # title=f"Annual TCO Path: Carbon Capture System Retrofit Drastically Avoids Taxes",
        xaxis_title="Calendar Year",
        yaxis_title="Annual TCO Cost (€ Million)",
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255, 255, 255, 0.8)"),
        hovermode="x unified",
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Year-by-Year Cash Flow & Tax Projection")
    st.write("Below is the complete projection data supporting the metrics on this page. All values are presented in Euros.")
    
    # Format the projections table for displaying
    df_disp = df_proj.copy()
    format_cols = [
        'Carbon_Price', 'Base_Fuel_Cost', 'Base_ETS_Fee', 'Base_FuelEU_Penalty', 'Base_IMO_Levy', 'Base_Opex', 'Base_TCO',
        'CCC_CO2_Generated', 'CCC_CO2_Captured', 'CCC_CO2_Net', 'CCC_Fuel_Cost', 'CCC_Maint', 'CCC_Opex', 'CCC_ETS_Fee',
        'CCC_FuelEU_Penalty', 'CCC_IMO_Levy', 'CCC_Disposal_Cost', 'CCC_CAPEX_Outflow', 'CCC_TCO', 'Annual_Savings', 'Cash_Flow', 'Cum_Cash_Flow'
    ]
    for col in format_cols:
        if col in df_disp.columns:
            df_disp[col] = df_disp[col].map(lambda x: f"{x:,.0f}" if not pd.isna(x) else "")

    st.dataframe(df_disp, use_container_width=True, hide_index=True)
    
    # Provide download capability
    csv_data = df_proj.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Projections CSV",
        data=csv_data,
        file_name=f"ccc_projections_{vessel_data['NAME']}.csv",
        mime="text/csv"
    )

with tab3:
    st.markdown("### Physical & Regulatory Framework Rules")
    
    st.markdown("""
    #### 1. Emissions Physics
    *   **Tank-to-Wake (Combustion) Limit:** Flue-gas carbon capture can only isolate emissions generated during actual fuel combustion. It does not touch upstream fuel production (well-to-tank) emissions or fuel handling methane slip.
    *   **Baseline Fuel Consumption:** Modeled using the stoichiometric physical factor where burning **1 tonne of LNG fuel releases 2.75 tonnes of $CO_2$**.
    *   **Fuel Savings Consistency:** Implementing a fuel savings rate (e.g., 22%) first lowers the fuel consumption, which proportionally reduces both the fuel cost and the generated $CO_2$ before applying the carbon capture factor.
    
    #### 2. Regulatory Calculations
    *   **EU ETS Fee:** Calculated at 100% of combustion emissions for the proportion of voyages operating in Europe.
    *   **FuelEU Maritime Penalty:** Targets the greenhouse gas intensity of marine fuels (2020 baseline of $91.16\text{ gCO}_2\text{eq/MJ}$). The targets tighten dynamically over time. If a vessel fails compliance, the deficit in Megajoules is converted to VLSFO-equivalent tons and penalized at **€2,400 per VLSFO-equivalent ton**.
    *   **IMO Net-Zero Levy (Optional):** Modeled based on the draft base-tier price of ~$100/tCO2e global levy starting in 2028.
    *   **CO₂ Disposal Cost:** Cost to permanently store or dispose of captured CO₂ (transport, injection, monitoring). Configurable by the user.
    """)