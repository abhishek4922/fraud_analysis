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
                external_stylesheets=[dbc.themes.FLATLY],
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
    'dark': '#95A5A6',
    'background': '#F8F9FA'
}

# Custom CSS for additional styling
custom_css = {
    'card-header': {
        'fontWeight': '600',
        'backgroundColor': colors['light'],
        'borderBottom': f'1px solid {colors["dark"]}'
    },
    'filter-card': {
        'boxShadow': '0 4px 6px rgba(0,0,0,0.1)',
        'borderRadius': '8px'
    },
    'upload-area': {
        'width': '100%', 
        'height': '120px', 
        'lineHeight': '120px',
        'borderWidth': '2px', 
        'borderStyle': 'dashed', 
        'borderRadius': '12px',
        'textAlign': 'center',
        'cursor': 'pointer',
        'transition': 'all 0.3s',
        'backgroundColor': 'white'
    },
    'upload-area-hover': {
        'borderColor': colors['info'],
        'backgroundColor': 'rgba(52, 152, 219, 0.05)'
    },
    'kpi-card': {
        'borderRadius': '10px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',
        'transition': 'transform 0.2s',
        'height': '100%'
    },
    'kpi-card-hover': {
        'transform': 'translateY(-5px)',
        'boxShadow': '0 6px 12px rgba(0,0,0,0.1)'
    }
}

# Nav bar component with improved styling
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.I(className="fas fa-shield-alt fa-2x me-2"), width="auto"),
                        dbc.Col(dbc.NavbarBrand("Insurance Fraud Analytics", className="ms-2", style={'fontSize': '24px'})),
                    ],
                    align="center",
                    className="g-0"
                ),
                href="#",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Dashboard", href="#", className="px-3")),
                        dbc.NavItem(dbc.NavLink("Documentation", href="#", className="px-3")),
                        dbc.NavItem(dbc.NavLink("About", href="#", className="px-3")),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ],
        fluid=True
    ),
    color="primary",
    dark=True,
    className="mb-4 shadow",
    style={'padding': '0.5rem 1rem'}
)

# File upload component with improved design
upload_card = dbc.Card(
    [
        dbc.CardHeader("Upload Data", className="py-3", style=custom_css['card-header']),
        dbc.CardBody(
            [
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-3x mb-3", style={'color': colors['info']}),
                            html.H5("Drag and Drop Excel File Here", className="mb-1"),
                            html.P("or click to browse files", className="text-muted mb-0"),
                            html.Small("Supports .xlsx files only", className="text-muted")
                        ], style={'padding': '20px'})
                    ]),
                    style=custom_css['upload-area'],
                    multiple=False
                ),
                html.Div(id="upload-status", className="mt-3")
            ],
            className="py-4"
        ),
    ],
    className="mb-4 shadow",
    style=custom_css['filter-card']
)

# Filters component with improved layout
filters_card = dbc.Card(
    [
        dbc.CardHeader("Data Filters", className="py-3", style=custom_css['card-header']),
        dbc.CardBody(
            [
                dbc.Row([
                    dbc.Col([
                        html.Label("State:", className="form-label fw-bold"),
                        dcc.Dropdown(
                            id="state-filter", 
                            multi=True, 
                            placeholder="Select state(s)...",
                            className="mb-3"
                        )
                    ], md=6),
                    dbc.Col([
                        html.Label("Channel:", className="form-label fw-bold"),
                        dcc.Dropdown(
                            id="channel-filter", 
                            multi=True, 
                            placeholder="Select channel(s)...",
                            className="mb-3"
                        )
                    ], md=6)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Apply Filters", 
                            id="apply-filters", 
                            color="primary", 
                            className="w-100 py-2",
                            style={'fontWeight': '600'}
                        )
                    ], width=12)
                ])
            ],
            className="py-3"
        )
    ],
    className="mb-4 shadow",
    style=custom_css['filter-card']
)

# Enhanced KPI metrics component
def create_kpi_card(title, value, color, icon, comparison=None):
    comparison_element = html.Div([
        html.I(className=f"fas fa-arrow-{'up' if comparison > 0 else 'down'} me-1"),
        f"{abs(comparison)}% from previous period"
    ], className=f"text-{'success' if comparison > 0 else 'danger'} small mt-1") if comparison is not None else None
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.Span(title, className="text-uppercase small text-muted fw-bold"),
                    html.Div([
                        html.I(className=f"{icon} me-2", style={"color": color}),
                        html.Span(value, className="h3 mb-0")
                    ], className="d-flex align-items-center mt-2 mb-1"),
                    comparison_element
                ], className="p-3")
            ])
        ], className="p-0"),
        className="mb-4 shadow-sm border-0",
        style={**custom_css['kpi-card'], 'borderLeft': f'4px solid {color}'},
        id=f"kpi-{title.replace(' ', '-').lower()}"
    )

# Create a layout with improved tabs
app.layout = html.Div(
    style={'backgroundColor': colors['background'], 'minHeight': '100vh'},
    children=[
    navbar,
    dbc.Container(fluid=True, children=[
        dbc.Row([
            dbc.Col([
                upload_card
            ], lg=12)
        ]),
        # Loading spinner
        dbc.Spinner(
            html.Div(id="loading-output"),
            color="primary",
            spinner_style={"width": "3rem", "height": "3rem"},
            fullscreen=True,
            spinnerClassName="mt-5"
        ),
        html.Div(id="dashboard-content", style={"display": "none"}, children=[
            # Filters section
            dbc.Row([
                dbc.Col([
                    filters_card
                ], lg=12)
            ]),
            # KPI metrics
            dbc.Row(id="kpi-metrics", className="g-4 mb-4"),
            # Tabs for different visualization groups
            dbc.Tabs([
                dbc.Tab(
                    label=html.Span([
                        html.I(className="fas fa-map-marked-alt me-2"),
                        "Geographic Analysis"
                    ], style={"display": "flex", "alignItems": "center"}),
                    tab_id="tab-geo", 
                    tabClassName="fw-bold",
                    children=[
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-map me-2"),
                                        "State-City Fraud Distribution"
                                    ], style=custom_css['card-header']),
                                    dbc.CardBody([
                                        dcc.Graph(id='treemap', config={'displayModeBar': False})
                                    ], className="p-3")
                                ], className="shadow-sm h-100")
                            ], lg=12, className="mb-4")
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-list-ol me-2"),
                                        "Top 10 Postcodes with Highest Number of Frauds"
                                    ], style=custom_css['card-header']),
                                    dbc.CardBody([
                                        dcc.Graph(id='top-postcodes-bar', config={'displayModeBar': False})
                                    ], className="p-3")
                                ], className="shadow-sm h-100")
                            ], lg=12, className="mb-4")
                        ])
                    ]
                ),
                dbc.Tab(
                    label=html.Span([
                        html.I(className="fas fa-random me-2"),
                        "Channel Analysis"
                    ], style={"display": "flex", "alignItems": "center"}),
                    tab_id="tab-channel",
                    tabClassName="fw-bold",
                    children=[
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-chart-bar me-2"),
                                        "Fraud Count by Channel"
                                    ], style=custom_css['card-header']),
                                    dbc.CardBody([
                                        dcc.Graph(id='channel-bar', config={'displayModeBar': False})
                                    ], className="p-3")
                                ], className="shadow-sm h-100")
                            ], lg=6, className="mb-4"),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-exchange-alt me-2"),
                                        "State-wise Distribution of Channels"
                                    ], style=custom_css['card-header']),
                                    dbc.CardBody([
                                        dcc.Graph(id='state-channel-bar', config={'displayModeBar': False})
                                    ], className="p-3")
                                ], className="shadow-sm h-100")
                            ], lg=6, className="mb-4")
                        ])
                    ]
                ),
                dbc.Tab(
                    label=html.Span([
                        html.I(className="fas fa-clock me-2"),
                        "Time Analysis"
                    ], style={"display": "flex", "alignItems": "center"}),
                    tab_id="tab-time",
                    tabClassName="fw-bold",
                    children=[
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-hourglass-half me-2"),
                                        "Days Between Policy Start and Death"
                                    ], style=custom_css['card-header']),
                                    dbc.CardBody([
                                        dcc.Graph(id='policy-death-hist', config={'displayModeBar': False})
                                    ], className="p-3")
                                ], className="shadow-sm h-100")
                            ], lg=6, className="mb-4"),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-calendar-times me-2"),
                                        "Intimation Delay Analysis"
                                    ], style=custom_css['card-header']),
                                    dbc.CardBody([
                                        dcc.Graph(id='intimation-delay-hist', config={'displayModeBar': False})
                                    ], className="p-3")
                                ], className="shadow-sm h-100")
                            ], lg=6, className="mb-4")
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-chart-line me-2"),
                                        "Fraud Trend Over Time"
                                    ], style=custom_css['card-header']),
                                    dbc.CardBody([
                                        dcc.Graph(id='time-series-chart', config={'displayModeBar': False})
                                    ], className="p-3")
                                ], className="shadow-sm h-100")
                            ], lg=12, className="mb-4")
                        ])
                    ]
                ),
                dbc.Tab(
                    label=html.Span([
                        html.I(className="fas fa-table me-2"),
                        "Data Table"
                    ], style={"display": "flex", "alignItems": "center"}),
                    tab_id="tab-data",
                    tabClassName="fw-bold",
                    children=[
                        dbc.Card([
                            dbc.CardHeader([
                                html.Div([
                                    html.I(className="fas fa-database me-2"),
                                    html.H5("Fraud Cases Data", className="d-inline-block mb-0"),
                                    dbc.Button(
                                        "Export CSV", 
                                        id="export-csv", 
                                        color="primary", 
                                        size="sm", 
                                        className="float-end",
                                        style={'fontWeight': '600'}
                                    )
                                ])
                            ], style=custom_css['card-header']),
                            dbc.CardBody([
                                dash_table.DataTable(
                                    id='data-table',
                                    page_size=15,
                                    style_table={
                                        'overflowX': 'auto',
                                        'borderRadius': '8px',
                                        'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
                                    },
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '12px',
                                        'minWidth': '100px',
                                        'width': '150px',
                                        'maxWidth': '300px',
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'border': '1px solid rgba(0,0,0,0.05)'
                                    },
                                    style_header={
                                        'backgroundColor': colors['light'],
                                        'fontWeight': 'bold',
                                        'borderBottom': f'2px solid {colors["dark"]}'
                                    },
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': 'rgba(0, 0, 0, 0.03)'
                                        }
                                    ],
                                    filter_action="native",
                                    sort_action="native",
                                    sort_mode="multi",
                                    export_format="csv"
                                )
                            ], className="p-3")
                        ], className="shadow-sm")
                    ]
                )
            ], 
            id="tabs", 
            active_tab="tab-geo",
            className="mb-4"
            )
        ]),
        # Store the processed data in a dcc.Store
        dcc.Store(id='processed-data')
    ]),
    # Footer
    html.Footer(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.P("Insurance Fraud Analytics Dashboard", className="text-muted mb-0"),
                    html.Small("© 2023 All Rights Reserved", className="text-muted")
                ], className="text-center py-3")
            ])
        ], fluid=True),
        className="mt-auto bg-light border-top"
    )
])

# Add hover effects using clientside callbacks
app.clientside_callback(
    """
    function(hover, cardId) {
        var element = document.getElementById(cardId);
        if (element) {
            if (hover) {
                element.style.transform = 'translateY(-5px)';
                element.style.boxShadow = '0 6px 12px rgba(0,0,0,0.1)';
            } else {
                element.style.transform = '';
                element.style.boxShadow = '0 2px 4px rgba(0,0,0,0.05)';
            }
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('dummy-output', 'children'),
    [Input('kpi-total-cases', 'n_clicks_timestamp'),
     Input('kpi-fraud-cases', 'n_clicks_timestamp'),
     Input('kpi-fraud-rate', 'n_clicks_timestamp'),
     Input('kpi-avg-days-to-death', 'n_clicks_timestamp')],
    [State('kpi-total-cases', 'id'),
     State('kpi-fraud-cases', 'id'),
     State('kpi-fraud-rate', 'id'),
     State('kpi-avg-days-to-death', 'id')]
)

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
        ], color="success", className="d-flex align-items-center")
        # Convert DataFrame to dictionary for storage
        df_dict = df.to_dict('records')
        return [df_dict, success_message, state_options, channel_options, {"display": "block"}, None]
    except Exception as e:
        error_message = dbc.Alert([
            html.I(className="fas fa-exclamation-circle me-2"),
            f"Error processing file: {str(e)}"
        ], color="danger", className="d-flex align-items-center")
        return [None, error_message, [], [], {"display": "none"}, None]

# Callback to update KPI metrics
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
            create_kpi_card("Total Cases", f"{total_cases:,}", colors['primary'], "fas fa-file-alt", id="kpi-total-cases")
        ], xs=12, sm=6, lg=3),
        dbc.Col([
            create_kpi_card("Fraud Cases", f"{fraud_cases:,}", colors['danger'], "fas fa-exclamation-triangle", id="kpi-fraud-cases")
        ], xs=12, sm=6, lg=3),
        dbc.Col([
            create_kpi_card("Fraud Rate", f"{fraud_rate}%", colors['warning'], "fas fa-percent", comparison=5.2, id="kpi-fraud-rate")
        ], xs=12, sm=6, lg=3),
        dbc.Col([
            create_kpi_card("Avg. Days to Death", f"{avg_policy_to_death}", colors['info'], "fas fa-calendar-alt", id="kpi-avg-days-to-death")
        ], xs=12, sm=6, lg=3)
    ]

# Callback to update all charts
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
    if not data:
        # Return empty figures if no data
        empty_fig = px.scatter(title="No data available")
        return [empty_fig] * 7 + [[], []]
    # Convert back to DataFrame
    df = pd.DataFrame(data)
    # Ensure 'Date of Death' is datetime
    df['Date of Death'] = pd.to_datetime(df['Date of Death'], errors='coerce')
    # Apply filters if they are set
    filtered_df = df.copy()
    if states and len(states) > 0:
        filtered_df = filtered_df[filtered_df['CORRESPONDENCESTATE'].isin(states)]
    if channels and len(channels) > 0:
        filtered_df = filtered_df[filtered_df['CHANNEL'].isin(channels)]
    # Filter out rows with invalid 'Date of Death'
    filtered_df = filtered_df[filtered_df['Date of Death'].notna()]
    # Check if filtered DataFrame is empty
    if filtered_df.empty:
        empty_fig = px.scatter(title="No data available")
        return [empty_fig] * 7 + [[], []]
    # Ensure 'Date of Death' is datetime before using .dt
    filtered_df['Death_Month'] = filtered_df['Date of Death'].dt.to_period('M')
    # Plot 1: Enhanced Treemap
    treemap_df = filtered_df.groupby(['CORRESPONDENCESTATE', 'CORRESPONDENCECITY']).size().reset_index(name='Count')
    fig1 = px.treemap(
        treemap_df,
        path=['CORRESPONDENCESTATE', 'CORRESPONDENCECITY'],
        values='Count',
        color='Count',
        color_continuous_scale='Viridis',
        hover_data={'Count': True}
    )
    fig1.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        coloraxis_showscale=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    # Plot 2: Enhanced Channel Bar
    channel_df = filtered_df.groupby('CHANNEL').size().reset_index(name='Count')
    channel_df = channel_df.sort_values(by='Count', ascending=False)
    fig2 = px.bar(
        channel_df,
        x='CHANNEL',
        y='Count',
        color='Count',
        color_continuous_scale='Viridis',
        text='Count'
    )
    fig2.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig2.update_layout(
        xaxis_title="Distribution Channel",
        yaxis_title="Number of Cases",
        xaxis={'categoryorder': 'total descending'},
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    # Plot 3: Enhanced Policy to Death Histogram
    fig3 = px.histogram(
        filtered_df,
        x='Policy_to_Death_Days',
        nbins=30,
        color_discrete_sequence=[colors['info']],
        marginal='box'
    )
    fig3.update_layout(
        xaxis_title="Days Between Policy Start and Death",
        yaxis_title="Frequency",
        bargap=0.05,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)')
    )
    # Plot 4: Enhanced State-Channel Distribution
    state_channel_df = filtered_df.groupby(['CORRESPONDENCESTATE', 'CHANNEL']).size().reset_index(name='Count')
    top_states = state_channel_df.groupby('CORRESPONDENCESTATE')['Count'].sum().nlargest(10).index.tolist()
    state_channel_df = state_channel_df[state_channel_df['CORRESPONDENCESTATE'].isin(top_states)]
    fig4 = px.bar(
        state_channel_df,
        x='CORRESPONDENCESTATE',
        y='Count',
        color='CHANNEL',
        barmode='group',
        text='Count'
    )
    fig4.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig4.update_layout(
        xaxis_title="State",
        yaxis_title="Number of Cases",
        legend_title="Channel",
        xaxis={'categoryorder': 'total descending', 'tickangle': -45},
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    # Plot 5: Enhanced Top Postcodes with Fraud
    fraud_df = filtered_df[filtered_df['Fraud Category'].notna()]
    fraud_counts = fraud_df.groupby(['CORRESPONDENCEPOSTCODE', 'CORRESPONDENCECITY']).size().reset_index(name='Fraud Count')
    top_frauds = fraud_counts.sort_values(by='Fraud Count', ascending=False).head(10)
    top_frauds['Postcode + City'] = top_frauds['CORRESPONDENCEPOSTCODE'].astype(str) + ' - ' + top_frauds['CORRESPONDENCECITY']
    fig5 = px.bar(
        top_frauds,
        x='Postcode + City',
        y='Fraud Count',
        text='Fraud Count',
        color='CORRESPONDENCECITY',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig5.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig5.update_layout(
        xaxis_title="Postcode - City",
        yaxis_title="Number of Fraud Cases",
        xaxis_tickangle=-45,
        showlegend=False,
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    # Plot 6: Intimation Delay Histogram
    fig6 = px.histogram(
        filtered_df,
        x='Death_to_Intimation_Days',
        nbins=30,
        color_discrete_sequence=[colors['warning']],
        marginal='box'
    )
    fig6.update_layout(
        xaxis_title="Days Between Death and Claim Intimation",
        yaxis_title="Frequency",
        bargap=0.05,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)')
    )
    # Plot 7: Fraud Trend Over Time
    filtered_df['Death_Month'] = filtered_df['Date of Death'].dt.to_period('M')
    time_series_df = filtered_df.groupby(['Death_Month']).agg(
        Total_Claims=('Dummy Policy No', 'count'),  # Updated column name
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
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
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
        {"name": "Policy Number", "id": "Dummy Policy No"},  # Updated column name
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
        # Ensure the column is in datetime format
        table_df[date_col] = pd.to_datetime(table_df[date_col], errors='coerce')
        # Format the datetime column to string
        table_df[date_col] = table_df[date_col].dt.strftime('%Y-%m-%d')
    # Select only necessary columns for table display
    table_data = table_df[[col['id'] for col in columns]].to_dict('records')
    return fig1, fig2, fig3, fig4, fig5, fig6, fig7, table_data, columns

# Run the app
if __name__ == '__main__':
    app.run(debug=True)