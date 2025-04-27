import dash
from dash import dcc, html, Input, Output, callback, no_update, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from datetime import datetime as dt
import base64
import io

# Initialize app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Insurance Fraud Analytics Dashboard"

# Custom colors
colors = {
    'background': '#f8f9fa',
    'text': '#343a40',
    'primary': '#007bff',
    'secondary': '#6c757d',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107'
}

# Placeholder for global dataframe
global_df = None

# Layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Insurance Fraud Analytics Dashboard", className="text-center text-primary mb-4"),
        ], width=12)
    ]),
    # File Upload Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Upload Your Data"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files', style={'color': colors['primary']})
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px 0'
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', style={'marginTop': '10px', 'color': colors['text']}),
                    dbc.Spinner(html.Div(id='loading-output'), color="primary", type="grow")
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    # Main Content (Hidden until data is uploaded)
    html.Div(id='main-content', style={'display': 'none'}, children=[
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Filters"),
                    dbc.CardBody([
                        html.Label("Date Range:"),
                        dcc.DatePickerRange(
                            id='date-range',
                            min_date_allowed=None,
                            max_date_allowed=None,
                            start_date=None,
                            end_date=None,
                            className="mb-3"
                        ),
                        html.Label("Channel:"),
                        dcc.Dropdown(id='channel-filter', className="mb-3"),
                        html.Label("State:"),
                        dcc.Dropdown(id='state-filter')
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Row([
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H4("Total Cases", className="text-center"),
                        html.H2(id="total-cases", className="text-center text-primary")
                    ]))),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H4("Fraud Cases", className="text-center"),
                        html.H2(id="fraud-cases", className="text-center text-danger")
                    ]))),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H4("Fraud Rate", className="text-center"),
                        html.H2(id="fraud-rate", className="text-center text-warning")
                    ]))),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H4("Avg. Claim", className="text-center"),
                        html.H2(id="avg-claim", className="text-center text-success")
                    ])), width=3 if 'CLAIMAMOUNT' in (global_df.columns if global_df is not None else []) else 0)
                ])
            ], width=9)
        ], className="mb-4"),
        # Charts
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Claims by State"),
                dbc.CardBody(dcc.Graph(id="state-bar", style={"height": "300px"}))
            ]), width=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Claims by Channel"),
                dbc.CardBody(dcc.Graph(id="channel-bar", style={"height": "300px"}))
            ]), width=6)
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Claims Over Time"),
                dbc.CardBody(dcc.Graph(id="time-series", style={"height": "300px"}))
            ]), width=12)
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Policy to Death Period"),
                dbc.CardBody(dcc.Graph(id="histogram-policy-death", style={"height": "300px"}))
            ]), width=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Death to Intimation Period"),
                dbc.CardBody(dcc.Graph(id="histogram-death-intimation", style={"height": "300px"}))
            ]), width=6)
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Fraud Hotspots"),
                dbc.CardBody(dcc.Graph(id="fraud-hotspots", style={"height": "350px"}))
            ]), width=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Relationship Analysis"),
                dbc.CardBody(dcc.Graph(id="relationship-analysis", style={"height": "350px"}))
            ]), width=6)
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Fraud Distribution by Location"),
                dbc.CardBody(dcc.Graph(id="treemap", style={"height": "350px"}))
            ]), width=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Channel Fraud Rate Comparison"),
                dbc.CardBody(dcc.Graph(id="radar-chart", style={"height": "350px"}))
            ]), width=6)
        ], className="mb-4")
    ])
], fluid=True, style={'backgroundColor': colors['background']})

# Callback for file upload
@app.callback(
    [Output('upload-status', 'children'),
     Output('main-content', 'style'),
     Output('loading-output', 'children'),
     Output('date-range', 'min_date_allowed'),
     Output('date-range', 'max_date_allowed'),
     Output('date-range', 'start_date'),
     Output('date-range', 'end_date'),
     Output('channel-filter', 'options'),
     Output('channel-filter', 'value'),
     Output('state-filter', 'options'),
     Output('state-filter', 'value'),
     Output('avg-claim', 'style')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def upload_data(contents, filename):
    global global_df
    if contents is None:
        return ("No file uploaded yet.", {'display': 'none'}, no_update, 
                None, None, None, None, [], None, [], None, {'display': 'block'})
    try:
        # Parse uploaded file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        # Use file extension to determine how to read the file
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return ("Unsupported file format. Please upload .xlsx or .csv files.", 
                    {'display': 'none'}, no_update, None, None, None, None, [], None, [], None, {'display': 'block'})
        
        # Rename the column to match the expected name
        if 'Dummy Policy No' in df.columns:
            df.rename(columns={'Dummy Policy No': 'Policy_Number'}, inplace=True)

        # Preprocess data - only these columns are now required
        required_columns = ['POLICYRISKCOMMENCEMENTDATE', 'Date of Death', 'INTIMATIONDATE', 'CHANNEL', 
                          'CORRESPONDENCESTATE', 'Fraud Category', 'Policy_Number']
        # Check if required columns exist
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            return (f"Uploaded file is missing required columns: {', '.join(missing_cols)}", 
                    {'display': 'none'}, no_update, None, None, None, None, [], None, [], None, {'display': 'block'})
        
        # Convert date columns
        date_columns = ['POLICYRISKCOMMENCEMENTDATE', 'Date of Death', 'INTIMATIONDATE']
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Calculate derived columns
        df['Policy_to_Death_Days'] = (df['Date of Death'] - df['POLICYRISKCOMMENCEMENTDATE']).dt.days
        df['Death_to_Intimation_Days'] = (df['INTIMATIONDATE'] - df['Date of Death']).dt.days
        df['Month_Year'] = df['INTIMATIONDATE'].dt.to_period('M').astype(str)
        df['Year'] = df['INTIMATIONDATE'].dt.year
        df['Fraud_Flag'] = df['Fraud Category'].isin(['Fraudulent', 'Suspicious'])
        
        # Update global dataframe
        global_df = df
        
        # Get unique values for filters
        states = sorted(df['CORRESPONDENCESTATE'].dropna().unique())
        channels = sorted(df['CHANNEL'].dropna().unique())
        
        # Set date range defaults
        min_date = df['INTIMATIONDATE'].min().date()
        max_date = df['INTIMATIONDATE'].max().date()
        start_date = min_date
        end_date = max_date
        
        # Show/hide avg claim card based on data availability
        avg_claim_style = {'display': 'block'} if 'CLAIMAMOUNT' in df.columns else {'display': 'none'}
        return (
            f"File '{filename}' uploaded successfully with {len(df)} records.",
            {'display': 'block'},
            no_update,
            min_date,
            max_date,
            start_date,
            end_date,
            [{'label': 'All', 'value': 'All'}] + [{'label': channel, 'value': channel} for channel in channels],
            'All',
            [{'label': 'All', 'value': 'All'}] + [{'label': state, 'value': state} for state in states],
            'All',
            avg_claim_style
        )
    except Exception as e:
        return (f"Error processing file: {str(e)}", 
                {'display': 'none'}, no_update, None, None, None, None, [], None, [], None, {'display': 'block'})

# Callback for metrics
@app.callback(
    [Output('total-cases', 'children'),
     Output('fraud-cases', 'children'),
     Output('fraud-rate', 'children'),
     Output('avg-claim', 'children')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('channel-filter', 'value'),
     Input('state-filter', 'value')]
)
def update_metrics(start_date, end_date, channel, state):
    global global_df
    if global_df is None:
        return "0", "0", "0%", "$0"
    if not start_date or not end_date:
        return "0", "0", "0%", "$0"
    filtered_df = global_df.copy()
    # Filter by date
    filtered_df = filtered_df[
        (filtered_df['INTIMATIONDATE'] >= pd.to_datetime(start_date)) &
        (filtered_df['INTIMATIONDATE'] <= pd.to_datetime(end_date))
    ]
    # Filter by channel and state
    if channel and channel != 'All':
        filtered_df = filtered_df[filtered_df['CHANNEL'] == channel]
    if state and state != 'All':
        filtered_df = filtered_df[filtered_df['CORRESPONDENCESTATE'] == state]
    # Calculate metrics
    total_cases = filtered_df['Policy_Number'].nunique()
    fraud_cases = filtered_df['Fraud_Flag'].sum()
    fraud_rate = f"{(fraud_cases / total_cases * 100):.1f}%" if total_cases > 0 else "0.0%"
    # Only calculate avg claim if the column exists
    if 'CLAIMAMOUNT' in filtered_df.columns:
        avg_claim = f"${filtered_df['CLAIMAMOUNT'].mean():,.0f}" if not filtered_df.empty else "$0"
    else:
        avg_claim = "N/A"
    return f"{total_cases:,}", f"{int(fraud_cases):,}", fraud_rate, avg_claim

# Callback for charts
@app.callback(
    [Output('state-bar', 'figure'),
     Output('channel-bar', 'figure'),
     Output('time-series', 'figure'),
     Output('histogram-policy-death', 'figure'),
     Output('histogram-death-intimation', 'figure'),
     Output('fraud-hotspots', 'figure'),
     Output('relationship-analysis', 'figure'),
     Output('treemap', 'figure'),
     Output('radar-chart', 'figure')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('channel-filter', 'value'),
     Input('state-filter', 'value')]
)
def update_all_charts(start_date, end_date, channel, state):
    global global_df
    if global_df is None:
        empty_fig = px.scatter()
        empty_fig.update_layout(
            annotations=[dict(text="No data available", showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")]
        )
        return [empty_fig] * 9
    if not start_date or not end_date:
        empty_fig = px.scatter()
        empty_fig.update_layout(
            annotations=[dict(text="No data available", showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")]
        )
        return [empty_fig] * 9
    filtered_df = global_df.copy()
    # Filter by date
    filtered_df = filtered_df[
        (filtered_df['INTIMATIONDATE'] >= pd.to_datetime(start_date)) &
        (filtered_df['INTIMATIONDATE'] <= pd.to_datetime(end_date))
    ]
    # Filter by channel and state
    if channel and channel != 'All':
        filtered_df = filtered_df[filtered_df['CHANNEL'] == channel]
    if state and state != 'All':
        filtered_df = filtered_df[filtered_df['CORRESPONDENCESTATE'] == state]
    # Handle empty dataframe case
    if filtered_df.empty:
        empty_fig = px.scatter()
        empty_fig.update_layout(
            annotations=[dict(text="No data available", showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")]
        )
        return [empty_fig] * 9
    # State bar chart
    state_counts = filtered_df['CORRESPONDENCESTATE'].value_counts().reset_index()
    state_counts.columns = ['State', 'Count']
    state_bar = px.bar(
        state_counts.nlargest(10, 'Count'),
        x='Count',
        y='State',
        orientation='h',
        labels={'Count': 'Number of Cases', 'State': 'State'},
        color='Count',
        color_continuous_scale='Blues'
    )
    state_bar.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    # Channel bar chart
    channel_counts = filtered_df['CHANNEL'].value_counts().reset_index()
    channel_counts.columns = ['Channel', 'Count']
    channel_bar = px.bar(
        channel_counts,
        x='Channel',
        y='Count',
        labels={'Channel': 'Channel', 'Count': 'Number of Cases'},
        color='Channel',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    channel_bar.update_layout(showlegend=False, plot_bgcolor='white', paper_bgcolor='white')
    # Time series chart
    time_data = filtered_df.copy()
    time_data['Month_Year_Date'] = pd.to_datetime(time_data['Month_Year'])
    time_series = time_data.groupby('Month_Year_Date').size().reset_index(name='Count')
    time_series = time_series.sort_values('Month_Year_Date')
    time_chart = px.line(
        time_series,
        x='Month_Year_Date',
        y='Count',
        labels={'Month_Year_Date': 'Month', 'Count': 'Number of Cases'},
        markers=True
    )
    time_chart.update_traces(line_color='#007bff', line_width=2)
    time_chart.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    # Histogram: Policy to Death
    hist_policy = px.histogram(
        filtered_df,
        x='Policy_to_Death_Days',
        nbins=30,
        labels={'Policy_to_Death_Days': 'Days', 'count': 'Number of Cases'},
        color_discrete_sequence=['#28a745']
    )
    hist_policy.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    # Histogram: Death to Intimation
    hist_death = px.histogram(
        filtered_df,
        x='Death_to_Intimation_Days',
        nbins=30,
        labels={'Death_to_Intimation_Days': 'Days', 'count': 'Number of Cases'},
        color_discrete_sequence=['#dc3545']
    )
    hist_death.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    # Fraud hotspots
    fraud_data = filtered_df[filtered_df['Fraud_Flag'] == True]
    if not fraud_data.empty:
        if 'CORRESPONDENCEPOSTCODE' in fraud_data.columns and 'CORRESPONDENCECITY' in fraud_data.columns:
            fraud_counts = fraud_data.groupby(['CORRESPONDENCEPOSTCODE', 'CORRESPONDENCECITY']).size().reset_index(name='Fraud_Count')
            fraud_counts['CORRESPONDENCEPOSTCODE'] = fraud_counts['CORRESPONDENCEPOSTCODE'].astype(str)
            fraud_counts['Location'] = fraud_counts['CORRESPONDENCECITY'] + ' (' + fraud_counts['CORRESPONDENCEPOSTCODE'] + ')'
            top_frauds = fraud_counts.nlargest(10, 'Fraud_Count')
            hotspot_chart = px.bar(
                top_frauds,
                x='Fraud_Count',
                y='Location',
                orientation='h',
                labels={'Fraud_Count': 'Number of Fraud Cases', 'Location': ''},
                color='Fraud_Count',
                color_continuous_scale='Reds'
            )
        else:
            hotspot_chart = go.Figure()
            hotspot_chart.add_annotation(text="Missing location data",
                                        x=0.5, y=0.5, showarrow=False)
    else:
        hotspot_chart = go.Figure()
        hotspot_chart.add_annotation(text="No fraud cases in selected filters",
                                    x=0.5, y=0.5, showarrow=False)
    hotspot_chart.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    # Relationship scatter
    scatter_df = filtered_df.dropna(subset=['Policy_to_Death_Days', 'Death_to_Intimation_Days', 'CHANNEL'])
    if not scatter_df.empty:
        relationship_chart = px.scatter(
            scatter_df,
            x='Policy_to_Death_Days',
            y='Death_to_Intimation_Days',
            color='CHANNEL',
            labels={
                'Policy_to_Death_Days': 'Days from Policy to Death',
                'Death_to_Intimation_Days': 'Days from Death to Intimation',
                'CHANNEL': 'Channel'
            },
            opacity=0.7
        )
    else:
        relationship_chart = go.Figure()
        relationship_chart.add_annotation(text="No data available",
                                           x=0.5, y=0.5, showarrow=False)
    relationship_chart.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    # Treemap
    if not fraud_data.empty:
        treemap = px.treemap(
            fraud_data,
            path=['CORRESPONDENCESTATE', 'CORRESPONDENCECITY'],
            values='Fraud_Flag',
            color_discrete_sequence=['#FF6B6B'],
        )
    else:
        treemap = go.Figure()
        treemap.add_annotation(text="No fraud data", x=0.5, y=0.5, showarrow=False)
    treemap.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    # Radar chart: Channel performance
    if 'CHANNEL' in filtered_df.columns:
        radar_data = filtered_df.groupby('CHANNEL').agg(
            Total_Cases=('CHANNEL', 'count'),
            Fraud_Cases=('Fraud_Flag', 'sum')
        ).reset_index()
        radar_data['Fraud_Rate'] = 0
        mask = radar_data['Total_Cases'] > 0
        radar_data.loc[mask, 'Fraud_Rate'] = (radar_data.loc[mask, 'Fraud_Cases'] / 
                                            radar_data.loc[mask, 'Total_Cases']) * 100
        radar_chart = go.Figure()
        radar_chart.add_trace(go.Scatterpolar(
            r=radar_data['Fraud_Rate'],
            theta=radar_data['CHANNEL'],
            fill='toself',
            name='Fraud Rate %'
        ))
        radar_chart.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max(100, radar_data['Fraud_Rate'].max() + 5)])),
            showlegend=False
        )
    else:
        radar_chart = go.Figure()
        radar_chart.add_annotation(text="Channel data not available", x=0.5, y=0.5, showarrow=False)
    return state_bar, channel_bar, time_chart, hist_policy, hist_death, hotspot_chart, relationship_chart, treemap, radar_chart

# Running app
if __name__ == '__main__':
    app.run(debug=True)