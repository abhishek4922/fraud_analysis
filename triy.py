import dash
from dash import dcc, html, Input, Output, State, dash_table, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64
from datetime import datetime
import numpy as np

# Initialize the Dash app with Bootstrap
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.FLATLY, 
                                     "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"],
                suppress_callback_exceptions=True)
app.title = "Insurance Fraud Analytics Dashboard"
server = app.server  # Required for deployment

# Define color palette - Enhanced for better contrast and accessibility
colors = {
    'primary': '#2C3E50',
    'primary_light': '#3E5771',
    'secondary': '#18BC9C',
    'secondary_light': '#2EEBC8',
    'danger': '#E74C3C',
    'danger_light': '#F5B4AE',
    'warning': '#F39C12',
    'warning_light': '#FAD7A0',
    'info': '#3498DB',
    'info_light': '#AED6F1',
    'light': '#ECF0F1',
    'dark': '#95A5A6',
    'background': '#F9FAFB',
    'card': '#FFFFFF',
    'text': '#34495E'
}

# Dashboard header with logo and title
header = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.I(className="fas fa-shield-alt me-2 fa-lg", 
                                      style={"color": colors['secondary']}), 
                               width="auto"),
                        dbc.Col(dbc.NavbarBrand("Insurance Fraud Analytics", 
                                               className="ms-2 fw-bold")),
                    ],
                    align="center",
                ),
                href="#",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Dashboard", active=True, href="#")),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ],
        fluid=True,
    ),
    color="primary",
    dark=True,
    className="mb-4 shadow-sm",
    sticky="top",
)

# Enhanced file upload card
# Upload Card Component
# Add dcc.Download component for handling file downloads
download_component = dcc.Download(id="download-sample-template")

# Upload Card Component
upload_card = dbc.Card(
    [
        dbc.CardHeader([
            html.I(className="fas fa-cloud-upload-alt me-2", style={"color": colors['info']}),
            "Data Source"
        ], className="d-flex align-items-center fw-bold"),
        dbc.CardBody(
            [
                # Upload area with hover effect
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        html.Div([
                            html.I(className="fas fa-file-excel fa-2x mb-2", style={"color": colors['info']}),
                            html.Div('Drag and Drop or Select File', className="fw-bold"),
                            html.Div('Excel (.xlsx) format only', className="text-muted small")
                        ], className="d-flex flex-column align-items-center justify-content-center")
                    ]),
                    style={
                        'width': '100%',
                        'height': '150px',
                        'borderWidth': '2px',
                        'borderStyle': 'dashed',
                        'borderRadius': '12px',
                        'borderColor': colors['info'],
                        'textAlign': 'center',
                        'background': f"{colors['light']}80",
                        'transition': 'all 0.3s',
                        'cursor': 'pointer',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center'
                    },
                    className="upload-box",
                    multiple=False
                ),
                # Upload status area with animation
                html.Div(id="upload-status", className="mt-3 text-center"),
                # Required Columns section with improved styling and larger font
                html.Div(
                    [
                        html.Div([
                            html.I(className="fas fa-list-check me-2", style={"color": colors['info']}),
                            html.H6("Required Columns", className="mb-0 fs-5")  # Increased size with fs-5
                        ], className="d-flex align-items-center mt-4 mb-3"),
                        html.Div(
                            [
                                dbc.Badge(col_name, color="primary", pill=True, 
                                          className="me-2 mb-2 px-3 py-2 fs-6")  # Increased badge font
                                for col_name in [
                                    "Policy Number", "State", "City", "Postcode", "Channel", 
                                    "Policy Start", "Death Date", "Intimation Date", 
                                    "Days to Death", "Fraud Category"
                                ]
                            ],
                            style={"display": "flex", "flexWrap": "wrap"}
                        ),
                        # Info tooltip/popover
                        html.Div([
                            dbc.Button(
                                html.I(className="fas fa-info-circle"),
                                id="tooltip-target",
                                color="link",
                                size="sm",
                                className="text-muted p-0"
                            ),
                            dbc.Tooltip(
                                "Column names in your Excel file should match these required fields.",
                                target="tooltip-target",
                                placement="top"
                            ),
                        ], className="mt-2 text-end")
                    ],
                    className="bg-light p-3 rounded",
                    style={"fontSize": "1rem"}  # Increased base font size for the entire section
                ),
                # Download Sample Template Section
                html.Div([
                    html.A([
                        html.I(className="fas fa-download me-2"),
                        "Download Sample Template"
                    ], 
                    href="#", 
                    className="text-decoration-none text-primary fw-bold", 
                    id="download-sample"
                    )
                ], className="mt-3 text-center"),
                download_component  # Add the dcc.Download component here
            ]
        ),
    ],
    className="mb-4 shadow",
    style={"border-radius": "15px", "border": "none"}
)

# Callback to Generate and Serve the Sample Template
@app.callback(
    Output("download-sample-template", "data"),  # Output to dcc.Download
    Input("download-sample", "n_clicks"),       # Trigger on button click
    prevent_initial_call=True
)
def download_sample_template(n_clicks):
    if n_clicks:
        try:
            # Path to the sample file in the local folder
            file_path = "Fraud data FY 2023-24 for B&CC (1)NOCLAIM.xlsx"
            
            # Read the file into memory
            with open(file_path, "rb") as file:
                file_content = file.read()
            
            # Return the file for download
            return dcc.send_bytes(
                file_content,
                filename="Sample_Template.xlsx",
                type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            print(f"Error loading sample file: {str(e)}")
            return None
# Filters component as a collapsible sidebar card
filters_card = dbc.Card(
    [
        dbc.CardHeader([
            html.Div([
                html.I(className="fas fa-filter me-2", style={"color": colors['info']}),
                "Filters",
                dbc.Button(
                    html.I(className="fas fa-chevron-down"),
                    id="collapse-button",
                    color="link",
                    className="ms-auto p-0"
                )
            ], className="d-flex align-items-center justify-content-between")
        ]),
        dbc.Collapse(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("State:", className="fw-bold mb-1"),
                        dcc.Dropdown(
                            id="state-filter", 
                            multi=True, 
                            placeholder="Select state(s)...",
                            className="mb-3",
                            style={"borderRadius": "6px"}
                        )
                    ], md=6),
                    dbc.Col([
                        html.Label("Channel:", className="fw-bold mb-1"),
                        dcc.Dropdown(
                            id="channel-filter", 
                            multi=True, 
                            placeholder="Select channel(s)...",
                            className="mb-3",
                            style={"borderRadius": "6px"}
                        )
                    ], md=6)
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Label("Date Range (Policy Start):", className="fw-bold mb-1"),
                        dcc.DatePickerRange(
                            id='date-range-filter',
                            className="mb-3",
                            start_date_placeholder_text="Start Date",
                            end_date_placeholder_text="End Date",
                            calendar_orientation='horizontal',
                        )
                    ], md=12)
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-search me-2"), "Apply Filters"],
                            id="apply-filters", 
                            color="primary", 
                            className="me-2"
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-undo me-2"), "Reset"],
                            id="reset-filters", 
                            color="secondary",
                            outline=True
                        )
                    ], className="d-flex justify-content-end")
                ])
            ]),
            id="filters-collapse",
            is_open=True,
        )
    ],
    className="mb-4 shadow-sm",
    style={"border-radius": "8px"}
)

# Enhanced KPI metrics card with trend indicators
def create_kpi_card(title, value, color, icon, description=None, trend=None):
    trend_icon = "fa-arrow-up" if trend and trend > 0 else "fa-arrow-down"
    trend_color = "success" if trend and trend > 0 else "danger"
    trend_element = html.Div([
        html.I(className=f"fas {trend_icon} me-1"),
        f"{abs(trend)}% {description or ''}"
    ], className=f"text-{trend_color} small mt-1") if trend is not None else None
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Div(
                    html.I(className=f"{icon}", 
                          style={"color": color, "font-size": "2rem"}),
                    className="p-3 rounded-circle mb-3",
                    style={"background": f"rgba({','.join(str(int(c)) for c in px.colors.hex_to_rgb(color)[:3])}, 0.2)"}
                ),
                html.H6(title, className="text-muted mb-2"),
                html.H3(value, className="mb-1 fw-bold", style={"color": colors['text']}),
                trend_element
            ], className="text-center")
        ]),
        className="mb-4 shadow-sm h-100",
        style={"border-radius": "8px", "border": "none"}
    )

# Chart card template for consistent styling
def create_chart_card(title, chart_id, icon="fas fa-chart-bar", help_text=None):
    header = html.Div([
        html.I(className=f"{icon} me-2", style={"color": colors['info']}),
        title,
        dbc.Button(
            html.I(className="fas fa-question-circle"),
            id=f"{chart_id}-help",
            color="link",
            className="ms-auto p-0",
            style={"color": colors['dark']}
        ) if help_text else None
    ], className="d-flex align-items-center justify-content-between")
    tooltip = dbc.Tooltip(
        help_text,
        target=f"{chart_id}-help",
        placement="top"
    ) if help_text else None
    return html.Div([
        dbc.Card([
            dbc.CardHeader(header),
            dbc.CardBody([
                dcc.Graph(
                    id=chart_id, 
                    config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['select2d', 'lasso2d']
                    },
                    style={"height": "100%"}
                )
            ], style={"minHeight": "300px"})
        ], className="shadow-sm h-100", style={"border-radius": "8px"}),
        tooltip
    ])

# Create a layout with sidebar and main content area
app.layout = html.Div([
    header,
    dbc.Container([
        dbc.Row([
            dbc.Col([
                upload_card
            ], width=12)
        ]),
        dbc.Spinner(
            html.Div(id="loading-output"),
            color="primary",
            spinner_style={"width": "3rem", "height": "3rem"},
            fullscreen=True,
            fullscreen_style={"backgroundColor": "rgba(0, 0, 0, 0.3)"}
        ),
        html.Div(id="dashboard-content", style={"display": "none"}, children=[
            dbc.Row([
                dbc.Col([
                    filters_card
                ], md=4),
                dbc.Col([
                    dbc.Row(id="kpi-metrics")
                ], md=8)
            ]),
            dbc.Tabs([
                dbc.Tab(label="Overview", tab_id="tab-overview", children=[
                    dbc.Row([
                        dbc.Col([
                            create_chart_card(
                                "Fraud Count by Channel", 
                                "channel-bar",
                                icon="fas fa-sitemap",
                                help_text="Distribution of fraud cases across different channels"
                            )
                        ], md=6, className="mb-4"),
                        dbc.Col([
                            create_chart_card(
                                "Top 10 Postcodes", 
                                "top-postcodes-bar",
                                icon="fas fa-map-marker-alt",
                                help_text="Top 10 postcodes with highest number of frauds"
                            )
                        ], md=6, className="mb-4")
                    ])
                ], className="mt-3"),
                dbc.Tab(label="Geographic Analysis", tab_id="tab-geo", children=[
                    dbc.Row([
                        dbc.Col([
                            create_chart_card(
                                "State-City Fraud Distribution", 
                                "treemap",
                                icon="fas fa-map",
                                help_text="Hierarchical view of fraud distribution by state and city"
                            )
                        ], width=12, className="my-4")
                    ]),
                    dbc.Row([
                        dbc.Col([
                            create_chart_card(
                                "State-wise Distribution of Channels", 
                                "state-channel-bar",
                                icon="fas fa-building",
                                help_text="Distribution of channels across different states"
                            )
                        ], width=12, className="mb-4")
                    ])
                ], className="mt-3"),
                dbc.Tab(label="Time Analysis", tab_id="tab-time", children=[
                    dbc.Row([
                        dbc.Col([
                            create_chart_card(
                                "Days Between Policy Start and Death", 
                                "policy-death-hist",
                                icon="fas fa-hourglass-half",
                                help_text="Distribution of days between policy start and death date"
                            )
                        ], md=6, className="mb-4"),
                        dbc.Col([
                            create_chart_card(
                                "Intimation Delay Analysis", 
                                "intimation-delay-hist",
                                icon="fas fa-clock",
                                help_text="Distribution of days between death and claim intimation"
                            )
                        ], md=6, className="mb-4")
                    ])
                ], className="mt-3"),
                dbc.Tab(label="Data Table", tab_id="tab-data", children=[
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.I(className="fas fa-table me-2", style={"color": colors['info']}),
                                html.Span("Fraud Cases Data", className="fw-bold"),
                                dbc.ButtonGroup([
                                    dbc.Button(
                                        [html.I(className="fas fa-download me-2"), "Export CSV"],
                                        id="export-csv", 
                                        color="primary", 
                                        size="sm",
                                        className="ms-2"
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-cog me-2"), "Columns"],
                                        id="column-settings", 
                                        color="secondary", 
                                        size="sm",
                                        outline=True,
                                        className="ms-2"
                                    )
                                ], className="ms-auto")
                            ], className="d-flex align-items-center justify-content-between")
                        ]),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id='data-table',
                                page_size=15,
                                style_table={
                                    'overflowX': 'auto',
                                    'border': 'none',
                                },
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '12px 8px',
                                    'minWidth': '100px',
                                    'width': '150px',
                                    'maxWidth': '300px',
                                    'whiteSpace': 'normal',
                                    'height': 'auto',
                                    'fontFamily': '"Segoe UI", Arial, sans-serif',
                                    'fontSize': '13px'
                                },
                                style_header={
                                    'backgroundColor': colors['light'],
                                    'fontWeight': 'bold',
                                    'borderBottom': f'2px solid {colors["primary"]}',
                                    'textAlign': 'center'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgba(0, 0, 0, 0.03)'
                                    },
                                    {
                                        'if': {'filter_query': '{Fraud Category} != ""'},  
                                        'backgroundColor': colors['danger_light'],
                                        'fontWeight': 'bold'
                                    }
                                ],
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                page_action="native",
                                export_format="csv",
                                row_selectable="multi"
                            )
                        ])
                    ], className="shadow-sm", style={"border-radius": "8px"})
                ], className="mt-3"),
            ], id="tabs", active_tab="tab-overview", className="custom-tabs")
        ]),
        html.Footer([
            html.Hr(),
            html.P("© 2025 Insurance Fraud Analytics Dashboard", className="text-center text-muted")
        ], className="mt-5"),
        dcc.Store(id='processed-data'),
        dcc.Store(id='filtered-data'),
        dcc.Store(id='filter-state')
    ], fluid=True, className="pb-5")
], style={"backgroundColor": colors['background'], "minHeight": "100vh"})

# Custom CSS for the app
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .custom-tabs .nav-link.active {
                color: #2C3E50 !important;
                font-weight: bold;
                border-bottom: 3px solid #18BC9C !important;
                border-top: none;
                border-left: none;
                border-right: none;
                background-color: transparent !important;
            }
            .custom-tabs .nav-link {
                color: #95A5A6;
                border: none;
                padding-bottom: 12px;
                transition: all 0.3s ease;
            }
            .custom-tabs .nav-link:hover:not(.active) {
                color: #18BC9C;
                border-bottom: 3px solid #ECF0F1;
            }
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th, 
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td {
                border: none !important;
            }
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner tr:hover {
                background-color: rgba(52, 152, 219, 0.1) !important;
            }
            /* Card hover effect */
            .card {
                transition: all 0.3s ease;
                border: none;
            }
            .card:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1) !important;
            }
            /* Tooltip styling */
            .tooltip-inner {
                max-width: 200px;
                padding: 8px 12px;
                background-color: #2C3E50;
                border-radius: 4px;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Callback to toggle the filter collapse
@app.callback(
    [Output("filters-collapse", "is_open"),
     Output("collapse-button", "children")],
    [Input("collapse-button", "n_clicks")],
    [State("filters-collapse", "is_open")]
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open, html.I(className=f"fas fa-chevron-{'up' if not is_open else 'down'}")
    return is_open, html.I(className="fas fa-chevron-down")

# Callback to parse uploaded data
@app.callback(
    [Output('processed-data', 'data'),
     Output('upload-status', 'children'),
     Output('state-filter', 'options'),
     Output('channel-filter', 'options'),
     Output('dashboard-content', 'style'),
     Output('loading-output', 'children')],
    Input('upload-data', 'contents'),
    prevent_initial_call=True
)
def parse_contents(contents):
    if contents is None:
        return [None, None, [], [], {"display": "none"}, None]
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))
        # Preprocess date columns
        for col in ['POLICYRISKCOMMENCEMENTDATE', 'Date of Death', 'INTIMATIONDATE']:
            df[col] = pd.to_datetime(df[col], errors='coerce')  
        # Calculate time differences
        df['Policy_to_Death_Days'] = (df['Date of Death'] - df['POLICYRISKCOMMENCEMENTDATE']).dt.days
        df['Death_to_Intimation_Days'] = (df['INTIMATIONDATE'] - df['Date of Death']).dt.days
        # Generate options for dropdown filters
        state_options = [{'label': state, 'value': state} for state in sorted(df['CORRESPONDENCESTATE'].dropna().unique())]
        channel_options = [{'label': channel, 'value': channel} for channel in sorted(df['CHANNEL'].dropna().unique())]
        # Success message with more details
        record_count = len(df)
        fraud_count = df[df['Fraud Category'].notna() & (df['Fraud Category'] != "No Fraud")].shape[0]
        fraud_percent = round((fraud_count / record_count) * 100, 1) if record_count > 0 else 0
        success_message = dbc.Alert([
            html.Div([
                html.I(className="fas fa-check-circle me-2"),
                html.Span("Data loaded successfully!", className="fw-bold"),
            ], className="mb-2"),
            html.Div([
                html.Span(f"Total records: {record_count:,}", className="me-3"),
                html.Span(f"Fraud cases: {fraud_count:,}", className="me-3"),
                html.Span(f"Fraud rate: {fraud_percent}%")
            ], className="small")
        ], color="success", dismissable=True)
        # Convert DataFrame to dictionary for storage
        df_dict = df.to_dict('records')
        return [df_dict, success_message, state_options, channel_options, {"display": "block"}, None]
    except Exception as e:
        error_message = dbc.Alert([
            html.I(className="fas fa-exclamation-circle me-2"),
            html.Span("Error processing file", className="fw-bold me-2"),
            html.Span(f"{str(e)}", className="small")
        ], color="danger", dismissable=True)
        return [None, error_message, [], [], {"display": "none"}, None]

# Callback to store filter state and filter data
@app.callback(
    [Output('filtered-data', 'data'),
     Output('filter-state', 'data')],
    [Input('processed-data', 'data'),
     Input('apply-filters', 'n_clicks'),
     Input('reset-filters', 'n_clicks')],
    [State('state-filter', 'value'),
     State('channel-filter', 'value'),
     State('date-range-filter', 'start_date'),
     State('date-range-filter', 'end_date')],
    prevent_initial_call=True
)
def filter_data(data, apply_clicks, reset_clicks, states, channels, start_date, end_date):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    if trigger_id == 'reset-filters':
        return data, {'states': None, 'channels': None, 'start_date': None, 'end_date': None}
    if not data:
        return None, None
    # Store filter state
    filter_state = {'states': states, 'channels': channels, 'start_date': start_date, 'end_date': end_date}
    # Apply filters
    df = pd.DataFrame(data)
    if states and len(states) > 0:
        df = df[df['CORRESPONDENCESTATE'].isin(states)]
    if channels and len(channels) > 0:
        df = df[df['CHANNEL'].isin(channels)]
    if start_date:
        start_date = pd.to_datetime(start_date)
        df = df[df['POLICYRISKCOMMENCEMENTDATE'] >= start_date]
    if end_date:
        end_date = pd.to_datetime(end_date)
        df = df[df['POLICYRISKCOMMENCEMENTDATE'] <= end_date]
    return df.to_dict('records'), filter_state

# Callback to update KPI metrics
@app.callback(
    Output('kpi-metrics', 'children'),
    Input('filtered-data', 'data'),
    prevent_initial_call=True
)
def update_kpi_metrics(filtered_data):
    if not filtered_data:
        return []
    # Convert to DataFrame
    df = pd.DataFrame(filtered_data)
    # Filter out rows where Fraud Category is NA or "No Fraud"
    fraud_filtered_df = df[df['Fraud Category'].notna() & (df['Fraud Category'] != "No Fraud")]
    # Calculate KPIs
    total_cases = len(df)
    fraud_cases = len(fraud_filtered_df)
    fraud_rate = round((fraud_cases / total_cases) * 100, 1) if total_cases > 0 else 0
    avg_policy_to_death = round(df['Policy_to_Death_Days'].mean(), 1)
    # Mock trend data (in a real app, this would be calculated from historical data)
    fraud_trend = 5.2  
    policy_trend = -2.8  
    # Return KPI cards in a row layout
    return [
        dbc.Col([
            create_kpi_card(
                "Total Cases", 
                f"{total_cases:,}", 
                colors['primary'], 
                "fas fa-file-alt"
            )
        ], lg=3, md=6, className="mb-4"),
        dbc.Col([
            create_kpi_card(
                "Fraud Cases", 
                f"{fraud_cases:,}", 
                colors['danger'], 
                "fas fa-exclamation-triangle"
            )
        ], lg=3, md=6, className="mb-4"),
        dbc.Col([
            create_kpi_card(
                "Fraud Rate", 
                f"{fraud_rate}%", 
                colors['warning'], 
                "fas fa-percent", 
                description="from previous period",
                trend=fraud_trend
            )
        ], lg=3, md=6, className="mb-4"),
        dbc.Col([
            create_kpi_card(
                "Avg. Policy to Death", 
                f"{avg_policy_to_death} days", 
                colors['info'], 
                "fas fa-calendar-alt",
                description="from previous period",
                trend=policy_trend
            )
        ], lg=3, md=6, className="mb-4")
    ]

# Enhanced plotly theme for consistent chart styling
def apply_chart_theme(fig):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family="'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        font_size=12,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        ),
        colorway=[colors['primary'], colors['secondary'], colors['danger'], 
                 colors['warning'], colors['info'], colors['dark']],
        hoverlabel=dict(
            bgcolor=colors['light'],
            font_size=12,
            font_family="'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        )
    )
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.05)',
        showline=True,
        linewidth=1,
        linecolor='rgba(0,0,0,0.2)'
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.05)',
        showline=True,
        linewidth=1,
        linecolor='rgba(0,0,0,0.2)'
    )
    return fig

# Callback to update all charts
@app.callback(
    [Output('treemap', 'figure'),
     Output('channel-bar', 'figure'),
     Output('policy-death-hist', 'figure'),
     Output('state-channel-bar', 'figure'),
     Output('top-postcodes-bar', 'figure'),
     Output('intimation-delay-hist', 'figure'),
     Output('data-table', 'data'),
     Output('data-table', 'columns')],
    Input('filtered-data', 'data'),
    prevent_initial_call=True
)
def update_all_visualizations(filtered_data):
    if not filtered_data:
        empty_fig = px.scatter(title="No data available")
        empty_fig = apply_chart_theme(empty_fig)
        empty_fig.update_layout(
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return [empty_fig] * 6 + [[], []]
    
    # Convert to DataFrame
    df = pd.DataFrame(filtered_data)
    # Ensure date columns are datetime
    for col in ['POLICYRISKCOMMENCEMENTDATE', 'Date of Death', 'INTIMATIONDATE']:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Check if filtered DataFrame is empty
    if df.empty:
        empty_fig = px.scatter(title="No data matches the selected filters")
        empty_fig = apply_chart_theme(empty_fig)
        empty_fig.update_layout(
            annotations=[{
                'text': 'No data matches the selected filters',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return [empty_fig] * 6 + [[], []]
    
    # Filter out rows where Fraud Category is NA or "No Fraud"
    fraud_filtered_df = df[df['Fraud Category'].notna() & (df['Fraud Category'] != "No Fraud")]
    
    # Generate enhanced figures using the filtered DataFrame
    treemap_data = fraud_filtered_df.groupby(['CORRESPONDENCESTATE', 'CORRESPONDENCECITY']).size().reset_index(name='Count')
    fig1 = px.treemap(
        treemap_data,
        path=['CORRESPONDENCESTATE', 'CORRESPONDENCECITY'],
        values='Count',
        color='Count',
        color_continuous_scale=['#18BC9C', '#2C3E50'],
        hover_data={'Count': True},
        title="Fraud Distribution by State and City"
    )
    fig1.update_traces(
        hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>',
        textinfo='label+value'
    )
    fig1 = apply_chart_theme(fig1)
    
    channel_data = fraud_filtered_df.groupby('CHANNEL').size().reset_index(name='Count')
    fig2 = px.bar(
        channel_data,
        x='CHANNEL',
        y='Count',
        color='Count',
        color_continuous_scale=['#AED6F1', '#3498DB'],
        text='Count',
        title="Fraud Count by Distribution Channel"
    )
    fig2.update_traces(
        texttemplate='%{text}',
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>',
        marker=dict(line=dict(width=1, color='#FFFFFF'))
    )
    fig2.update_layout(xaxis_title="Channel", yaxis_title="Number of Fraud Cases")
    fig2 = apply_chart_theme(fig2)
    
    fig3 = px.histogram(
        fraud_filtered_df,
        x='Policy_to_Death_Days',
        nbins=30,
        opacity=0.8,
        color_discrete_sequence=[colors['info']],
        marginal='box',
        title="Days Between Policy Start and Death"
    )
    fig3.update_traces(
        marker=dict(line=dict(width=1, color='white')),
        hovertemplate='Days: %{x}<br>Count: %{y}<extra></extra>'
    )
    fig3.update_layout(
        xaxis_title="Number of Days",
        yaxis_title="Number of Cases",
        bargap=0.1
    )
    fig3 = apply_chart_theme(fig3)
    
    median_days = fraud_filtered_df['Policy_to_Death_Days'].median()
    fig3.add_shape(
        type="line",
        x0=median_days,
        y0=0,
        x1=median_days,
        y1=1,
        yref="paper",
        line=dict(color=colors['danger'], width=2, dash="dash"),
    )
    fig3.add_annotation(
        x=median_days,
        y=0.95,
        yref="paper",
        text=f"Median: {median_days:.0f} days",
        showarrow=True,
        arrowhead=2,
        arrowcolor=colors['danger'],
        arrowsize=1,
        arrowwidth=2,
        bgcolor=colors['light'],
        bordercolor=colors['danger'],
        borderwidth=1,
        borderpad=4,
        font=dict(color=colors['danger'])
    )
    
    state_channel_data = fraud_filtered_df.groupby(['CORRESPONDENCESTATE', 'CHANNEL']).size().reset_index(name='Count')
    top_states = fraud_filtered_df['CORRESPONDENCESTATE'].value_counts().nlargest(10).index.tolist()
    state_channel_data = state_channel_data[state_channel_data['CORRESPONDENCESTATE'].isin(top_states)]
    fig4 = px.bar(
        state_channel_data,
        x='CORRESPONDENCESTATE',
        y='Count',
        color='CHANNEL',
        title="Channel Distribution by State (Top 10 States)",
        barmode='stack',
        text='Count'
    )
    fig4.update_traces(
        textposition='inside',
        texttemplate='%{text}',
        hovertemplate='<b>%{x}</b><br>Channel: %{fullData.name}<br>Count: %{y}<extra></extra>',
        marker=dict(line=dict(width=0.5, color='white'))
    )
    fig4.update_layout(
        xaxis_title="State",
        yaxis_title="Number of Cases",
        legend_title="Channel"
    )
    fig4 = apply_chart_theme(fig4)
    
    fraud_filtered_df['Postcode_City'] = fraud_filtered_df['CORRESPONDENCEPOSTCODE'].astype(str) + " (" + fraud_filtered_df['CORRESPONDENCECITY'] + ")"
    postcode_data = fraud_filtered_df.groupby('Postcode_City').size().reset_index(name='Count').nlargest(10, 'Count')
    postcode_data = postcode_data.sort_values('Count', ascending=True)  
    fig5 = px.bar(
        postcode_data,
        y='Postcode_City',
        x='Count',
        title="Top 10 Postcodes with Highest Number of Frauds",
        orientation='h',
        color='Count',
        color_continuous_scale=['#FAD7A0', '#F39C12'],
        text='Count'
    )
    fig5.update_traces(
        texttemplate='%{text}',
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>',
        marker=dict(line=dict(width=1, color='white'))
    )
    fig5.update_layout(
        yaxis_title="Postcode (City)",
        xaxis_title="Number of Cases"
    )
    fig5 = apply_chart_theme(fig5)
    
    fig6 = px.histogram(
        fraud_filtered_df,
        x='Death_to_Intimation_Days',
        nbins=30,
        opacity=0.8,
        color_discrete_sequence=[colors['secondary']],
        marginal='box',
        title="Delay Between Death and Claim Intimation"
    )
    fig6.update_traces(
        marker=dict(line=dict(width=1, color='white')),
        hovertemplate='Days: %{x}<br>Count: %{y}<extra></extra>'
    )
    fig6.update_layout(
        xaxis_title="Number of Days",
        yaxis_title="Number of Cases",
        bargap=0.1
    )
    fig6 = apply_chart_theme(fig6)
    
    # Add a vertical line at median value
    median_intimation = fraud_filtered_df['Death_to_Intimation_Days'].median()
    fig6.add_shape(
        type="line",
        x0=median_intimation,
        y0=0,
        x1=median_intimation,
        y1=1,
        yref="paper",
        line=dict(color=colors['secondary'], width=2, dash="dash"),
    )
    fig6.add_annotation(
        x=median_intimation,
        y=0.95,
        yref="paper",
        text=f"Median: {median_intimation:.0f} days",
        showarrow=True,
        arrowhead=2,
        arrowcolor=colors['secondary'],
        arrowsize=1,
        arrowwidth=2,
        bgcolor=colors['light'],
        bordercolor=colors['secondary'],
        borderwidth=1,
        borderpad=4,
        font=dict(color=colors['secondary'])
    )

    # Data table with improved formatting
    columns = [
        {"name": "Policy Number", "id": "Dummy Policy No", "selectable": True},
        {"name": "State", "id": "CORRESPONDENCESTATE", "selectable": True},
        {"name": "City", "id": "CORRESPONDENCECITY", "selectable": True},
        {"name": "Postcode", "id": "CORRESPONDENCEPOSTCODE", "selectable": True},
        {"name": "Channel", "id": "CHANNEL", "selectable": True},
        {"name": "Policy Start", "id": "POLICYRISKCOMMENCEMENTDATE", "selectable": True},
        {"name": "Death Date", "id": "Date of Death", "selectable": True},
        {"name": "Intimation Date", "id": "INTIMATIONDATE", "selectable": True},
        {"name": "Days to Death", "id": "Policy_to_Death_Days", "selectable": True, "type": "numeric", "format": {"specifier": ",.0f"}},
        {"name": "Fraud Category", "id": "Fraud Category", "selectable": True}
    ]
    
    # Create a copy of filtered_df for the data table
    table_df = fraud_filtered_df.copy()
    
    # Format dates for table display
    for date_col in ['POLICYRISKCOMMENCEMENTDATE', 'Date of Death', 'INTIMATIONDATE']:
        table_df[date_col] = table_df[date_col].dt.strftime('%Y-%m-%d')
    
    # Select only necessary columns for table display
    table_data = table_df[[col['id'] for col in columns]].to_dict('records')

    return fig1, fig2, fig3, fig4, fig5, fig6, table_data, columns

# Callback for exporting CSV
@app.callback(
    Output("export-csv", "n_clicks"),
    Input("export-csv", "n_clicks"),
    State("filtered-data", "data"),
    prevent_initial_call=True
)
def export_csv(n_clicks, data):
    if n_clicks and data:
        # In a real app, this would trigger a download
        # For Dash, you'd typically use dcc.Download component
        print("CSV export triggered")
    return None

# Reset filters callback
@app.callback(
    [Output("state-filter", "value"),
     Output("channel-filter", "value"),
     Output("date-range-filter", "start_date"),
     Output("date-range-filter", "end_date")],
    Input("reset-filters", "n_clicks"),
    prevent_initial_call=True
)
def reset_filters(n_clicks):
    return None, None, None, None

# Help tooltips callbacks
for chart_id in ["treemap", "channel-bar", "policy-death-hist", 
                "state-channel-bar", "top-postcodes-bar", 
                "intimation-delay-hist"]:
    @app.callback(
        Output(f"{chart_id}-help", "children"),
        Input(f"{chart_id}-help", "n_clicks"),
        prevent_initial_call=True
    )
    def help_tooltip_click(n_clicks):
        return html.I(className="fas fa-question-circle")

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)