import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from datetime import datetime as dt

# Load data
df = pd.read_excel("Fraud data FY 2023-24 for B&CC.xlsx")

# Preprocess
df['POLICYRISKCOMMENCEMENTDATE'] = pd.to_datetime(df['POLICYRISKCOMMENCEMENTDATE'], errors='coerce')
df['Date of Death'] = pd.to_datetime(df['Date of Death'], errors='coerce')
df['INTIMATIONDATE'] = pd.to_datetime(df['INTIMATIONDATE'], errors='coerce')
df['Policy_to_Death_Days'] = (df['Date of Death'] - df['POLICYRISKCOMMENCEMENTDATE']).dt.days
df['Death_to_Intimation_Days'] = (df['INTIMATIONDATE'] - df['Date of Death']).dt.days
df['Month_Year'] = df['INTIMATIONDATE'].dt.to_period('M').astype(str)
df['Year'] = df['INTIMATIONDATE'].dt.year

# Create fraud flag if Fraud Category exists
df['Fraud_Flag'] = df['Fraud Category'].notna()

# Initialize app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Insurance Fraud Analytics Dashboard"

# Custom colors
colors = {
    'background': '#f8f9fa',
    'text': '#343a40',
    'primary': '#007bff',
    'secondary': '#6c757d',
    'success': '#28a745'
}

# Layout
app.layout = dbc.Container([
    # Header with filters
    dbc.Row([
        dbc.Col([
            html.H1("Insurance Fraud Analytics Dashboard", 
                   className='text-center text-primary my-4'),
            html.P("Interactive dashboard for analyzing fraud patterns in insurance claims",
                   className='text-center text-secondary mb-4')
        ], width=12)
    ]),
    
    # Filters Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Filters", className="bg-primary text-white"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Date Range:"),
                            dcc.DatePickerRange(
                                id='date-range',
                                min_date_allowed=df['INTIMATIONDATE'].min(),
                                max_date_allowed=df['INTIMATIONDATE'].max(),
                                start_date=df['INTIMATIONDATE'].min(),
                                end_date=df['INTIMATIONDATE'].max(),
                                display_format='YYYY-MM-DD'
                            )
                        ], md=4),
                        dbc.Col([
                            html.Label("Channel:"),
                            dcc.Dropdown(
                                id='channel-filter',
                                options=[{'label': 'All', 'value': 'All'}] + 
                                        [{'label': i, 'value': i} for i in df['CHANNEL'].unique()],
                                value='All',
                                clearable=False
                            )
                        ], md=4),
                        dbc.Col([
                            html.Label("State:"),
                            dcc.Dropdown(
                                id='state-filter',
                                options=[{'label': 'All', 'value': 'All'}] + 
                                        [{'label': i, 'value': i} for i in df['CORRESPONDENCESTATE'].unique()],
                                value='All',
                                clearable=False
                            )
                        ], md=4)
                    ])
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    
    # Key Metrics Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Cases", className="card-title"),
                    html.H3(id='total-cases', className="card-text text-primary")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Fraud Cases", className="card-title"),
                    html.H3(id='fraud-cases', className="card-text text-danger")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Fraud Rate", className="card-title"),
                    html.H3(id='fraud-rate', className="card-text text-warning")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Avg Claim Amount", className="card-title"),
                    html.H3(id='avg-claim', className="card-text text-success")
                ])
            ], className="text-center shadow-sm")
        ], md=3)
    ], className="mb-4"),
    
    # Main Charts Row 1
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Fraud Cases by State", className="bg-primary text-white"),
                dbc.CardBody([
                    dcc.Graph(id='state-bar')
                ])
            ], className="h-100 shadow-sm")
        ], lg=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Fraud Cases by Channel", className="bg-primary text-white"),
                dbc.CardBody([
                    dcc.Graph(id='channel-bar')
                ])
            ], className="h-100 shadow-sm")
        ], lg=6)
    ], className="mb-4"),
    
    # Main Charts Row 2
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Monthly Trend of Fraud Cases", className="bg-primary text-white"),
                dbc.CardBody([
                    dcc.Graph(id='time-series')
                ])
            ], className="h-100 shadow-sm")
        ], width=12)
    ], className="mb-4"),
    
    # Main Charts Row 3
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Days Between Policy Start and Death", className="bg-primary text-white"),
                dbc.CardBody([
                    dcc.Graph(id='histogram-policy-death')
                ])
            ], className="h-100 shadow-sm")
        ], lg=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Days Between Death and Intimation", className="bg-primary text-white"),
                dbc.CardBody([
                    dcc.Graph(id='histogram-death-intimation')
                ])
            ], className="h-100 shadow-sm")
        ], lg=6)
    ], className="mb-4"),
    
    # Main Charts Row 4
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Top Fraud Hotspots", className="bg-primary text-white"),
                dbc.CardBody([
                    dcc.Graph(id='fraud-hotspots')
                ])
            ], className="h-100 shadow-sm")
        ], lg=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Policy-to-Death vs Death-to-Intimation", className="bg-primary text-white"),
                dbc.CardBody([
                    dcc.Graph(id='relationship-analysis')
                ])
            ], className="h-100 shadow-sm")
        ], lg=6)
    ], className="mb-4"),
    
    # Additional Analysis Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Geographical Distribution", className="bg-primary text-white"),
                dbc.CardBody([
                    dcc.Graph(id='treemap')
                ])
            ], className="h-100 shadow-sm")
        ], lg=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Channel Performance Metrics", className="bg-primary text-white"),
                dbc.CardBody([
                    dcc.Graph(id='radar-chart')
                ])
            ], className="h-100 shadow-sm")
        ], lg=6)
    ], className="mb-4"),
    
    # Footer
    dbc.Row([
        dbc.Col([
            html.Div([
                html.P("Data last updated: " + dt.now().strftime("%Y-%m-%d"), 
                       className="text-muted small text-center"),
                html.P("© 2025 Quads Team", 
                       className="text-muted small text-center")
            ], className="mt-4")
        ], width=12)
    ])
], fluid=True, style={'backgroundColor': colors['background']})

# Callbacks for filters and metrics
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
    filtered_df = df.copy()
    
    # Apply date filter
    filtered_df = filtered_df[
        (filtered_df['INTIMATIONDATE'] >= pd.to_datetime(start_date)) &
        (filtered_df['INTIMATIONDATE'] <= pd.to_datetime(end_date))
    ]
    
    # Apply channel filter
    if channel != 'All':
        filtered_df = filtered_df[filtered_df['CHANNEL'] == channel]
    
    # Apply state filter
    if state != 'All':
        filtered_df = filtered_df[filtered_df['CORRESPONDENCESTATE'] == state]
    
    # Calculate metrics
    total_cases = len(filtered_df)
    fraud_cases = filtered_df['Fraud_Flag'].sum()
    fraud_rate = f"{(fraud_cases / total_cases * 100):.1f}%" if total_cases > 0 else "0%"
    
    # Assuming there's a claim amount column - adjust as needed
    if 'CLAIMAMOUNT' in filtered_df.columns:
        avg_claim = f"${filtered_df['CLAIMAMOUNT'].mean():,.0f}"
    else:
        avg_claim = "N/A"
    
    return (
        f"{total_cases:,}",
        f"{fraud_cases:,}",
        fraud_rate,
        avg_claim
    )

# Callback for updating all charts
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
    filtered_df = df.copy()
    
    # Apply filters
    filtered_df = filtered_df[
        (filtered_df['INTIMATIONDATE'] >= pd.to_datetime(start_date)) &
        (filtered_df['INTIMATIONDATE'] <= pd.to_datetime(end_date))
    ]
    
    if channel != 'All':
        filtered_df = filtered_df[filtered_df['CHANNEL'] == channel]
    
    if state != 'All':
        filtered_df = filtered_df[filtered_df['CORRESPONDENCESTATE'] == state]
    
    # State bar chart
    state_counts = filtered_df['CORRESPONDENCESTATE'].value_counts().nlargest(10)
    state_bar = px.bar(
        x=state_counts.values, 
        y=state_counts.index,
        orientation='h', 
        title='',
        labels={'x': 'Number of Cases', 'y': 'State'},
        color=state_counts.values,
        color_continuous_scale='Blues'
    )
    state_bar.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    
    # Channel bar chart
    channel_counts = filtered_df['CHANNEL'].value_counts()
    channel_bar = px.bar(
        x=channel_counts.index, 
        y=channel_counts.values, 
        title='',
        labels={'x': 'Channel', 'y': 'Number of Cases'},
        color=channel_counts.index,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    channel_bar.update_layout(showlegend=False, plot_bgcolor='white', paper_bgcolor='white')
    
    # Time series chart
    time_series = filtered_df.groupby('Month_Year').size().reset_index(name='Count')
    time_series['Month_Year'] = pd.to_datetime(time_series['Month_Year'])
    time_series = time_series.sort_values('Month_Year')
    time_chart = px.line(
        time_series, 
        x='Month_Year', 
        y='Count', 
        title='',
        labels={'Month_Year': 'Month', 'Count': 'Number of Cases'},
        markers=True
    )
    time_chart.update_traces(line_color='#007bff', line_width=2)
    time_chart.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    
    # Histogram - Policy to Death
    hist_policy = px.histogram(
        filtered_df, 
        x='Policy_to_Death_Days', 
        nbins=30,
        title='',
        labels={'Policy_to_Death_Days': 'Days', 'count': 'Number of Cases'},
        color_discrete_sequence=['#28a745']
    )
    hist_policy.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    
    # Histogram - Death to Intimation
    hist_death = px.histogram(
        filtered_df, 
        x='Death_to_Intimation_Days', 
        nbins=30,
        title='',
        labels={'Death_to_Intimation_Days': 'Days', 'count': 'Number of Cases'},
        color_discrete_sequence=['#dc3545']
    )
    hist_death.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    
    # Fraud hotspots
    fraud_data = filtered_df[filtered_df['Fraud_Flag']]
    if not fraud_data.empty:
        fraud_counts = fraud_data.groupby(['CORRESPONDENCEPOSTCODE', 'CORRESPONDENCECITY']).size().reset_index(name='Fraud_Count')
        fraud_counts['Location'] = fraud_counts['CORRESPONDENCECITY'] + ' (' + fraud_counts['CORRESPONDENCEPOSTCODE'].astype(str) + ')'
        top_frauds = fraud_counts.nlargest(10, 'Fraud_Count')
        hotspot_chart = px.bar(
            top_frauds, 
            x='Fraud_Count', 
            y='Location', 
            orientation='h', 
            title='',
            labels={'Fraud_Count': 'Number of Fraud Cases', 'Location': ''},
            color='Fraud_Count',
            color_continuous_scale='Reds'
        )
    else:
        hotspot_chart = px.bar(title="No fraud cases in selected filters")
    hotspot_chart.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    
    # Relationship analysis
    scatter_df = filtered_df.dropna(subset=['Policy_to_Death_Days', 'Death_to_Intimation_Days', 'CHANNEL'])
    if not scatter_df.empty:
        relationship_chart = px.scatter(
            scatter_df, 
            x='Policy_to_Death_Days', 
            y='Death_to_Intimation_Days',
            color='CHANNEL', 
            title='',
            labels={
                'Policy_to_Death_Days': 'Days from Policy to Death',
                'Death_to_Intimation_Days': 'Days from Death to Intimation',
                'CHANNEL': 'Channel'
            },
            opacity=0.7
        )
    else:
        relationship_chart = px.scatter(title="No data in selected filters")
    relationship_chart.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    
    # Treemap
    geo_data = filtered_df.groupby('CORRESPONDENCESTATE').size().reset_index(name='Count')
    if not geo_data.empty:
        treemap = px.treemap(
            geo_data, 
            path=['CORRESPONDENCESTATE'], 
            values='Count',
            title='',
            color='Count',
            color_continuous_scale='Greens'
        )
    else:
        treemap = px.treemap(title="No data in selected filters")
    treemap.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    
    # Radar chart
    radar_data = filtered_df.groupby('CHANNEL').agg(
        Avg_Policy_to_Death=('Policy_to_Death_Days', 'mean'),
        Avg_Death_to_Intimation=('Death_to_Intimation_Days', 'mean'),
        Count=('CHANNEL', 'size')
    ).reset_index()
    
    if not radar_data.empty:
        for col in ['Avg_Policy_to_Death', 'Avg_Death_to_Intimation', 'Count']:
            max_val = radar_data[col].max()
            min_val = radar_data[col].min()
            radar_data[f'{col}_Normalized'] = (radar_data[col] - min_val) / (max_val - min_val) if (max_val - min_val) != 0 else 0.5

        top_channels = radar_data.nlargest(5, 'Count')
        fig_radar = go.Figure()
        categories = ['Avg_Policy_to_Death_Normalized', 'Avg_Death_to_Intimation_Normalized', 'Count_Normalized']
        labels = ['Policy to Death', 'Death to Intimation', 'Count']
        
        for _, row in top_channels.iterrows():
            values = [row[col] for col in categories] + [row[categories[0]]]
            fig_radar.add_trace(go.Scatterpolar(
                r=values, 
                theta=labels + [labels[0]],
                fill='toself', 
                name=row['CHANNEL']
            ))
        
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
    else:
        fig_radar = go.Figure()
        fig_radar.add_annotation(text="No data in selected filters", showarrow=False)
    
    return (
        state_bar, channel_bar, time_chart, hist_policy, hist_death, 
        hotspot_chart, relationship_chart, treemap, fig_radar
    )

if __name__ == '__main__':
    app.run(debug=True)