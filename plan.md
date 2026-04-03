# MCP Server – Smart Listing Search: Implementation Plan

## Architecture

```
User (natural language) → MCP Client (LLM) → converts to structured params → MCP Server Tool → MLS API → listings back
```

The MCP **client** (already an LLM like Claude) handles natural language → structured criteria conversion.
The MCP **server** is a thin, well-documented API wrapper — no LLM needed inside it.

---

## Files to Create

### 1. `server.py` — Main MCP Server

**FastMCP server** exposing two tools:

#### Tool 1: `search_listings`
- **Purpose:** Search MLS listings with structured criteria
- **Parameters (all optional, so the LLM picks what's relevant):**
  - `status` — list of status codes (e.g. `[5]` for Closed)
  - `property_type` — list of property type codes (e.g. `[0]` for Residential)
  - `property_sub_type` — list of sub-type codes
  - `city` — string
  - `zip_code` — string
  - `state` — string
  - `area` — list of area codes
  - `min_price` / `max_price` — integers
  - `min_beds` / `max_beds` — integers
  - `min_baths` / `max_baths` — integers
  - `min_sqft` / `max_sqft` — integers

- **What it does:**
  1. Builds the `criterias` array from the provided parameters
  2. Authenticates with MLS (session-based login)
  3. POSTs to `ListingSearchElastic`
  4. Returns the JSON response

- The tool's **docstring** will contain detailed descriptions of each parameter including the code mappings (e.g., "Status: 1=Active, 5=Closed..."), so the client LLM knows how to fill them.

#### Tool 2: `get_field_codes`
- **Purpose:** Returns the code-to-label mappings for Status, PropertyType, PropertySubType, and Area
- **No parameters**
- Helps the LLM client understand what codes to use if it's unsure

### 2. `mls_client.py` — MLS API Client Module
- `MLSClient` class that handles:
  - Login/session management (reuses session, re-authenticates if expired)
  - Building the criteria payload from structured params
  - Making the search API call
  - Error handling

### 3. `field_codes.py` — Code Mappings
- Dictionaries mapping numeric codes → descriptive labels for:
  - Status (e.g., `5 → "Closed"`)
  - PropertyType (e.g., `0 → "Residential"`)
  - PropertySubType
  - Area
- *We'll populate with known values; you can expand later*

### 4. `requirements.txt`
- `mcp[cli]` (FastMCP)
- `requests`
- `python-dotenv` (optional, for local dev convenience)

### 5. `.env.example`
- Template showing required env vars:
  - `MLS_USERNAME`
  - `MLS_PASSWORD`

---

## Key Design Decisions

1. **Flat parameters on the tool** (not a raw criteria array) — This makes it easy for the client LLM to map "3 bedroom house in Beverly Hills under $2M" → `city="Beverly Hills", min_beds=3, max_price=2000000`

2. **Session caching** — Login once, reuse the session for subsequent calls. Re-login if a call fails with auth error.

3. **Rich docstrings** — The tool description will include all code mappings so the client LLM can self-serve without calling `get_field_codes` every time.

4. **Env vars for credentials** — Read `MLS_USERNAME` and `MLS_PASSWORD` from environment.

---

## Flow Example

User says: *"Find me active 3+ bedroom homes in Beverly Hills under $2 million"*

Client LLM calls tool:
```json
search_listings(
  status=[1],
  property_type=[0],
  city="Beverly Hills",
  min_beds=3,
  max_price=2000000
)
```

Server builds payload:
```json
{
  "searchType": "QCK",
  "criterias": [
    {"field": "Status", "value1": 1},
    {"field": "PropertyType", "value1": 0},
    {"field": "City", "value1": "Beverly Hills"},
    {"field": "Bed", "value1": "3"},
    {"field": "ListPrice", "value2": "2000000"}
  ]
}
```

Server returns listing results to client LLM, which summarizes them for the user.
