"""
MCP Server — Smart Listing Search

Exposes MLS listing search as MCP tools for LLM clients.
"""

import os
from dotenv import load_dotenv

# Load .env from the same directory as this file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from mcp.server.fastmcp import FastMCP

from mls_client import MLSClient
from field_codes import (
    STATUS_CODES,
    PROPERTY_TYPE_CODES,
    PROPERTY_SUB_TYPE_CODES,
    AREA_CODES,
)

mcp = FastMCP("Smart Listing Search")
client = MLSClient()


@mcp.tool()
def search_listings(
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
) -> dict:
    """Search MLS listings with structured criteria.

    All parameters are optional — provide only the ones relevant to the query.
    String values for status, property_type, property_sub_type, and area are
    fuzzy-matched against known codes, so approximate values work fine
    (e.g. "residential" matches "Residential", "Beverly Hill" matches "Beverly Hills").

    Args:
        status: Listing status labels (e.g. ["Active"], ["Closed"]).
            Known values: {status_keys}
        property_type: Property type labels (e.g. ["Residential"]).
            Known values: {property_type_keys}
        property_sub_type: Sub-type labels (e.g. ["Single Family Residence"]).
            Known values: {property_sub_type_keys}
        city: City name (passed directly, no code lookup needed).
        zip_code: ZIP code string.
        state: State name or abbreviation.
        area: Area labels.
            Known values: {area_keys}
        min_price: Minimum list price.
        max_price: Maximum list price.
        min_beds: Minimum bedrooms.
        max_beds: Maximum bedrooms.
        min_baths: Minimum bathrooms.
        max_baths: Maximum bathrooms.
        min_sqft: Minimum square footage.
        max_sqft: Maximum square footage.
    """.format(
        status_keys=list(STATUS_CODES.keys()) or "TBD — not yet configured",
        property_type_keys=list(PROPERTY_TYPE_CODES.keys()) or "TBD — not yet configured",
        property_sub_type_keys=list(PROPERTY_SUB_TYPE_CODES.keys()) or "TBD — not yet configured",
        area_keys=list(AREA_CODES.keys()) or "TBD — not yet configured",
    )
    return client.search(
        status=status,
        property_type=property_type,
        property_sub_type=property_sub_type,
        city=city,
        zip_code=zip_code,
        state=state,
        area=area,
        min_price=min_price,
        max_price=max_price,
        min_beds=min_beds,
        max_beds=max_beds,
        min_baths=min_baths,
        max_baths=max_baths,
        min_sqft=min_sqft,
        max_sqft=max_sqft,
    )


@mcp.tool()
def get_field_codes() -> dict:
    """Returns all known code mappings for MLS search fields.

    Use this to discover valid values for status, property_type,
    property_sub_type, and area parameters in search_listings.
    """
    return {
        "status": STATUS_CODES,
        "property_type": PROPERTY_TYPE_CODES,
        "property_sub_type": PROPERTY_SUB_TYPE_CODES,
        "area": AREA_CODES,
    }


@mcp.tool()
def get_area_codes(refresh: bool = False) -> dict:
    """Fetch all MLS area codes (AreaName → AreaID mapping).

    Area codes are loaded from the MLS API at server startup and cached
    in memory. Set refresh=True to re-fetch from the API.

    Returns:
        A dict mapping area names to their numeric IDs.
        e.g. {"Beverly Hills": 1, "Bel Air - Holmby Hills": 4, ...}
    """
    if refresh:
        return client.refresh_area_codes()
    return AREA_CODES



# if __name__ == "__main__":
#     mcp.run()
