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

# Initialize the Dash app with a modern Bootstrap theme
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.LUX],  # Updated theme
                suppress_callback_exceptions=True)
app.title = "Insurance Fraud Analytics Dashboard"

# Define color palette
colors = {
    'primary': '#2C3E50',
    'secondary': '#18BC9C',
    'danger': '#E74C3C',
    'warning': '#F39C12',
    'info': '#3498DB',
    'light': '#ECF0F1',
    'dark': '#95A5A6'
}

# Navbar component with enhanced styling
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.I(className="fas fa-shield-alt me-2 text-light"), width="auto"),
                        dbc.Col(dbc.NavbarBrand("Insurance Fraud Analytics", className="ms-2 text-light")),
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
                        dbc.NavItem(dbc.NavLink("Dashboard", href="#", className="text-light")),
                        dbc.NavItem(dbc.NavLink("Documentation", href="#", className="text-light")),
                        dbc.NavItem(dbc.NavLink("About", href="#", className="text-light")),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ]
    ),
    color="primary",
    dark=True,
    className="mb-4 shadow-sm",  # Added shadow for depth
)

# File upload component with enhanced UI
upload_card = dbc.Card(
    [
        dbc.CardHeader([
            html.I(className="fas fa-upload me-2"),
            "Upload Data Source"
        ], className="bg-primary text-light"),
        dbc.CardBody(
            [
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        html.I(className="fas fa-file-excel me-2"),
                        'Drag & Drop or ',
                        html.A('Select Excel File (.xlsx)', className="text-primary fw-bold")
                    ]),
                    style={
                        'width': '100%', 
                        'height': '60px', 
                        'lineHeight': '60px',
                        'borderWidth': '2px', 
                        'borderStyle': 'dashed', 
                        'borderRadius': '10px',
                        'textAlign': 'center',
                        'transition': 'border-color 0.3s ease-in-out',
                        'cursor': 'pointer'
                    },
                    multiple=False
                ),
                html.Div(id="upload-status", className="mt-2")
            ]
        ),
    ],
    className="mb-4 shadow-sm",  # Added shadow for depth
)

# Filters component with tooltips
filters_card = dbc.Card(
    [
        dbc.CardHeader([
            html.I(className="fas fa-filter me-2"),
            "Filters"
        ], className="bg-secondary text-light"),
        dbc.CardBody(
            [
                dbc.Row([
                    dbc.Col([
                        html.Label("State:"),
                        dbc.Tooltip("Filter by state(s)", target="state-filter-tooltip"),
                        dcc.Dropdown(id="state-filter", multi=True, placeholder="Select state(s)...", className="mt-1"),
                        html.Div(id="state-filter-tooltip", style={"display": "none"})
                    ], width=6),
                    dbc.Col([
                        html.Label("Channel:"),
                        dbc.Tooltip("Filter by channel(s)", target="channel-filter-tooltip"),
                        dcc.Dropdown(id="channel-filter", multi=True, placeholder="Select channel(s)...", className="mt-1"),
                        html.Div(id="channel-filter-tooltip", style={"display": "none"})
                    ], width=6)
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Apply Filters", id="apply-filters", color="primary", className="mt-3 w-100"),
                    ], width=12, className="text-center")
                ])
            ]
        )
    ],
    className="mb-4 shadow-sm",  # Added shadow for depth
)

# KPI metrics component with hover effects
def create_kpi_card(title, value, color, icon, comparison=None):
    comparison_element = html.Div([
        html.I(className=f"fas fa-arrow-{'up' if comparison > 0 else 'down'} me-1"),
        f"{abs(comparison)}% from previous period"
    ], className=f"text-{'success' if comparison > 0 else 'danger'} small") if comparison is not None else None
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H4(title, className="text-muted mb-0"),
                    html.H2([
                        html.I(className=f"{icon} me-2", style={"color": color}),
                        value
                    ], className="mb-0"),
                    comparison_element
                ])
            ])
        ]),
        className="mb-4 shadow-sm",  # Added shadow for depth
        style={"transition": "transform 0.3s ease-in-out", "cursor": "pointer"},
        id={"type": "kpi-card", "index": title},
    )

# Callback to add hover effect to KPI cards
@app.callback(
    Output({"type": "kpi-card", "index": dash.ALL}, "style"),
    Input({"type": "kpi-card", "index": dash.ALL}, "n_clicks")
)
def hover_kpi_cards(n_clicks):
    styles = [{"transform": "scale(1.05)"} if nc else {"transform": "scale(1)"} for nc in n_clicks]
    return styles

# Create a layout with tabs and improved styling
app.layout = html.Div([
    navbar,
    dbc.Container([
        dbc.Row([
            dbc.Col([
                upload_card
            ], width=12)
        ]),
        # Loading spinner with animation
        dbc.Spinner(
            html.Div(id="loading-output"),
            color="primary",
            spinner_style={"width": "3rem", "height": "3rem", "animation": "spin 1s linear infinite"}
        ),
        html.Div(id="dashboard-content", style={"display": "none"}, children=[
            # Filters section
            dbc.Row([
                dbc.Col([
                    filters_card
                ], width=12)
            ]),
            # KPI metrics
            dbc.Row(id="kpi-metrics"),
            # Tabs for different visualization groups
            dbc.Tabs([
                dbc.Tab(label="Geographic Analysis", tab_id="tab-geo", children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("State-City Fraud Distribution"),
                                dbc.CardBody([
                                    dcc.Graph(id='treemap', config={'displayModeBar': False})
                                ])
                            ])
                        ], width=12)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Top 10 Postcodes with Highest Number of Frauds"),
                                dbc.CardBody([
                                    dcc.Graph(id='top-postcodes-bar', config={'displayModeBar': False})
                                ])
                            ])
                        ], width=12, className="mt-4")
                    ])
                ]),
                dbc.Tab(label="Channel Analysis", tab_id="tab-channel", children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Fraud Count by Channel"),
                                dbc.CardBody([
                                    dcc.Graph(id='channel-bar', config={'displayModeBar': False})
                                ])
                            ])
                        ], width=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("State-wise Distribution of Channels"),
                                dbc.CardBody([
                                    dcc.Graph(id='state-channel-bar', config={'displayModeBar': False})
                                ])
                            ])
                        ], width=6)
                    ])
                ]),
                dbc.Tab(label="Time Analysis", tab_id="tab-time", children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Days Between Policy Start and Death"),
                                dbc.CardBody([
                                    dcc.Graph(id='policy-death-hist', config={'displayModeBar': False})
                                ])
                            ])
                        ], width=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Intimation Delay Analysis"),
                                dbc.CardBody([
                                    dcc.Graph(id='intimation-delay-hist', config={'displayModeBar': False})
                                ])
                            ])
                        ], width=6)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Fraud Trend Over Time"),
                                dbc.CardBody([
                                    dcc.Graph(id='time-series-chart', config={'displayModeBar': False})
                                ])
                            ])
                        ], width=12, className="mt-4")
                    ])
                ]),
                dbc.Tab(label="Data Table", tab_id="tab-data", children=[
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.H5("Fraud Cases Data", className="d-inline"),
                                dbc.Button("Export CSV", id="export-csv", color="primary", size="sm", className="float-end"),
                                dbc.Button("Export Chart", id="export-chart", color="secondary", size="sm", className="float-end me-2")
                            ])
                        ]),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id='data-table',
                                page_size=15,
                                style_table={'overflowX': 'auto'},
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '8px',
                                    'minWidth': '100px',
                                    'width': '150px',
                                    'maxWidth': '300px',
                                    'whiteSpace': 'normal',
                                    'height': 'auto'
                                },
                                style_header={
                                    'backgroundColor': colors['light'],
                                    'fontWeight': 'bold'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgba(0, 0, 0, 0.05)'
                                    }
                                ],
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                export_format="csv"
                            )
                        ])
                    ])
                ])
            ], id="tabs", active_tab="tab-geo")
        ]),
        # Store the processed data in a dcc.Store
        dcc.Store(id='processed-data')
    ], fluid=True)
])

# Callback to parse uploaded data (unchanged but with improved error messages)
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
            df[col] = pd.to_datetime(df[col], errors='coerce')  # Convert to datetime, invalid values become NaT
        # Check for missing or invalid dates
        if df['Date of Death'].isna().any():
            print("Warning: Some 'Date of Death' values could not be converted to datetime.")
        # Calculate time differences
        df['Policy_to_Death_Days'] = (df['Date of Death'] - df['POLICYRISKCOMMENCEMENTDATE']).dt.days
        df['Death_to_Intimation_Days'] = (df['INTIMATIONDATE'] - df['Date of Death']).dt.days
        # Generate options for dropdown filters
        state_options = [{'label': state, 'value': state} for state in sorted(df['CORRESPONDENCESTATE'].dropna().unique())]
        channel_options = [{'label': channel, 'value': channel} for channel in sorted(df['CHANNEL'].dropna().unique())]
        # Success message
        success_message = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Successfully loaded data with {len(df)} records"
        ], color="success")
        # Convert DataFrame to dictionary for storage
        df_dict = df.to_dict('records')
        return [df_dict, success_message, state_options, channel_options, {"display": "block"}, None]
    except Exception as e:
        error_message = dbc.Alert([
            html.I(className="fas fa-exclamation-circle me-2"),
            f"Error processing file: {str(e)}"
        ], color="danger")
        return [None, error_message, [], [], {"display": "none"}, None]

# Callback to update KPI metrics (unchanged but with improved hover effects)
@app.callback(
    Output('kpi-metrics', 'children'),
    [Input('processed-data', 'data'),
     Input('apply-filters', 'n_clicks')],
    [State('state-filter', 'value'),
     State('channel-filter', 'value')],
    prevent_initial_call=True
)
def update_kpi_metrics(data, n_clicks, states, channels):
    if not data:
        return []
    # Convert back to DataFrame
    df = pd.DataFrame(data)
    # Apply filters if they are set
    filtered_df = df.copy()
    if states and len(states) > 0:
        filtered_df = filtered_df[filtered_df['CORRESPONDENCESTATE'].isin(states)]
    if channels and len(channels) > 0:
        filtered_df = filtered_df[filtered_df['CHANNEL'].isin(channels)]
    # Calculate KPIs
    total_cases = len(filtered_df)
    fraud_cases = filtered_df['Fraud Category'].notna().sum()
    fraud_rate = round((fraud_cases / total_cases) * 100, 2) if total_cases > 0 else 0
    avg_policy_to_death = round(filtered_df['Policy_to_Death_Days'].mean(), 1)
    avg_intimation_delay = round(filtered_df['Death_to_Intimation_Days'].mean(), 1)
    # Return KPI cards
    return [
        dbc.Col([
            create_kpi_card("Total Cases", f"{total_cases:,}", colors['primary'], "fas fa-file-alt")
        ], width=3),
        dbc.Col([
            create_kpi_card("Fraud Cases", f"{fraud_cases:,}", colors['danger'], "fas fa-exclamation-triangle")
        ], width=3),
        dbc.Col([
            create_kpi_card("Fraud Rate", f"{fraud_rate}%", colors['warning'], "fas fa-percent", comparison=5.2)
        ], width=3),
        dbc.Col([
            create_kpi_card("Avg. Days to Death", f"{avg_policy_to_death}", colors['info'], "fas fa-calendar-alt")
        ], width=3)
    ]

# Callback to update all charts (unchanged but with improved hover effects)
@app.callback(
    [Output('treemap', 'figure'),
     Output('channel-bar', 'figure'),
     Output('policy-death-hist', 'figure'),
     Output('state-channel-bar', 'figure'),
     Output('top-postcodes-bar', 'figure'),
     Output('intimation-delay-hist', 'figure'),
     Output('time-series-chart', 'figure'),
     Output('data-table', 'data'),
     Output('data-table', 'columns')],
    [Input('processed-data', 'data'),
     Input('apply-filters', 'n_clicks')],
    [State('state-filter', 'value'),
     State('channel-filter', 'value')],
    prevent_initial_call=True
)
def update_all_visualizations(data, n_clicks, states, channels):
    print("Callback triggered. n_clicks:", n_clicks)
    if not data:
        # Return empty figures if no data
        empty_fig = px.scatter(title="No data available")
        return [empty_fig] * 7 + [[], []]
    # Convert back to DataFrame
    df = pd.DataFrame(data)
    # Ensure 'Date of Death' is datetime
    df['Date of Death'] = pd.to_datetime(df['Date of Death'], errors='coerce')
    # Debugging: Print the filter values
    print("Selected States:", states)
    print("Selected Channels:", channels)
    # Apply filters if they are set
    filtered_df = df.copy()
    if states and len(states) > 0:
        filtered_df = filtered_df[filtered_df['CORRESPONDENCESTATE'].isin(states)]
    if channels and len(channels) > 0:
        filtered_df = filtered_df[filtered_df['CHANNEL'].isin(channels)]
    # Debugging: Print the filtered DataFrame
    print("Filtered DataFrame After Applying Filters:")
    print(filtered_df.head())
    # Check if filtered DataFrame is empty
    if filtered_df.empty:
        empty_fig = px.scatter(title="No data available")
        return [empty_fig] * 7 + [[], []]
    # Generate figures using the filtered DataFrame
    # Figure 1: Treemap for State-City Fraud Distribution
    fig1 = px.treemap(
        filtered_df.groupby(['CORRESPONDENCESTATE', 'CORRESPONDENCECITY']).size().reset_index(name='Count'),
        path=['CORRESPONDENCESTATE', 'CORRESPONDENCECITY'],
        values='Count',
        color='Count',
        color_continuous_scale='Viridis',
        hover_data={'Count': True}
    )
    # Figure 2: Bar chart for Fraud Count by Channel
    fig2 = px.bar(
        filtered_df.groupby('CHANNEL').size().reset_index(name='Count'),
        x='CHANNEL',
        y='Count',
        color='CHANNEL',
        title="Fraud Count by Channel"
    )
    # Figure 3: Histogram for Days Between Policy Start and Death
    fig3 = px.histogram(
        filtered_df,
        x='Policy_to_Death_Days',
        nbins=20,
        title="Days Between Policy Start and Death",
        labels={'Policy_to_Death_Days': 'Days'}
    )
    # Figure 4: Bar chart for State-wise Distribution of Channels
    fig4 = px.bar(
        filtered_df.groupby(['CORRESPONDENCESTATE', 'CHANNEL']).size().reset_index(name='Count'),
        x='CORRESPONDENCESTATE',
        y='Count',
        color='CHANNEL',
        title="State-wise Distribution of Channels"
    )
    # Combine Postcode and City for better labels
    filtered_df['Postcode_City'] = filtered_df['CORRESPONDENCEPOSTCODE'].astype(str) + " (" + filtered_df['CORRESPONDENCECITY'] + ")"
    # Figure 5: Bar chart for Top 10 Postcodes with Highest Number of Frauds
    fig5 = px.bar(
        filtered_df.groupby('Postcode_City').size().reset_index(name='Count').nlargest(10, 'Count'),
        x='Postcode_City',
        y='Count',
        title="Top 10 Postcodes with Highest Number of Frauds",
        labels={'Postcode_City': 'Postcode (City)', 'Count': 'Number of Cases'}
    )
    # Figure 6: Histogram for Intimation Delay Analysis
    fig6 = px.histogram(
        filtered_df,
        x='Death_to_Intimation_Days',
        nbins=20,
        title="Intimation Delay Analysis",
        labels={'Death_to_Intimation_Days': 'Days'}
    )
    # Figure 7: Fraud Trend Over Time
    filtered_df['Death_Month'] = filtered_df['Date of Death'].dt.to_period('M')
    time_series_df = filtered_df.groupby(['Death_Month']).agg(
        Total_Claims=('Dummy Policy No', 'count'),
        Fraud_Claims=('Fraud Category', lambda x: x.notna().sum())
    ).reset_index()
    time_series_df['Death_Month'] = time_series_df['Death_Month'].astype(str)
    time_series_df['Fraud_Rate'] = (time_series_df['Fraud_Claims'] / time_series_df['Total_Claims']) * 100
    fig7 = make_subplots(specs=[[{"secondary_y": True}]])
    fig7.add_trace(
        go.Bar(
            x=time_series_df['Death_Month'],
            y=time_series_df['Total_Claims'],
            name="Total Claims",
            marker_color=colors['primary']
        ),
        secondary_y=False
    )
    fig7.add_trace(
        go.Scatter(
            x=time_series_df['Death_Month'],
            y=time_series_df['Fraud_Rate'],
            name="Fraud Rate (%)",
            mode="lines+markers",
            line=dict(color=colors['danger'], width=3),
            marker=dict(size=8)
        ),
        secondary_y=True
    )
    fig7.update_layout(
        xaxis_title="Month",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    fig7.update_yaxes(
        title_text="Number of Claims",
        secondary_y=False,
        gridcolor='rgba(0,0,0,0.1)'
    )
    fig7.update_yaxes(
        title_text="Fraud Rate (%)",
        secondary_y=True,
        gridcolor='rgba(0,0,0,0.1)'
    )
    # Data table
    columns = [
        {"name": "Policy Number", "id": "Dummy Policy No"},
        {"name": "State", "id": "CORRESPONDENCESTATE"},
        {"name": "City", "id": "CORRESPONDENCECITY"},
        {"name": "Postcode", "id": "CORRESPONDENCEPOSTCODE"},
        {"name": "Channel", "id": "CHANNEL"},
        {"name": "Policy Start", "id": "POLICYRISKCOMMENCEMENTDATE"},
        {"name": "Death Date", "id": "Date of Death"},
        {"name": "Intimation Date", "id": "INTIMATIONDATE"},
        {"name": "Policy to Death Days", "id": "Policy_to_Death_Days"},
        {"name": "Fraud Category", "id": "Fraud Category"}
    ]
    # Create a copy of filtered_df for the data table
    table_df = filtered_df.copy()
    # Format dates for table display
    for date_col in ['POLICYRISKCOMMENCEMENTDATE', 'Date of Death', 'INTIMATIONDATE']:
        table_df[date_col] = pd.to_datetime(table_df[date_col], errors='coerce')
        table_df[date_col] = table_df[date_col].dt.strftime('%Y-%m-%d')
    # Select only necessary columns for table display
    table_data = table_df[[col['id'] for col in columns]].to_dict('records')
    return fig1, fig2, fig3, fig4, fig5, fig6, fig7, table_data, columns

# Run the app
if __name__ == '__main__':
    app.run(debug=True)