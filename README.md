# MCP Server – Smart Listing Search

An MCP (Model Context Protocol) server that exposes MLS real estate listing search as tools for LLM clients like Claude. The client LLM handles natural language → structured query conversion; this server is a thin, well-documented API wrapper around the MLS backend.

## Architecture

```
User (natural language)
  → MCP Client (LLM, e.g. Claude)
  → converts to structured params
  → MCP Server Tools (this project)
  → MLS API
  → listing results back to user
```

## Tools Exposed

### `search_listings`
Search MLS listings with structured criteria. All parameters are optional — the client LLM picks what's relevant from the user's request.

| Parameter | Type | Description |
|---|---|---|
| `status` | list[int] | Status codes (e.g. `[1]` for Active, `[5]` for Closed) |
| `property_type` | list[int] | Property type codes (e.g. `[0]` for Residential) |
| `property_sub_type` | list[int] | Sub-type codes |
| `city` | string | City name |
| `zip_code` | string | ZIP code |
| `state` | string | State abbreviation |
| `area` | list[int] | Area codes |
| `min_price` / `max_price` | int | Price range |
| `min_beds` / `max_beds` | int | Bedroom range |
| `min_baths` / `max_baths` | int | Bathroom range |
| `min_sqft` / `max_sqft` | int | Square footage range |

### `get_field_codes`
Returns the code-to-label mappings for Status, PropertyType, PropertySubType, and Area. Useful when the client LLM needs to look up which codes to use.

## Project Structure

```
mcp_server_smart_listing_search/
├── server.py          # FastMCP server — exposes the two tools
├── mls_client.py      # MLSClient — handles auth, payload building, API calls
├── field_codes.py     # Code-to-label mappings (Status, PropertyType, Area, etc.)
├── requirements.txt   # Python dependencies
├── .env.example       # Template for required environment variables
└── plan.md            # Implementation plan and design decisions
```

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd mcp_server_smart_listing_search
python -m venv myenv
source myenv/bin/activate   # Windows: myenv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` and fill in your MLS credentials:

```
MLS_USERNAME=your_username_here
MLS_PASSWORD=your_password_here
```

### 4. Run the server

```bash
python server.py
```

## Usage Example

User says: *"Find me active 3+ bedroom homes in Beverly Hills under $2 million"*

The client LLM (Claude) translates this and calls:

```json
search_listings(
  status=[1],
  property_type=[0],
  city="Beverly Hills",
  min_beds=3,
  max_price=2000000
)
```

The server builds and POSTs the MLS query payload, then returns the listing results to the client LLM, which summarizes them for the user.

## Design Decisions

- **Flat tool parameters** — Easy for the client LLM to map natural language to individual fields rather than constructing a raw criteria array.
- **Session caching** — Logs in once and reuses the session; re-authenticates automatically on auth errors.
- **Rich docstrings** — Tool descriptions include all code mappings so the LLM can self-serve without calling `get_field_codes` every time.
- **Env vars for credentials** — `MLS_USERNAME` and `MLS_PASSWORD` are read from the environment, never hardcoded.

## Dependencies

- `mcp[cli]` (FastMCP)
- `requests`
- `python-dotenv`
