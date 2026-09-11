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

# --- ADVANCED COST ASSUMPTIONS (previously hardcoded) ---
with st.expander("Advanced Cost & Market Assumptions", expanded=False):
    st.caption(
        "Adjust these to stress-test the sensitivity of the results to fuel price volatility, inflation, and fuel source."
    )
    col1, col2 = st.columns(2)

    with col1:
        lng_price = st.number_input(
            "LNG Price (€/tonne)",
            min_value=100.0,
            max_value=2000.0,
            value=550.0,
            step=10.0,
            help="Bunker price assumption for LNG fuel in the start year."
        )
        lng_price_escalation = st.slider(
            "LNG Price Annual Escalation (%)",
            min_value=-10.0,
            max_value=15.0,
            value=0.0,
            step=0.5,
            help="Annual compounding growth (or decline) in LNG price. 0% keeps it flat, matching real fuel price volatility risk."
        ) / 100.0
        carbon_price_escalation = st.slider(
            "EU ETS Carbon Price Annual Escalation (%)",
            min_value=0.0,
            max_value=15.0,
            value=3.0,
            step=0.5,
            help="Annual compounding growth rate applied to the starting EU ETS carbon price."
        ) / 100.0

    with col2:
        lng_ghg_intensity = st.slider(
            "LNG Well-to-Wake GHG Intensity (gCO₂eq/MJ)",
            min_value=60.0,
            max_value=95.0,
            value=77.0,
            step=1.0,
            help="Lifecycle GHG intensity of the LNG fuel supply. Varies by supply source (e.g. pipeline vs. shipped, upstream methane leakage)."
        )

    st.info(
        "**Fixed FSRU opex is applied equally to both scenarios** so it "
        "cancels out of NPV, IRR, Payback, and Total Savings regardless of its value. "
        "**Strong assumption:** the model treats the retrofit as opex-neutral — extra crew, "
        "inspections, or insurance from the retrofit aren't captured. Held flat at €5M/year."
    )

# Fixed opex assumption — see note above. Not user-adjustable by design: it cancels out of
# every investment metric since it's applied identically to both scenarios. If you need to
# model a retrofit-specific opex increase, that requires a genuine modeling change (making
# opex asymmetric between scenarios), not just changing this constant.
base_opex = 5.0            # € Million/year, flat, identical in both scenarios
opex_escalation = 0.0      # kept at 0% for the same reason — see note above

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
    co2_disposal_cost=co2_disposal_cost,  # NEW
    lng_price_eur_per_tonne=lng_price,                    # NEW: was hardcoded 550.0
    lng_price_escalation=lng_price_escalation,            # NEW: was flat (0%)
    base_fsru_opex_eur=base_opex * 1_000_000.0,           # NEW: was hardcoded 5,000,000
    opex_escalation=opex_escalation,                      # NEW: was flat (0%)
    carbon_price_escalation=carbon_price_escalation,      # NEW: was hardcoded 3%
    fuel_ghg_intensity_gco2eq_per_mj=lng_ghg_intensity,   # NEW: was hardcoded 77.0
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
tab1, tab2, tab3 = st.tabs(["TCO Trend & Payback Path", "Detailed Projections Data",  "How This Calculation Works"])

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

    # Highlight payback years, if achieved
    if payback_simple is not None and payback_simple == payback_disc:
        fig.add_vline(
            x=payback_simple,
            line_width=2,
            line_dash="dot",
            line_color="#1565c0",
            annotation_text="Payback (Simple & Discounted)",
            annotation_position="bottom right"
        )
    else:
        if payback_simple is not None:
            fig.add_vline(
                x=payback_simple,
                line_width=2,
                line_dash="dot",
                line_color="#1565c0",
                annotation_text="Simple Payback",
                annotation_position="bottom left"
            )
        if payback_disc is not None:
            fig.add_vline(
                x=payback_disc,
                line_width=2,
                line_dash="dot",
                line_color="#6a1b9a",
                annotation_text="Discounted Payback",
                annotation_position="bottom right"
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

# with tab3:
#     st.markdown("### Physical & Regulatory Framework Rules")
    
#     st.markdown("""
#     #### 1. Emissions Physics
#     *   **Tank-to-Wake (Combustion) Limit:** Flue-gas carbon capture can only isolate emissions generated during actual fuel combustion. It does not touch upstream fuel production (well-to-tank) emissions or fuel handling methane slip.
#     *   **Baseline Fuel Consumption:** Modeled using the stoichiometric physical factor where burning **1 tonne of LNG fuel releases 2.75 tonnes of $CO_2$**.
#     *   **Fuel Savings Consistency:** Implementing a fuel savings rate (e.g., 22%) first lowers the fuel consumption, which proportionally reduces both the fuel cost and the generated $CO_2$ before applying the carbon capture factor.
    
#     #### 2. Regulatory Calculations
#     *   **EU ETS Fee:** Calculated at 100% of combustion emissions for the proportion of voyages operating in Europe.
#     *   **FuelEU Maritime Penalty:** Targets the greenhouse gas intensity of marine fuels (2020 baseline of $91.16\text{ gCO}_2\text{eq/MJ}$). The targets tighten dynamically over time. If a vessel fails compliance, the deficit in Megajoules is converted to VLSFO-equivalent tons and penalized at **€2,400 per VLSFO-equivalent ton**.
#     *   **IMO Net-Zero Levy (Optional):** Modeled based on the draft base-tier price of ~$100/tCO2e global levy starting in 2028.
#     *   **CO₂ Disposal Cost:** Cost to permanently store or dispose of captured CO₂ (transport, injection, monitoring). Configurable by the user.
#     """)

with tab3:
    st.markdown("### How This Calculation Works")
    st.caption(
        "A plain-language walkthrough of what the model does, start to finish — "
        "no formulas required to follow it."
    )

    st.markdown("""
Every year, running the FSRU **as-is** costs money in five buckets: **fuel**, **EU carbon
tax (ETS)**, **EU fuel-cleanliness penalty (FuelEU)**, **a possible future global carbon
levy (IMO)**, and **fixed operating costs**. The model adds those five up for every year
from 2026 to 2050 — that's the **Base** scenario.

Then it asks: *what if, in some year, you bolt a carbon-capture system onto the vessel?*
That changes some of those five buckets (less fuel burned, less taxable CO₂) but adds two
new costs (the machine's own upkeep, and disposing of the CO₂ you captured). That's the
**CCC** scenario.

The difference between the two, year by year, is your **savings**. Subtract the cost of
buying the machine, and you get a cash-flow story you can judge like any investment: does
it pay for itself, and how well?
    """)

    st.markdown("#### Step 1 — How much fuel and CO₂ are we even talking about?")
    st.markdown("""
You give the model one number: how many tonnes of CO₂ the vessel emits in a year at full
operation. Everything else is derived from that, using one physical fact from the
reference paper: **burning 1 tonne of LNG produces 2.75 tonnes of CO₂.**

> fuel burned = CO₂ emitted ÷ 2.75

If the vessel isn't running at full tilt all year, the **Load Factor** scales both numbers
down proportionally — 85% load means 85% of the fuel and 85% of the CO₂.
    """)

    st.markdown("#### Step 2 — What the Base (as-is) scenario pays for, each year")
    st.markdown("""
- **Fuel** — tonnes of LNG × price per tonne.
- **EU ETS (carbon tax)** — tonnes of CO₂ × the carbon price that year. The price starts
  at whatever you set and grows 3%/year, compounding. Only applies if the vessel is
  EU-based — non-EU vessels pay €0 here.
- **FuelEU penalty** — this isn't about *how much* CO₂ you emit, it's about how clean your
  fuel is *per unit of energy*. LNG's GHG intensity is assumed to be **77 gCO₂eq/MJ**. The
  EU's *target* intensity starts at 91.16 (2020 baseline) and ratchets down over time — by
  2%, then 6%, then 14.5%, then 31%, then 62%, then 80% by 2050. As long as 77 stays below
  the target, you pay nothing. Once the target drops below 77 (roughly around 2040), you're
  suddenly out of compliance and pay a penalty proportional to the gap. This is why the
  Base cost line doesn't rise smoothly — it's flat for years, then jumps once the target
  catches up.
- **IMO levy** (optional, off by default) — same shape as ETS but global, applying even to
  non-EU vessels, and only active if you turn it on, since the real-world policy isn't
  adopted yet.
- **Fixed opex** — a flat annual cost of just running the FSRU, unrelated to fuel or carbon.

Add all five up → that's the Base TCO for that year.
    """)

    st.markdown("#### Step 3 — What the CCC retrofit actually changes")
    st.markdown("""
Nothing happens until the **Install Year**. From then on, three things shift at once:

1. **Less fuel is burned** — the Fuel Savings % (22% from the paper's waste-heat
   integration) reduces fuel consumption directly. Less fuel burned also means less CO₂ is
   *generated* in the first place — the fuel-savings effect and the capture-rate effect
   are kept separate and multiplicative, not double-counted.
2. **A slice of what's still generated gets captured** — the Capture Rate % removes that
   fraction from the flue gas before it reaches the funnel.
3. **What's left after capture is what counts against your taxes** — *if* regulators
   credit captured CO₂ (the **Credit Captured CO2** toggle). This is the single biggest
   assumption in the whole model: if true, ETS and FuelEU costs can drop close to zero; if
   regulators never recognize stored CO₂ this way, you only benefit from the fuel savings,
   not the tax avoidance.

One physical nuance worth knowing: capture can only remove the CO₂ that comes from
*burning* the fuel. It can't touch the emissions baked into producing and shipping the
LNG in the first place. So even at 100% capture, the effective GHG intensity doesn't hit
zero — it drops from 77 to about 20 gCO₂eq/MJ. That's realistic, not a rounding error.

Two new costs also appear from the install year on:

- **CCC maintenance** — a flat 3%/year of whatever the machine cost.
- **CO₂ disposal/transport cost** — every tonne *physically* captured has to go somewhere,
  regardless of whether regulators credit it for tax purposes. This cost always applies
  once the system is capturing CO₂.

Add up (adjusted ETS + adjusted FuelEU + IMO if on + adjusted opex + maintenance +
disposal) → that's the CCC TCO for that year.
    """)

    st.markdown("#### Step 4 — Turning yearly savings into an investment answer")
    st.markdown("""
- **Annual savings** = Base TCO − CCC TCO, for each year.
- **Cash flow** = annual savings, except in the install year, where the full CAPEX is also
  subtracted in one lump — that's when you actually pay for the machine.
- **Cumulative cash flow** — a running total of cash flow from the install year onward.
  The first year it turns positive is the **Simple Payback Year**.
- **Discounted cash flow** — the same thing, but each future year's cash is shrunk by the
  WACC before adding it up, since €1 five years from now is worth less than €1 today. When
  *that* running total turns positive, that's the **Discounted Payback Year** — always the
  same year or later than the simple one.
- **NPV** — the sum of all discounted cash flows from install year to 2050. Positive means
  the investment is worth more than it costs, in today's money.
- **IRR** — the discount rate at which NPV would be exactly zero. Roughly: the higher the
  IRR, the better the return relative to the size of the investment. If the very first
  year's savings already nearly cover the whole CAPEX, IRR can shoot into the hundreds of
  percent — that's mathematically real but not a very useful number at that point; NPV and
  payback year are more reliable to read in that situation.
    """)

    st.info(
        "In short: physics converts CO₂ into fuel and energy numbers → regulations convert "
        "those into euros, year by year, for two parallel versions of the same vessel → the "
        "gap between them becomes a cash-flow story → standard finance turns that story into "
        "NPV, IRR, and a payback year."
    )

    st.markdown("#### A strong assumption worth knowing: fixed opex is retrofit-neutral")
    st.warning(
        "The model assumes the CCC retrofit changes fuel and carbon costs, but leaves "
        "**fixed FSRU opex** — crew, mooring, insurance, general upkeep — completely "
        "unaffected. That value is applied identically to both the Base and CCC scenarios, "
        "so it cancels out of every headline number (NPV, IRR, Payback Year, Total Savings) "
        "no matter what it's set to. It isn't adjustable in this tool for exactly that "
        "reason — a slider that can't move the answer would be misleading. In reality, a "
        "retrofit of this scale could plausibly require additional crew training, more "
        "frequent inspections, or higher insurance premiums beyond the CCC-specific "
        "maintenance the model already accounts for. If that's a real cost in practice, "
        "this model currently doesn't capture it, and the investment case would look "
        "somewhat weaker than shown here."
    )