import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc

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

# Initialize app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = dbc.Container([
    html.H1("Fraud Analysis Dashboard", className='text-center text-primary mb-4'),

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
], fluid=True)

# Callbacks or static plots
def generate_all_graphs():
    state_counts = df['CORRESPONDENCESTATE'].value_counts().nlargest(10)
    state_bar = px.bar(x=state_counts.values, y=state_counts.index,
                       orientation='h', title='Top 10 States with Highest Fraud Cases')

    channel_counts = df['CHANNEL'].value_counts()
    channel_bar = px.bar(x=channel_counts.index, y=channel_counts.values, title='Fraud Count by Channel')

    time_series = df.groupby('Month_Year').size().reset_index(name='Count')
    time_series['Month_Year'] = pd.to_datetime(time_series['Month_Year'])
    time_series = time_series.sort_values('Month_Year')
    time_chart = px.line(time_series, x='Month_Year', y='Count', title='Monthly Trend of Fraud Cases')

    hist_policy = px.histogram(df, x='Policy_to_Death_Days', nbins=30,
                               title='Days Between Policy Start and Death')
    hist_death = px.histogram(df, x='Death_to_Intimation_Days', nbins=30,
                              title='Days Between Death and Intimation')

    fraud_data = df[df['Fraud Category'].notna()]
    fraud_counts = fraud_data.groupby(['CORRESPONDENCEPOSTCODE', 'CORRESPONDENCECITY']).size().reset_index(name='Fraud_Count')
    fraud_counts['Location'] = fraud_counts['CORRESPONDENCECITY'] + ' (' + fraud_counts['CORRESPONDENCEPOSTCODE'].astype(str) + ')'
    top_frauds = fraud_counts.nlargest(10, 'Fraud_Count')
    hotspot_chart = px.bar(top_frauds, x='Fraud_Count', y='Location', orientation='h', title='Top 10 Fraud Hotspots')

    scatter_df = df.dropna(subset=['Policy_to_Death_Days', 'Death_to_Intimation_Days', 'CHANNEL'])
    relationship_chart = px.scatter(scatter_df, x='Policy_to_Death_Days', y='Death_to_Intimation_Days',
                                    color='CHANNEL', title='Policy-to-Death vs Death-to-Intimation by Channel')

    state_channel = df.groupby(['CORRESPONDENCESTATE', 'CHANNEL']).size().reset_index(name='Count')
    pivot_data = state_channel.pivot(index='CORRESPONDENCESTATE', columns='CHANNEL', values='Count').fillna(0)
    top_states = pivot_data.sum(axis=1).nlargest(10).index
    stacked_data = pivot_data.loc[top_states]
    channel_dist = px.bar(stacked_data, title='Channel Distribution in Top 10 States', barmode='stack')

    geo_data = df.groupby('CORRESPONDENCESTATE').size().reset_index(name='Count')
    treemap = px.treemap(geo_data, path=['CORRESPONDENCESTATE'], values='Count',
                         title='Geographical Distribution of Fraud Cases')

    radar_data = df.groupby('CHANNEL').agg(
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

# Assign all figures
(state_bar, channel_bar, time_chart, hist_policy, hist_death,
 hotspot_chart, relationship_chart, channel_dist,
 treemap_fig, radar_fig) = generate_all_graphs()

@app.callback(Output('state-bar', 'figure'), Input('state-bar', 'id'))
def update_state_bar(_): return state_bar

@app.callback(Output('channel-bar', 'figure'), Input('channel-bar', 'id'))
def update_channel_bar(_): return channel_bar

@app.callback(Output('time-series', 'figure'), Input('time-series', 'id'))
def update_time_series(_): return time_chart

@app.callback(Output('histogram-policy-death', 'figure'), Input('histogram-policy-death', 'id'))
def update_hist_policy(_): return hist_policy

@app.callback(Output('histogram-death-intimation', 'figure'), Input('histogram-death-intimation', 'id'))
def update_hist_death(_): return hist_death

@app.callback(Output('fraud-hotspots', 'figure'), Input('fraud-hotspots', 'id'))
def update_hotspots(_): return hotspot_chart

@app.callback(Output('relationship-analysis', 'figure'), Input('relationship-analysis', 'id'))
def update_relationship(_): return relationship_chart

@app.callback(Output('channel-distribution', 'figure'), Input('channel-distribution', 'id'))
def update_channel_distribution(_): return channel_dist

@app.callback(Output('treemap', 'figure'), Input('treemap', 'id'))
def update_treemap(_): return treemap_fig

@app.callback(Output('radar-chart', 'figure'), Input('radar-chart', 'id'))
def update_radar(_): return radar_fig

if __name__ == '__main__':
    app.run(debug=True)
