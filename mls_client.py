"""
MLS API client — handles authentication and listing search.
"""

import os
import requests

import field_codes
from field_codes import (
    STATUS_CODES,
    PROPERTY_TYPE_CODES,
    PROPERTY_SUB_TYPE_CODES,
    AREA_CODES,
    AREA_CODES_URL,
    CITY_LIST,
    fetch_area_codes,
)
from fuzzy_match import fuzzy_lookup_many, fuzzy_match_name


LOGIN_URL = "https://www.themls.com/CLAW.Security.AuthServer/Account/Login"
SEARCH_URL = "https://www.themls.com/MlsListingAPI/api/Search/ListingSearchElastic"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.themls.com",
    "Referer": "https://www.themls.com/",
}


class MLSClient:
    """Manages session-based auth and search calls to TheMLS API."""

    def __init__(self):
        self._session: requests.Session | None = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _login(self) -> requests.Session:
        username = os.environ.get("MLS_USERNAME", "")
        password = os.environ.get("MLS_PASSWORD", "")
        if not username or not password:
            raise RuntimeError("MLS_USERNAME and MLS_PASSWORD env vars must be set.")

        session = requests.Session()
        payload = {
            "account_key": "",
            "auth_legacy": True,
            "legacy": True,
            "trackUser": True,
            "accessUrl": "memberdashboard",
            "username": username,
            "password": password,
            "scheme": "",
        }
        resp = session.post(LOGIN_URL, json=payload)
        resp.raise_for_status()
        self._session = session
        return session

    def _get_session(self) -> requests.Session:
        if self._session is None:
            return self._login()
        return self._session

    # ------------------------------------------------------------------
    # Area codes
    # ------------------------------------------------------------------

    @staticmethod
    def fetch_areas() -> list[dict]:
        """
        Fetch the raw area list from the MLS API.
        Returns list of dicts: [{"AreaID": 1, "AreaName": "Beverly Hills", ...}, ...]
        """
        resp = requests.get(AREA_CODES_URL, timeout=15)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def refresh_area_codes() -> dict[str, int]:
        """
        Re-fetch area codes from the API and update the in-memory mapping.
        Returns the refreshed { AreaName: AreaID } dict.
        """
        refreshed = fetch_area_codes()
        field_codes.AREA_CODES.clear()
        field_codes.AREA_CODES.update(refreshed)
        return refreshed

    # ------------------------------------------------------------------
    # Criteria builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_criteria(
        status: list[str] | None = None,
        property_type: list[str] | None = None,
        property_sub_type: list[str] | None = None,
        city: str | None = None,
        zip_code: str | None = None,
        state: str | None = None,
        area: list[str] | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        min_beds: int | None = None,
        max_beds: int | None = None,
        min_baths: int | None = None,
        max_baths: int | None = None,
        min_sqft: int | None = None,
        max_sqft: int | None = None,
    ) -> list[dict]:
        criteria: list[dict] = []

        # --- Fields that need fuzzy code resolution ---
        if status:
            codes = fuzzy_lookup_many(status, STATUS_CODES)
            for c in codes:
                criteria.append({"field": "Status", "value1": c})

        if property_type:
            codes = fuzzy_lookup_many(property_type, PROPERTY_TYPE_CODES)
            for c in codes:
                criteria.append({"field": "PropertyType", "value1": c})

        if property_sub_type:
            codes = fuzzy_lookup_many(property_sub_type, PROPERTY_SUB_TYPE_CODES)
            for c in codes:
                criteria.append({"field": "PropertySubType", "value1": c})

        if area:
            codes = fuzzy_lookup_many(area, AREA_CODES)
            for c in codes:
                criteria.append({"field": "Area", "value1": c})

        # --- City — fuzzy matched against known city list ---
        if city:
            resolved_city = fuzzy_match_name(city, CITY_LIST)
            criteria.append({"field": "City", "value1": resolved_city})

        if zip_code:
            criteria.append({"field": "ZipCode", "value1": zip_code})

        if state:
            criteria.append({"field": "State", "value1": state})

        # --- Range fields ---
        if min_price is not None or max_price is not None:
            entry: dict = {"field": "ListPrice"}
            if min_price is not None:
                entry["value1"] = str(min_price)
            if max_price is not None:
                entry["value2"] = str(max_price)
            criteria.append(entry)

        if min_beds is not None or max_beds is not None:
            entry = {"field": "Bed"}
            if min_beds is not None:
                entry["value1"] = str(min_beds)
            if max_beds is not None:
                entry["value2"] = str(max_beds)
            criteria.append(entry)

        if min_baths is not None or max_baths is not None:
            entry = {"field": "Bath"}
            if min_baths is not None:
                entry["value1"] = str(min_baths)
            if max_baths is not None:
                entry["value2"] = str(max_baths)
            criteria.append(entry)

        if min_sqft is not None or max_sqft is not None:
            entry = {"field": "Sqft"}
            if min_sqft is not None:
                entry["value1"] = str(min_sqft)
            if max_sqft is not None:
                entry["value2"] = str(max_sqft)
            criteria.append(entry)

        return criteria

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, **kwargs) -> dict:
        """
        Build criteria from kwargs and call the MLS search API.
        Re-authenticates once if the first attempt fails with an auth error.
        """
        criteria = self._build_criteria(**kwargs)
        payload = {
            "searchType": "QCK",
            "criterias": criteria,
        }

        session = self._get_session()
        resp = session.post(SEARCH_URL, json=payload, headers=HEADERS)

        # If auth expired, re-login and retry once
        if resp.status_code in (401, 403):
            session = self._login()
            resp = session.post(SEARCH_URL, json=payload, headers=HEADERS)

        resp.raise_for_status()
        return resp.json()
