HIDE_SIDEBAR_NAV = """
<style>
    /* Hide the default multi-page navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Make the custom sidebar navigation more prominent */
    .sidebar .sidebar-content {
        padding-top: 2rem;
    }
</style>
"""

SIDEBAR_STYLES = {
    # "container": {"padding": "1!important", "background-color": "#005B9F"},  # Wärtsilä Blue
    "container": {"padding": "1!important", "background-color": "#fafafa"},
    "icon": {"color": "#FCA500", "font-size": "24px"},  # Wärtsilä Orange
    "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#E6F0FA", "color": "#005B9F"},
    "nav-link-selected": {"background-color": "#FCA500", "color": "#005B9F"}  # Orange selected state on blue
}