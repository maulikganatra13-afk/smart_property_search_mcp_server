"""
Field code mappings for MLS Listing Search.

Each dictionary maps a human-readable label → numeric code.
Populate these with actual values from your MLS system.

AREA_CODES is fetched dynamically from the MLS API at startup.
CITY_LIST is loaded from test_data/city_list.json.
"""

import json
import os
import requests


# Status codes
STATUS_CODES: dict[str, int] = {
    "Active": 5,
    "Pending": 10,
    "Withdrawn": 15,
    "Sold/Leased": 20,
    "Expired": 25,
    "Active Under Contract": 30,
    "Canceled": 35,
    "Hold": 40,
    "Coming Soon": 55,
    "MLS Exclusive": 60,
}

# Property Type codes
PROPERTY_TYPE_CODES: dict[str, int] = {
    "Single Family": 0,
    "Condo/Co-Op": 1,
    "Income": 2,
    "Land": 3,
    "Lease": 4,
    "Sale": 5,
    "Lease Commercial": 6,
    "Business Opportunity": 10,
    "Mobile Home": 11,
    "Privacy": 12,
}

# Property Sub Type — TODO: Replace with actual mappings
PROPERTY_SUB_TYPE_CODES: dict[str, int] = {
}


# ------------------------------------------------------------------
# City list — loaded from test_data/city_list.json
# ------------------------------------------------------------------

_CITY_LIST_PATH = os.path.join(os.path.dirname(__file__), "test_data", "city_list.json")


def load_city_list() -> list[str]:
    """Load the list of valid city names from the JSON file."""
    try:
        with open(_CITY_LIST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[field_codes] WARNING: Could not load city list: {e}")
        return []


CITY_LIST: list[str] = load_city_list()


# ------------------------------------------------------------------
# Area codes — fetched live from MLS API
# ------------------------------------------------------------------

AREA_CODES_URL = (
    "https://www.themls.com/MLSListingSearchAPI/api/SearchDataField/"
    "GetAreaByMlsId/null/null/CLAW/Area"
)


def fetch_area_codes() -> dict[str, int]:
    """
    Fetch area-code mappings from the MLS API.
    Returns { "Beverly Hills": 1, "Bel Air - Holmby Hills": 4, ... }
    """
    try:
        resp = requests.get(AREA_CODES_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {item["AreaName"]: item["AreaID"] for item in data}
    except Exception as e:
        print(f"[field_codes] WARNING: Could not fetch area codes: {e}")
        return {}


# Load area codes once at import time
AREA_CODES: dict[str, int] = fetch_area_codes()
