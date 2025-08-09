"""
Store Configuration for Par Delta Individual Store Dashboards
"""

# Store mapping configuration
STORE_CONFIG = {
    "357993": {
        "name": "Enola",
        "address": "423 N Enola Rd",
        "subdomain": "357993",
        "full_url": "https://357993.streamlit.app"
    },
    "301290": {
        "name": "Paxton", 
        "address": "TBD",
        "subdomain": "301290",
        "full_url": "https://301290.streamlit.app"
    },
    "343939": {
        "name": "Mount Joy",
        "address": "807 E Main St", 
        "subdomain": "343939",
        "full_url": "https://343939.streamlit.app"
    },
    "358529": {
        "name": "Columbia",
        "address": "3929 Columbia Avenue",
        "subdomain": "358529", 
        "full_url": "https://358529.streamlit.app"
    },
    "359042": {
        "name": "Lititz",
        "address": "TBD",
        "subdomain": "359042",
        "full_url": "https://359042.streamlit.app"
    },
    "363271": {
        "name": "Marietta",
        "address": "TBD", 
        "subdomain": "363271",
        "full_url": "https://363271.streamlit.app"
    },
    "364322": {
        "name": "Elizabethtown",
        "address": "TBD",
        "subdomain": "364322",
        "full_url": "https://364322.streamlit.app"
    }
}

def get_store_config(pc_number):
    """Get configuration for a specific store"""
    return STORE_CONFIG.get(str(pc_number))

def get_all_stores():
    """Get all store configurations"""
    return STORE_CONFIG
