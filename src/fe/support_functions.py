import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

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


###########################
# FSRU CCC Investment Model 
###########################

DEFAULT_ASSUMPTIONS = dict(
    start_year=2026,
    end_year=2050,
    carbon_price_escalation=0.03,           # EU ETS price annual growth
    lng_price_eur_per_tonne=550.0,          # LNG bunker proxy price
    base_fsru_opex_eur=5_000_000.0,         # fixed annual FSRU opex, non-fuel
    ccc_maint_pct=0.03,                     # CCC annual O&M, % of CAPEX
    discount_rate=0.08,                     # WACC for NPV / discounted payback
    lng_co2_factor_t_per_t=2.75,            # t CO2 / t LNG fuel
    lng_lhv_mj_per_tonne=48_000.0,          # LNG lower calorific value
    fuel_ghg_intensity_gco2eq_per_mj=77.0,  # well-to-wake default for fossil LNG
    fueleu_baseline_gco2eq_per_mj=91.16,
    fueleu_penalty_eur_per_t_vlsfo=2400.0,
    vlsfo_lhv_mj_per_tonne=41_000.0,
    credit_captured_co2=True,               # biggest open assumption
    include_imo_nzf=False,                  # off by default: not yet adopted
    imo_nzf_start_year=2028,
    imo_price_usd_per_t=100.0,              # draft base-tier price, illustrative
    usd_eur_fx=0.92,
    co2_disposal_cost=50.0,                 # CO2 disposal/storage cost per tonne
)

FUELEU_STEPS = [
    (2025, 2029, 0.02),
    (2030, 2034, 0.06),
    (2035, 2039, 0.145),
    (2040, 2044, 0.31),
    (2045, 2049, 0.62),
    (2050, 9999, 0.80),
]

def _fueleu_reduction(year: int) -> float:
    for y0, y1, red in FUELEU_STEPS:
        if y0 <= year <= y1:
            return red
    return 0.0 if year < 2025 else 0.80

def _imo_nzf_reduction(year: int, start_year: int) -> float:
    if year < start_year:
        return 0.0
    reduction = 0.04 + 0.02 * (year - start_year)
    years_to_2050 = max(2050 - start_year, 1)
    reduction = min(reduction, 1.0 * (year - start_year) / years_to_2050)
    return float(np.clip(reduction, 0.0, 1.0))

def _irr(cash_flows: list[float]) -> float | None:
    cash_flows = np.array(cash_flows, dtype=float)
    if not (cash_flows < 0).any() or not (cash_flows > 0).any():
        return None  # no sign change
    def npv_at(rate):
        t = np.arange(len(cash_flows))
        return np.sum(cash_flows / (1.0 + rate) ** t)
    lo = -0.99
    for hi in (10.0, 100.0, 1000.0, 10_000.0):
        f_lo, f_hi = npv_at(lo), npv_at(hi)
        if f_lo * f_hi <= 0:
            break
    else:
        return hi
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = npv_at(mid)
        if abs(f_mid) < 1e-6:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return mid

def fsru_ccc_investment_model(
    annual_co2_tonnes: float = 109_588.2353,
    is_eu: bool = True,
    ccc_capex_eur: float = 15_000_000.0,
    carbon_price_eur_per_t: float = 80.0,
    fuel_savings_pct: float = 0.22,
    capture_rate_pct: float = 1.0,
    installation_year: int = 2028,
    load_factor_pct: float = 1.0,
    co2_disposal_cost: float = 50.0,
    **overrides,
) -> dict:
    """
    FSRU Cryogenic Carbon Capture (CCC) — Regulatory Cost & TCO / Payback Model
    
    Compares a "base / as-is" FSRU scenario against a "CCC retrofit" scenario
    across EU ETS, FuelEU Maritime, and (optionally) the still-draft IMO
    Net-Zero Framework, from an installation year through 2050.
    
    Parameters:
    -----------
    annual_co2_tonnes : float
        Baseline annual CO2 emissions at 100% load (from data_fsru.csv 'Estimate CO2')
    is_eu : bool
        True if vessel is stationed in EU waters (100% ETS/FuelEU exposure)
    ccc_capex_eur : float
        One-off CAPEX for the CCC retrofit (EUR)
    carbon_price_eur_per_t : float
        EU ETS price (EUR/tCO2) in start_year
    fuel_savings_pct : float
        Opex reduction from waste-heat integration (0-1)
    capture_rate_pct : float
        CO2 capture efficiency of the CCC unit (0-1)
    installation_year : int
        Year the CCC unit comes online
    load_factor_pct : float
        % of year at full regasification load (0-1)
    co2_disposal_cost : float
        Cost to permanently store/dispose captured CO2 (EUR/tonne)
    **overrides : dict
        Any DEFAULT_ASSUMPTIONS key can be overridden
    
    Returns:
    --------
    dict:
        - projections: pd.DataFrame with year-by-year data
        - metrics: dict with NPV, IRR, Payback_Year, Payback_Year_Discounted, Total_Savings
        - assumptions: dict with the full assumption set used
    """
    
    a = {
        **DEFAULT_ASSUMPTIONS,
        "annual_co2_tonnes": annual_co2_tonnes,
        "is_eu": is_eu,
        "ccc_capex_eur": ccc_capex_eur,
        "carbon_price_eur_per_t": carbon_price_eur_per_t,
        "fuel_savings_pct": fuel_savings_pct,
        "capture_rate_pct": capture_rate_pct,
        "installation_year": installation_year,
        "load_factor_pct": load_factor_pct,
        "co2_disposal_cost": co2_disposal_cost,
        **overrides
    }
    
    years = np.arange(a["start_year"], a["end_year"] + 1)
    eu_scope = 1.0 if a["is_eu"] else 0.0

    ttw_factor = (a["lng_co2_factor_t_per_t"] * 1e6) / a["lng_lhv_mj_per_tonne"]  # gCO2/MJ
    baseline_co2 = a["annual_co2_tonnes"] * a["load_factor_pct"]
    baseline_fuel_t = baseline_co2 / a["lng_co2_factor_t_per_t"]

    rows = []
    for yr in years:
        carbon_price = a["carbon_price_eur_per_t"] * (1 + a["carbon_price_escalation"]) ** (yr - a["start_year"])
        target_ghg = a["fueleu_baseline_gco2eq_per_mj"] * (1 - _fueleu_reduction(yr))
        imo_price_eur = a["imo_price_usd_per_t"] * a["usd_eur_fx"]
        imo_reduction = _imo_nzf_reduction(yr, a["imo_nzf_start_year"]) if a["include_imo_nzf"] else 0.0

        # ---------------- BASE (as-is) ----------------
        base_fuel_t = baseline_fuel_t
        base_co2 = baseline_co2
        base_fuel_cost = base_fuel_t * a["lng_price_eur_per_tonne"]
        base_energy_mj = base_fuel_t * a["lng_lhv_mj_per_tonne"]

        base_ets = base_co2 * eu_scope * carbon_price

        base_ghgie_actual = a["fuel_ghg_intensity_gco2eq_per_mj"]
        base_fueleu = 0.0
        if base_ghgie_actual > target_ghg:
            deficit_g = (base_ghgie_actual - target_ghg) * base_energy_mj
            deficit_t_vlsfo = deficit_g / (base_ghgie_actual * a["vlsfo_lhv_mj_per_tonne"])
            base_fueleu = deficit_t_vlsfo * a["fueleu_penalty_eur_per_t_vlsfo"] * eu_scope

        base_imo = 0.0
        if a["include_imo_nzf"]:
            allowed_t = base_co2 * (1 - imo_reduction)
            base_imo = max(0.0, base_co2 - allowed_t) * imo_price_eur

        base_opex = a["base_fsru_opex_eur"] + base_fuel_cost
        base_tco = base_ets + base_fueleu + base_imo + base_opex

        # ---------------- CCC retrofit ----------------
        is_installed = yr >= a["installation_year"]
        cap_rate_yr = a["capture_rate_pct"] if is_installed else 0.0
        fuel_save_yr = a["fuel_savings_pct"] if is_installed else 0.0

        ccc_fuel_t = baseline_fuel_t * (1 - fuel_save_yr)
        ccc_co2_generated = ccc_fuel_t * a["lng_co2_factor_t_per_t"]
        ccc_co2_captured = ccc_co2_generated * cap_rate_yr
        if a["credit_captured_co2"]:
            ccc_co2_net = ccc_co2_generated - ccc_co2_captured
        else:
            ccc_co2_net = ccc_co2_generated

        ccc_fuel_cost = ccc_fuel_t * a["lng_price_eur_per_tonne"]
        ccc_energy_mj = ccc_fuel_t * a["lng_lhv_mj_per_tonne"]
        ccc_maint = a["ccc_capex_eur"] * a["ccc_maint_pct"] if is_installed else 0.0
        ccc_opex = a["base_fsru_opex_eur"] + ccc_fuel_cost + ccc_maint

        ccc_ets = ccc_co2_net * eu_scope * carbon_price

        ccc_ghgie_actual = a["fuel_ghg_intensity_gco2eq_per_mj"]
        if a["credit_captured_co2"]:
            ccc_ghgie_actual = ccc_ghgie_actual - cap_rate_yr * ttw_factor
        
        ccc_fueleu = 0.0
        if ccc_ghgie_actual > target_ghg:
            deficit_g = (ccc_ghgie_actual - target_ghg) * ccc_energy_mj
            deficit_t_vlsfo = deficit_g / (ccc_ghgie_actual * a["vlsfo_lhv_mj_per_tonne"])
            ccc_fueleu = deficit_t_vlsfo * a["fueleu_penalty_eur_per_t_vlsfo"] * eu_scope

        ccc_imo = 0.0
        if a["include_imo_nzf"]:
            allowed_t = ccc_co2_generated * (1 - imo_reduction)
            ccc_imo = max(0.0, ccc_co2_net - allowed_t) * imo_price_eur

        # NEW: CO2 disposal cost
        ccc_disposal_cost = ccc_co2_captured * a["co2_disposal_cost"]

        ccc_capex_outflow = a["ccc_capex_eur"] if yr == a["installation_year"] else 0.0
        ccc_tco = ccc_ets + ccc_fueleu + ccc_imo + ccc_opex + ccc_disposal_cost
        annual_savings = base_tco - ccc_tco

        rows.append(dict(
            Year=yr, 
            Carbon_Price=carbon_price, 
            FuelEU_Target=target_ghg,
            Base_CO2=base_co2, 
            Base_Fuel_Cost=base_fuel_cost, 
            Base_ETS_Fee=base_ets,
            Base_FuelEU_Penalty=base_fueleu, 
            Base_IMO_Levy=base_imo,
            Base_Opex=base_opex, 
            Base_TCO=base_tco,
            CCC_Installed=int(is_installed), 
            CCC_CO2_Generated=ccc_co2_generated,
            CCC_CO2_Captured=ccc_co2_captured, 
            CCC_CO2_Net=ccc_co2_net,
            CCC_Fuel_Cost=ccc_fuel_cost, 
            CCC_Maint=ccc_maint, 
            CCC_Opex=ccc_opex,
            CCC_ETS_Fee=ccc_ets, 
            CCC_FuelEU_Penalty=ccc_fueleu, 
            CCC_IMO_Levy=ccc_imo,
            CCC_Disposal_Cost=ccc_disposal_cost,
            CCC_CAPEX_Outflow=ccc_capex_outflow, 
            CCC_TCO=ccc_tco,
            Annual_Savings=annual_savings,
        ))

    df = pd.DataFrame(rows)

    # ---------------- Financial metrics ----------------
    cash_flows, disc_cash_flows = [], []
    cum, cum_disc = 0.0, 0.0
    payback_year, payback_year_discounted = None, None
    
    for _, row in df.iterrows():
        yr = row["Year"]
        cf = row["Annual_Savings"] - row["CCC_CAPEX_Outflow"]
        cash_flows.append(cf)
        disc_cf = cf / (1 + a["discount_rate"]) ** (yr - a["start_year"])
        disc_cash_flows.append(disc_cf)
        if yr >= a["installation_year"]:
            cum += cf
            cum_disc += disc_cf
            if cum >= 0 and payback_year is None:
                payback_year = int(yr)
            if cum_disc >= 0 and payback_year_discounted is None:
                payback_year_discounted = int(yr)

    df["Cash_Flow"] = cash_flows
    df["Cum_Cash_Flow"] = df["Cash_Flow"].where(df["Year"] < a["installation_year"], other=np.nan)
    df.loc[df["Year"] >= a["installation_year"], "Cum_Cash_Flow"] = df.loc[df["Year"] >= a["installation_year"], "Cash_Flow"].cumsum()

    npv = sum(
        cf / (1 + a["discount_rate"]) ** (yr - a["installation_year"])
        for cf, yr in zip(cash_flows, years) if yr >= a["installation_year"]
    )
    cf_post_install = [cf for cf, yr in zip(cash_flows, years) if yr >= a["installation_year"]]
    irr = _irr(cf_post_install)

    metrics = dict(
        NPV=npv,
        IRR=irr,
        Payback_Year=payback_year,
        Payback_Year_Discounted=payback_year_discounted,
        Total_Savings=df["Annual_Savings"].sum(),
    )

    return dict(projections=df, metrics=metrics, assumptions=a)