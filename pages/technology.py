import streamlit as st

import os 
import yaml

from src.fe.support_functions import setup_sidebar
from src.fe.styles import HIDE_SIDEBAR_NAV


################
# --- SET UP ---
################

# --- PAGE CONFIG --- 
st.set_page_config(page_title="TECHNOLOGY", layout="wide")

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
    st.title(selected_page)
elif selected_page == "OVERVIEW":
    st.switch_page("pages/overview.py")
elif selected_page == "SIMULATOR":
    st.switch_page("pages/simulator.py")


# --- PAGE ---
st.title("❄️ Cryogenic Carbon Capture Technology")

# Hero Section
st.markdown("""
<div style='background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
    <h3 style='color: #00d4ff; margin: 0;'>Pioneering Maritime Decarbonization</h3>
    <p style='color: #ffffff; font-size: 1.1rem; margin-top: 0.5rem;'>
        Leveraging LNG's cryogenic potential to capture 100% of CO₂ emissions while reducing fuel consumption by up to 22%
    </p>
</div>
""", unsafe_allow_html=True)

# Key Metrics
st.header("🎯 Proven Performance Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="CO₂ Capture Rate",
        value="100%",
        delta="From Boiler Exhaust"
    )

with col2:
    st.metric(
        label="Fuel Savings",
        value="22%",
        delta="Regasification Boilers"
    )

with col3:
    st.metric(
        label="Capture Temperature",
        value="-57°C",
        delta="Liquefaction Point"
    )

with col4:
    st.metric(
        label="Energy Utilization",
        value="17.4 MW",
        delta="Combined Systems"
    )

st.divider()

# Technology Overview
st.header("🔬 The Science Behind CCC")

st.markdown("""
Cryogenic Carbon Capture (CCC) is an advanced decarbonization technology that exploits the extreme cold energy of Liquefied Natural Gas (LNG) to capture CO₂ from exhaust gases. Unlike conventional chemical absorption methods, CCC relies on **physical temperature-driven transformations** to achieve:

- **Superior CO₂ purity** (>99%)
- **No chemical solvents** or toxic waste
- **Energy recovery** through cogeneration cycles
- **Scalable application** across maritime and industrial sectors

### How It Works

The process leverages LNG's cryogenic potential at **-162°C**, which contains approximately **830 kJ/kg** of usable cold energy. This energy is typically wasted during LNG regasification but can be captured and repurposed for CO₂ liquefaction.
""")

# Process Diagram
st.header("🔄 Two-Stage Capture Process")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Stage 1: Water Removal")
    st.markdown("""
    **Objective:** Remove moisture to prevent ice formation
    
    1. **Heat Recovery**  
       Flue gas (110-267°C) passes through a heat exchanger  
       → **11.4 MW** transferred to seawater
    
    2. **Condensation**  
       Water vapor condenses and is removed  
       → Dry gas mixture remains (CO₂, O₂, N₂)
    
    3. **Composition After Stage 1**  
       - CO₂: 5%  
       - H₂O: Removed  
       - O₂: 10%  
       - N₂: 75%
    """)

with col2:
    st.subheader("Stage 2: CO₂ Liquefaction")
    st.markdown("""
    **Objective:** Capture CO₂ in liquid form for storage
    
    1. **Pressurization**  
       Dry gas pressurized to **5.1 bar** (triple point)
    
    2. **Cryogenic Cooling**  
       LNG cold energy cools gas to **-57°C**  
       → CO₂ transitions to liquid phase  
       → Other gases (O₂, N₂) remain gaseous
    
    3. **Separation & Recovery**  
       Liquid CO₂ extracted for storage/use  
       → **5.9 MW** recovered energy for regasification
    """)

st.divider()

# Case Study
st.header("🚢 FSRU Case Study: Real-World Validation")

st.markdown("""
A comprehensive study published in the *Journal of Marine Science and Engineering* (2025) evaluated CCC integration on a Floating Storage Regasification Unit (FSRU) operating in Northern Europe. The research employed Thermoflow Thermoflex 32 software to simulate system performance under actual operational conditions.
""")

# Case Study Details
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Vessel Specifications**
    
    - **Type:** FSRU with 170,000 m³ storage
    - **Engine:** 3× Wärtsilä 8L50DF (7,800 kW each) + 1× 6L50DF (5,850 kW)
    - **Boilers:** 2× 65,000 kg/h regasification units
    - **Regasification:** Closed-loop operation (seawater <13°C)
    - **Send-out Capacity:** 3× 142,799 Nm³/hour @ 0°C
    """)

with col2:
    st.markdown("""
    **Key Findings**
    
    ✅ **100% CO₂ liquefaction** from boiler exhaust  
    ✅ **22% reduction** in boiler fuel consumption  
    ✅ **17.4 MW** total thermal energy utilized  
    ✅ **15.5°C** send-out temperature achieved with 78 MW  
    ✅ Simulation accuracy **within 1%** of actual performance  
    ✅ Technology Readiness Level: **TRL 7-8** (near-commercial)
    """)

# Energy Balance
st.subheader("⚡ Energy Balance Optimization")

st.markdown("""
The integrated CCC system redistributes energy flows to maximize efficiency:

| Component | Before CCC | After CCC | Energy Saved |
|-----------|------------|-----------|--------------|
| Steam Heater 1 | 27,353 kW | 10,931 kW | 16,422 kW |
| Steam Heater 2 | 27,353 kW | 24,898 kW | 2,455 kW |
| Steam Heater 3 | 27,353 kW | 24,898 kW | 2,455 kW |
| **Total Savings** | - | - | **21,332 kW** |

Additional energy recovery:
- Water separator: **11,411 kW**
- Flue gas cooler: **4,851 kW**
- CO₂ cooler: **1,103 kW**
""")

st.divider()

# Regulatory Context
st.header("📜 Regulatory Compliance & Market Drivers")

st.markdown("""
Cryogenic CO₂ capture directly addresses the maritime industry's most pressing regulatory requirements:
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **IMO 2023 GHG Strategy**
    - Net-zero emissions by **2050**
    - At least **40% CO₂ reduction by 2030**
    - **70% reduction by 2040** (compared to 2008)
    
    **Vessel Efficiency Indices**
    - **EEXI** (Energy Efficiency Existing Ship Index)
    - **EEDI** (Energy Efficiency Design Index)
    - **CII** (Carbon Intensity Indicator) - mandatory ratings
    - **SEEMP** (Ship Energy Efficiency Management Plan)
    """)

with col2:
    st.markdown("""
    **European Union Regulations**
    - **EU ETS** (Emissions Trading System)
      - Shipping included since **January 2024**
      - Carbon price: **~80-96 EUR/ton CO₂**
    - **FuelEU Maritime** (2021/562 framework)
      - Well-to-wake emission approach
      - Technology-neutral framework
      - Gradual reduction targets to 2050
    
    **Market Pressure**
    - 772 LNG vessels globally (2023)
    - 2,400+ dual-fuel vessels
    - FSRU fleet: 51 units + 341 on order
    """)

st.divider()

# Advantages & Challenges
col1, col2 = st.columns(2)

with col1:
    st.header("✅ Key Advantages")
    st.markdown("""
    - **100% CO₂ capture rate** (boiler exhaust)
    - **No chemical solvents** or toxic byproducts
    - **Leverages waste cold energy** from LNG regasification
    - **Reduces fuel consumption** by 22%
    - **Energy recovery** through cogeneration cycles
    - **Scalable** to various vessel types and sizes
    - **Aligned with regulatory frameworks** (IMO, EU ETS)
    - **Utilizes existing LNG infrastructure**
    - **TRL 7-8** (ready for commercial deployment)
    """)

with col2:
    st.header("⚠️ Current Challenges")
    st.markdown("""
    - **Energy intensity** of cryogenic cooling processes
    - **Moisture management** (ice formation prevention)
    - **High capital costs** for specialized equipment
    - **Space constraints** on existing vessels (retrofitting)
    - **CO₂ storage** requirements onboard
    - **Methane slip** from LNG combustion (ongoing engine improvements)
    - **Varying efficiency** with seawater temperature fluctuations
    - **Need for dynamic load optimization**
    """)

st.divider()

# Future Outlook
st.header("🚀 Future Development Pathways")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Technology Advancement**
    - Enhanced refrigeration systems
    - Next-generation heat exchangers
    - Hybrid capture systems
    - Integration with Organic Rankine Cycle (ORC)
    """)

with col2:
    st.markdown("""
    **Operational Optimization**
    - Dynamic load response algorithms
    - Real-time performance monitoring
    - Variable seawater temperature adaptation
    - Scalability across vessel designs
    """)

with col3:
    st.markdown("""
    **Industry Adoption**
    - Retrofit solutions for existing vessels
    - Newbuild integration designs
    - Standardization efforts
    - Cost reduction through economies of scale
    """)

st.markdown("""
### 🌍 Broader Implications

The successful implementation of CCC on FSRUs represents a significant step toward maritime decarbonization with **immediate applicability** and **proven results**:

- **Social Impact:** Reduces environmental footprint, improves public perception of LNG industry
- **Economic Benefits:** Fuel savings offset carbon costs (EU ETS at 80 EUR/ton)
- **Regulatory Alignment:** Provides compliance pathway through 2030 and beyond
- **Theoretical Contribution:** Advances research on cryogenic systems in maritime applications
- **Industry Catalyst:** Demonstrates feasibility for broader adoption across LNG value chain
""")

st.divider()

# References
st.header("📚 References")

st.markdown("""
**Primary Source:**
Malukas, A., & Lebedevas, S. (2025). Decarbonization and Improvement of Energy Efficiency of FSRU by Cryogenic CO₂ Capture. *Journal of Marine Science and Engineering, 13*(4), 770. https://doi.org/10.3390/jmse13040770

**Supporting References:**
- DNV (2024). Maritime Forecast to 2050. Energy Transition Outlook.
- Global CCS Institute (2024). Global Status of CCS Report.
- IMO (2023). 2023 IMO Strategy on Reduction of GHG Emissions from Ships.
- European Commission (2021). FuelEU Maritime Initiative (COM/2021/562).
- Park, J., Kim, Y., et al. (2024). Advancing greener LNG-fueled vessels. *Journal of Cleaner Production, 478*.
- Naveiro, M., et al. (2022). Novel closed loop regasification system integrating ORC and CO₂ capture. *Energy Conversion and Management, 257*.
""")

st.caption("""
**Note:** Performance data based on peer-reviewed research on FSRU vessels operating in closed-loop regasification mode at 100% load. 
Results may vary based on specific vessel configurations, operational conditions, and environmental factors.
""")