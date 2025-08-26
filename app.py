from typing import List  # Import type hints for better code documentation
from io import StringIO  # Import StringIO for in-memory file handling

import pandas as pd  # Import pandas for data manipulation and analysis
from dash import Dash, html, dcc, Input, Output, State, dash_table  # Import Dash components for web app
import dash_bootstrap_components as dbc  # Import Bootstrap components for styling

from trend_data import TrendData  # Import custom module for trend data handling
from trend_charts import TrendCharts  # Import custom module for creating charts
from utils import get_country_code  # Import utility function to get country codes

# App Setup 
external_stylesheets = [dbc.themes.MINTY]  # Use MINTY Bootstrap theme for styling
app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)  # Initialize Dash app
server = app.server  # Expose server for deployment (e.g., on Heroku)

# Services
data_service = TrendData()  # Create instance of TrendData service for data operations
charts = TrendCharts(template="plotly_white")  # Create chart service with white theme

# Define timeframe options for the dropdown
timeframe_options = [
    {"label": "Now 1 hour", "value": "now 1-H"},
    {"label": "Now 4 hours", "value": "now 4-H"},
    {"label": "Now 1 day", "value": "now 1-d"},
    {"label": "Today 1 month", "value": "today 1-m"},
    {"label": "Today 3 months", "value": "today 3-m"},
    {"label": "Today 12 months", "value": "today 12-m"},
    {"label": "Today 5 years", "value": "today 5-y"},
    {"label": "All time", "value": "all"},
]

def _parse_keywords(raw: str) -> List[str]:
    """Parse and clean comma-separated keywords input from user"""
    if not raw:  # If input is empty
        return []  # Return empty list
    # Split by comma and strip whitespace and quotes from each part
    parts = [p.strip().strip('"\''"”’") for p in raw.split(",")]
    seen = set()  # Track seen keywords to avoid duplicates
    cleaned = []  # Store cleaned keywords
    for p in parts:
        if p and p not in seen:  # If keyword is not empty and not a duplicate
            cleaned.append(p)  # Add to cleaned list
            seen.add(p)  # Add to seen set
    return cleaned[:5]  # Return up to 5 keywords (Pytrends API limit)

# Layout 
# Create navigation bar component
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(  # Logo and brand link
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="/assets/logo.png", height="36")),  # Logo image
                        dbc.Col(dbc.NavbarBrand("Google Trends Explorer", className="ms-2")),  # App title
                    ],
                    align="center",  # Center align items
                    className="g-0",  # No gutter between columns
                ),
                href="#",  # Link destination
                style={"textDecoration": "none"},  # Remove underline from link
            ),
            dbc.Nav(  # Navigation menu
                [
                    dbc.NavItem(dbc.NavLink("Home", href="#")),  # Home link
                    dbc.NavItem(dbc.NavLink("Docs", href="#")),  # Documentation link
                    dbc.NavItem(dbc.NavLink("Contact", href="#")),  # Contact link
                ],
                className="ms-auto",  # Align to right
                navbar=True,  # Style as navbar
            ),
        ]
    ),
    color="primary",  # Primary color
    dark=True,  # Use dark text
    sticky="top",  # Stick to top of page
)

# Create filter card with input controls
filters_card = dbc.Card(
    [
        dbc.CardHeader("Filters"),  # Card header
        dbc.CardBody(  # Card body with form elements
            [
                dbc.Label("Keywords (comma separated)"),  # Input label
                dcc.Input(  # Text input for keywords
                    id="keywords-input",
                    type="text",
                    placeholder="e.g. Python, Data Science",
                    style={"width": "100%"},  # Full width
                    debounce=True,  # Delay input processing
                ),
                dbc.Label("Timeframe", className="mt-3"),  # Label with top margin
                dcc.Dropdown(  # Dropdown for timeframe selection
                    id="timeframe-dropdown",
                    options=timeframe_options,  # Options defined above
                    value="today 1-m",  # Default value
                    clearable=False,  # Cannot clear selection
                ),
                dbc.Label("Country (code or name)", className="mt-3"),  # Country input label
                dcc.Input(  # Text input for country
                    id="country-input",
                    type="text",
                    placeholder="e.g. NG or Nigeria (leave empty for worldwide)",
                    style={"width": "100%"},  # Full width
                    debounce=True,  # Delay input processing
                ),
                html.Hr(className="my-4"),  # Horizontal divider
                html.H6("Regional Filters"),  # Subheading
                dbc.Label("Top N regions"),  # Slider label
                dcc.Slider(  # Slider for selecting number of regions
                    id="topn-slider",
                    min=5, max=50, step=1, value=10,  # Range 5-50, default 10
                    marks={i: str(i) for i in range(5, 51, 5)},  # Marks every 5 units
                    tooltip={"placement": "bottom", "always_visible": False},  # Tooltip settings
                ),
                html.Div(style={"height": "12px"}),  # Spacer
                dbc.Label("Minimum interest"),  # Slider label
                dcc.Slider(  # Slider for minimum interest threshold
                    id="min-interest-slider",
                    min=0, max=100, step=5, value=0,  # Range 0-100, default 0
                    marks={i: str(i) for i in range(0, 101, 20)},  # Marks every 20 units
                    tooltip={"placement": "bottom", "always_visible": False},  # Tooltip settings
                ),
                dbc.Button("Analyze", id="analyze-btn", color="primary", className="mt-4 w-100", n_clicks=0),  # Action button
                dcc.Download(id="download-csv"),  # Hidden download component
                # stores for caching data between callbacks
                dcc.Store(id="store-time-df"),  # Store for time series data
                dcc.Store(id="store-region-df"),  # Store for regional data
                dcc.Store(id="store-related"),  # Store for related queries data
            ]
        ),
    ],
    className="mb-4 shadow-sm",  # Bottom margin and shadow
)

# Card for displaying time series chart
time_series_card = dbc.Card(
    [
        dbc.CardHeader("Interest Over Time"),  # Card header
        dbc.CardBody(dcc.Graph(id="time-series-graph")),  # Graph container
    ],
    className="mb-4 shadow-sm",  # Bottom margin and shadow
)

# Card for displaying regional map
region_map_card = dbc.Card(
    [
        dbc.CardHeader("Interest by Country"),  # Card header
        dbc.CardBody(dcc.Graph(id="region-map-graph")),  # Graph container
    ],
    className="mb-4 shadow-sm",  # Bottom margin and shadow
)

# Card for displaying top regions chart
top_regions_card = dbc.Card(
    [
        dbc.CardHeader("Top Regions"),  # Card header
        dbc.CardBody(dcc.Graph(id="top-regions-graph")),  # Graph container
    ],
    className="mb-4 shadow-sm",  # Bottom margin and shadow
)

# Card for displaying related queries table
related_card = dbc.Card(
    [
        dbc.CardHeader("Top Related Queries"),  # Card header
        dbc.CardBody(
            [
                dash_table.DataTable(  # Data table for related queries
                    id="related-table",
                    columns=[],  # Columns will be populated dynamically
                    data=[],  # Data will be populated dynamically
                    page_size=10,  # Show 10 rows per page
                    style_table={"overflowX": "auto"},  # Horizontal scrolling
                    style_cell={"textAlign": "left"},  # Left align text
                ),
                html.Div(id="related-note", className="text-muted small mt-2"),  # Note display area
                dbc.Button("📥 Download Time Data", id="download-btn", color="secondary", className="mt-3"),  # Download button
            ]
        ),
    ],
    className="mb-4 shadow-sm",  # Bottom margin and shadow
)

# Main app layout
app.layout = html.Div(
    [
        navbar,  # Navigation bar at top
        dbc.Container(  # Main content container
            fluid=True,  # Full width container
            className="py-4",  # Vertical padding
            style={"backgroundColor": "#f7fbff"},  # Light blue background
            children=[
                dbc.Row(  # Main row
                    [
                        dbc.Col(filters_card, md=3, lg=3, xl=3),  # Filters column (25% width)
                        dbc.Col(  # Charts column (75% width)
                            [
                                dbc.Alert(id="alert-box", is_open=False, color="danger", className="mb-3"),  # Error alert
                                dbc.Row(  # First row of charts
                                    [
                                        dbc.Col(time_series_card, md=6),  # Time series chart (50% width)
                                        dbc.Col(region_map_card, md=6),  # Region map chart (50% width)
                                    ]
                                ),
                                dbc.Row(  # Second row of charts
                                    [
                                        dbc.Col(top_regions_card, md=6),  # Top regions chart (50% width)
                                        dbc.Col(related_card, md=6),  # Related queries table (50% width)
                                    ],
                                    className="mt-1",  # Small top margin
                                ),
                            ],
                            md=9, lg=9, xl=9,  # Column width (75%)
                        ),
                    ]
                ),
            ],
        ),
    ]
)

# Callbacks 
@app.callback(
    Output("store-time-df", "data"),  # Output: store time data
    Output("store-region-df", "data"),  # Output: store region data
    Output("store-related", "data"),  # Output: store related queries data
    Output("alert-box", "is_open"),  # Output: control alert visibility
    Output("alert-box", "children"),  # Output: alert message content
    Input("analyze-btn", "n_clicks"),  # Input: analyze button clicks
    State("keywords-input", "value"),  # State: keywords input value
    State("timeframe-dropdown", "value"),  # State: selected timeframe
    State("country-input", "value"),  # State: country input value
    prevent_initial_call=True,  # Don't run on app initialization
)
def run_analysis(n_clicks, keywords_raw, timeframe, country_raw):
    """
    Run Trends calls, serialize DataFrames for the other callbacks,
    and show clear alert messages when something is off.
    Also caches related queries (top + rising) so the table update
    doesn't make another network call.
    """
    try:
        raw_list = _parse_keywords(keywords_raw)  # Parse keywords input
        trimmed = False
        if keywords_raw:
            # Check if user entered more than 5 keywords
            user_count = len([p for p in (keywords_raw.split(",") if keywords_raw else []) if p.strip()])
            trimmed = user_count > len(raw_list)

        if not raw_list:  # If no valid keywords
            return None, None, None, True, "Please enter at least one keyword."

        geo = get_country_code(country_raw or "")  # Convert country input to code
        data_service.set_query(keywords=raw_list, timeframe=timeframe, geo=geo)  # Set query parameters

        time_df = data_service.fetch_interest_over_time()  # Fetch time series data
        region_df = data_service.get_interest_by_region()  # Fetch regional data

        # Fetch related once here
        frames = data_service.get_related_frames()  # Get related queries
        top_df = frames.get("top")  # Top related queries
        rising_df = frames.get("rising")  # Rising related queries
        related_json = {
            "top": top_df.to_json(orient="split") if isinstance(top_df, pd.DataFrame) else None,
            "rising": rising_df.to_json(orient="split") if isinstance(rising_df, pd.DataFrame) else None,
        }

        if time_df.empty:  # If no data returned
            msg = "No trend data returned. Try a longer timeframe (e.g., 'today 12-m') or different keywords."
            if trimmed:
                msg += " Note: only the first 5 keywords are used."
            return None, None, related_json, True, "❌ " + msg

        time_json = time_df.to_json(date_format="iso", orient="split")  # Serialize time data
        region_json = region_df.to_json(date_format="iso", orient="split") if not region_df.empty else None  # Serialize region data

        if trimmed:  # If keywords were trimmed
            return time_json, region_json, related_json, True, "ℹ️ Only the first 5 keywords were used."

        return time_json, region_json, related_json, False, ""  # Return success
    except Exception as e:
        return None, None, None, True, f"Something went wrong: {e}"  # Return error

@app.callback(
    Output("time-series-graph", "figure"),  # Output: time series graph
    Input("store-time-df", "data"),  # Input: stored time data
)
def update_time_series(time_json):
    if not time_json:  # If no data
        return {}  # Return empty figure
    df = pd.read_json(time_json, orient="split")  # Deserialize data
    fig = charts.plot_interest_over_time(df)  # Create chart
    return fig or {}  # Return figure or empty dict

@app.callback(
    Output("region-map-graph", "figure"),  # Output: region map graph
    Input("store-region-df", "data"),  # Input: stored region data
)
def update_region_map(region_json):
    if not region_json:  # If no data
        return {}  # Return empty figure
    df = pd.read_json(region_json, orient="split")  # Deserialize data
    fig = charts.plot_interest_map(df)  # Create map
    return fig or {}  # Return figure or empty dict

@app.callback(
    Output("top-regions-graph", "figure"),  # Output: top regions graph
    Input("store-region-df", "data"),  # Input: stored region data
    Input("store-time-df", "data"),  # Input: stored time data
    State("min-interest-slider", "value"),  # State: minimum interest value
    State("topn-slider", "value"),  # State: top N regions value
)
def update_top_regions(region_json, time_json, min_interest, top_n):
    if not region_json or not time_json:  # If missing data
        return {}  # Return empty figure
    region_df = pd.read_json(region_json, orient="split")  # Deserialize region data
    time_df = pd.read_json(time_json, orient="split")  # Deserialize time data

    if time_df.columns.size == 0:  # If no columns
        return {}  # Return empty figure
    first_keyword = str(time_df.columns[0])  # Get first keyword
    if first_keyword not in region_df.columns:  # If keyword not in region data
        return {}  # Return empty figure

    # Filter and sort regions
    fr = region_df[region_df[first_keyword] >= (min_interest or 0)].sort_values(
        by=first_keyword, ascending=False
    ).head(top_n or 10)

    if fr.empty:  # If no regions meet criteria
        return {}  # Return empty figure

    fr = fr.rename(columns={first_keyword: f"{first_keyword}_interest"})  # Rename column
    fig = charts.plot_top_regions(fr, f"{first_keyword}_interest")  # Create chart
    return fig or {}  # Return figure or empty dict

@app.callback(
    Output("related-table", "columns"),  # Output: table columns
    Output("related-table", "data"),  # Output: table data
    Output("related-note", "children"),  # Output: note under table
    Input("store-related", "data"),  # Input: stored related queries data
)
def update_related_table(related_json):
    if not related_json:  # If no data
        return [], [], ""  # Return empty table
    top_json = related_json.get("top")  # Get top queries data
    rising_json = related_json.get("rising")  # Get rising queries data

    df = None
    note = ""
    if top_json:  # If top queries available
        df = pd.read_json(top_json, orient="split")  # Deserialize data
        note = "Showing top related queries."
    elif rising_json:  # If rising queries available
        df = pd.read_json(rising_json, orient="split")  # Deserialize data
        note = "‘Top’ not available for this combo — showing rising queries instead."
    else:  # If no related queries
        return [], [], "No related queries available for this keyword/timeframe/region."

    if df is None or df.empty:  # If data is empty
        return [], [], "No related queries available for this keyword/timeframe/region."

    cols = [{"name": c, "id": c} for c in df.columns]  # Create column definitions
    data = df.to_dict("records")  # Convert to dictionary format for table
    return cols, data, note  # Return table components

@app.callback(
    Output("download-csv", "data"),  # Output: download data
    Input("download-btn", "n_clicks"),  # Input: download button clicks
    State("store-time-df", "data"),  # State: stored time data
    prevent_initial_call=True,  # Don't run on app initialization
)
def download_time_csv(n_clicks, time_json):
    if not time_json:  # If no data
        return None  # Cancel download
    df = pd.read_json(time_json, orient="split").reset_index().rename(columns={"index": "Date"})  # Prepare data
    buf = StringIO()  # Create in-memory file
    df.to_csv(buf, index=False)  # Convert to CSV
    return dict(content=buf.getvalue(), filename="interest_over_time.csv")  # Trigger download

if __name__ == "__main__":
    app.run(debug=True)  # Run app in debug mode