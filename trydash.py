import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import base64
import io

# Initialize the Dash app with Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Fraud Analysis Dashboard"

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

# Navbar component
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.I(className="fas fa-shield-alt me-2"), width="auto"),
                        dbc.Col(dbc.NavbarBrand("Fraud Analysis Dashboard", className="ms-2")),
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
                        dbc.NavItem(dbc.NavLink("Dashboard", href="#")),
                        dbc.NavItem(dbc.NavLink("Documentation", href="#")),
                        dbc.NavItem(dbc.NavLink("About", href="#")),
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
    className="mb-4",
)

# File upload component
upload_card = dbc.Card(
    [
        dbc.CardHeader("Data Source"),
        dbc.CardBody(
            [
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        html.I(className="fas fa-file-excel me-2"),
                        'Drag and Drop or ',
                        html.A('Select Excel File (.xlsx)', className="text-primary")
                    ]),
                    style={
                        'width': '100%', 
                        'height': '60px', 
                        'lineHeight': '60px',
                        'borderWidth': '1px', 
                        'borderStyle': 'dashed', 
                        'borderRadius': '5px',
                        'textAlign': 'center'
                    },
                    multiple=False
                ),
                html.Div(id="upload-status", className="mt-2")
            ]
        ),
    ],
    className="mb-4"
)

# Filters component
filters_card = dbc.Card(
    [
        dbc.CardHeader("Filters"),
        dbc.CardBody(
            [
                dbc.Row([
                    dbc.Col([
                        html.Label("State:"),
                        dcc.Dropdown(id="state-filter", multi=True, placeholder="Select state(s)..."),
                    ], width=4),
                    dbc.Col([
                        html.Label("City:"),
                        dcc.Dropdown(id="city-filter", multi=True, placeholder="Select city(s)..."),
                    ], width=4),
                    dbc.Col([
                        html.Label("Age Range:"),
                        dcc.RangeSlider(
                            id='age-range-slider',
                            min=0,
                            max=100,
                            step=1,
                            value=[0, 100],
                            marks={i: str(i) for i in range(0, 101, 10)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], width=4)
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Apply Filters", id="apply-filters", color="primary", className="mt-3")
                    ], width=12, className="text-center")
                ])
            ]
        )
    ],
    className="mb-4"
)

# Layout
app.layout = html.Div([
    navbar,
    dbc.Container([
        dbc.Row([
            dbc.Col(upload_card, width=12)
        ]),
        dbc.Spinner(
            html.Div(id="loading-output"),
            color="primary",
            spinner_style={"width": "3rem", "height": "3rem"}
        ),
        html.Div(id="dashboard-content", style={"display": "none"}, children=[
            dbc.Row([
                dbc.Col(filters_card, width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='state-bar')
                ], width=6),
                dbc.Col([
                    dcc.Graph(id='channel-bar')
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='time-series')
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='histogram-policy-death')
                ], width=6),
                dbc.Col([
                    dcc.Graph(id='histogram-death-intimation')
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='fraud-hotspots')
                ], width=6),
                dbc.Col([
                    dcc.Graph(id='relationship-analysis')
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='channel-distribution')
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='treemap')
                ], width=6),
                dbc.Col([
                    dcc.Graph(id='radar-chart')
                ], width=6)
            ])
        ]),
        dcc.Store(id='processed-data')
    ], fluid=True)
])

# Callback to parse uploaded data
@app.callback(
    [Output('processed-data', 'data'),
     Output('upload-status', 'children'),
     Output('state-filter', 'options'),
     Output('city-filter', 'options'),
     Output('age-range-slider', 'min'),
     Output('age-range-slider', 'max'),
     Output('age-range-slider', 'value'),
     Output('dashboard-content', 'style')],
    Input('upload-data', 'contents'),
    prevent_initial_call=True
)
def parse_contents(contents):
    if contents is None:
        return [None, None, [], [], 0, 100, [0, 100], {"display": "none"}]
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))
        
        # Preprocess date columns
        df['POLICYRISKCOMMENCEMENTDATE'] = pd.to_datetime(df['POLICYRISKCOMMENCEMENTDATE'], errors='coerce')
        df['Date of Death'] = pd.to_datetime(df['Date of Death'], errors='coerce')
        df['INTIMATIONDATE'] = pd.to_datetime(df['INTIMATIONDATE'], errors='coerce')
        
        # Calculate time differences
        df['Policy_to_Death_Days'] = (df['Date of Death'] - df['POLICYRISKCOMMENCEMENTDATE']).dt.days
        df['Death_to_Intimation_Days'] = (df['INTIMATIONDATE'] - df['Date of Death']).dt.days
        
        # Generate options for dropdown filters
        state_options = [{'label': state, 'value': state} for state in sorted(df['CORRESPONDENCESTATE'].dropna().unique())]
        city_options = [{'label': city, 'value': city} for city in sorted(df['CORRESPONDENCECITY'].dropna().unique())]
        
        # Age range settings
        min_age = 0
        max_age = 100
        age_range = [min_age, max_age]
        
        # Success message
        success_message = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Successfully loaded data with {len(df)} records"
        ], color="success")
        
        # Convert DataFrame to dictionary for storage
        df_dict = df.to_dict('records')
        return [df_dict, success_message, state_options, city_options, min_age, max_age, age_range, {"display": "block"}]
    except Exception as e:
        error_message = dbc.Alert([
            html.I(className="fas fa-exclamation-circle me-2"),
            f"Error processing file: {str(e)}"
        ], color="danger")
        return [None, error_message, [], [], 0, 100, [0, 100], {"display": "none"}]

# Callback to apply filters and update graphs
@app.callback(
    [Output('state-bar', 'figure'),
     Output('channel-bar', 'figure'),
     Output('time-series', 'figure'),
     Output('histogram-policy-death', 'figure'),
     Output('histogram-death-intimation', 'figure'),
     Output('fraud-hotspots', 'figure'),
     Output('relationship-analysis', 'figure'),
     Output('channel-distribution', 'figure'),
     Output('treemap', 'figure'),
     Output('radar-chart', 'figure')],
    [Input('apply-filters', 'n_clicks')],
    [State('processed-data', 'data'),
     State('state-filter', 'value'),
     State('city-filter', 'value'),
     State('age-range-slider', 'value')],
    prevent_initial_call=True
)
def update_graphs(n_clicks, data, states, cities, age_range):
    if not data:
        empty_fig = px.scatter(title="No data available")
        return [empty_fig] * 10
    
    # Convert back to DataFrame
    df = pd.DataFrame(data)
    
    # Apply filters if they are set
    filtered_df = df.copy()
    if states and len(states) > 0:
        filtered_df = filtered_df[filtered_df['CORRESPONDENCESTATE'].isin(states)]
    if cities and len(cities) > 0:
        filtered_df = filtered_df[filtered_df['CORRESPONDENCECITY'].isin(cities)]
    if age_range:
        filtered_df = filtered_df[(filtered_df['AGE'] >= age_range[0]) & (filtered_df['AGE'] <= age_range[1])]
    
    # Generate all graphs
    state_counts = filtered_df['CORRESPONDENCESTATE'].value_counts().nlargest(10)
    state_bar = px.bar(x=state_counts.values, y=state_counts.index,
                       orientation='h', title='Top 10 States with Highest Fraud Cases')

    channel_counts = filtered_df['CHANNEL'].value_counts()
    channel_bar = px.bar(x=channel_counts.index, y=channel_counts.values, title='Fraud Count by Channel')

    time_series = filtered_df.groupby('Month_Year').size().reset_index(name='Count')
    time_series['Month_Year'] = pd.to_datetime(time_series['Month_Year'])
    time_series = time_series.sort_values('Month_Year')
    time_chart = px.line(time_series, x='Month_Year', y='Count', title='Monthly Trend of Fraud Cases')

    hist_policy = px.histogram(filtered_df, x='Policy_to_Death_Days', nbins=30,
                               title='Days Between Policy Start and Death')
    hist_death = px.histogram(filtered_df, x='Death_to_Intimation_Days', nbins=30,
                              title='Days Between Death and Intimation')

    fraud_data = filtered_df[filtered_df['Fraud Category'].notna()]
    fraud_counts = fraud_data.groupby(['CORRESPONDENCEPOSTCODE', 'CORRESPONDENCECITY']).size().reset_index(name='Fraud_Count')
    fraud_counts['Location'] = fraud_counts['CORRESPONDENCECITY'] + ' (' + fraud_counts['CORRESPONDENCEPOSTCODE'].astype(str) + ')'
    top_frauds = fraud_counts.nlargest(10, 'Fraud_Count')
    hotspot_chart = px.bar(top_frauds, x='Fraud_Count', y='Location', orientation='h', title='Top 10 Fraud Hotspots')

    scatter_df = filtered_df.dropna(subset=['Policy_to_Death_Days', 'Death_to_Intimation_Days', 'CHANNEL'])
    relationship_chart = px.scatter(scatter_df, x='Policy_to_Death_Days', y='Death_to_Intimation_Days',
                                    color='CHANNEL', title='Policy-to-Death vs Death-to-Intimation by Channel')

    state_channel = filtered_df.groupby(['CORRESPONDENCESTATE', 'CHANNEL']).size().reset_index(name='Count')
    pivot_data = state_channel.pivot(index='CORRESPONDENCESTATE', columns='CHANNEL', values='Count').fillna(0)
    top_states = pivot_data.sum(axis=1).nlargest(10).index
    stacked_data = pivot_data.loc[top_states]
    channel_dist = px.bar(stacked_data, title='Channel Distribution in Top 10 States', barmode='stack')

    geo_data = filtered_df.groupby('CORRESPONDENCESTATE').size().reset_index(name='Count')
    treemap = px.treemap(geo_data, path=['CORRESPONDENCESTATE'], values='Count',
                         title='Geographical Distribution of Fraud Cases')

    radar_data = filtered_df.groupby('CHANNEL').agg(
        Avg_Policy_to_Death=('Policy_to_Death_Days', 'mean'),
        Avg_Death_to_Intimation=('Death_to_Intimation_Days', 'mean'),
        Count=('CHANNEL', 'size')
    ).reset_index()
    for col in ['Avg_Policy_to_Death', 'Avg_Death_to_Intimation', 'Count']:
        max_val = radar_data[col].max()
        min_val = radar_data[col].min()
        radar_data[f'{col}_Normalized'] = (radar_data[col] - min_val) / (max_val - min_val)

    top_channels = radar_data.nlargest(5, 'Count')
    fig_radar = go.Figure()
    categories = ['Avg_Policy_to_Death_Normalized', 'Avg_Death_to_Intimation_Normalized', 'Count_Normalized']
    labels = ['Policy to Death', 'Death to Intimation', 'Count']
    angles = list(np.linspace(0, 2 * np.pi, len(categories), endpoint=False)) + [0]

    for _, row in top_channels.iterrows():
        values = [row[col] for col in categories] + [row[categories[0]]]
        fig_radar.add_trace(go.Scatterpolar(r=values, theta=labels + [labels[0]],
                                            fill='toself', name=row['CHANNEL']))
    fig_radar.update_layout(title='Radar Chart of Top 5 Channels', polar=dict(radialaxis=dict(visible=True)), showlegend=True)

    return state_bar, channel_bar, time_chart, hist_policy, hist_death, hotspot_chart, relationship_chart, channel_dist, treemap, fig_radar

# Run the app
if __name__ == '__main__':
    app.run(debug=True)