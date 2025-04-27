import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import base64
import io
from datetime import datetime

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.Div(
            [
                html.H4("Upload Data"),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div(['Drag and Drop or ', html.A('Select a CSV File')]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    multiple=False
                ),
                html.H4("Filters"),
                html.Label("Policy Start Date Range:"),
                dcc.DatePickerRange(
                    id='date-range',
                    min_date_allowed=None,
                    max_date_allowed=None,
                    start_date=None,
                    end_date=None,
                    display_format='YYYY-MM-DD'
                ),
                html.Label("Channel:"),
                dcc.Dropdown(
                    id='channel-filter',
                    options=[{'label': 'All', 'value': 'All'}],
                    value='All',
                    clearable=False
                ),
                html.Label("State:"),
                dcc.Dropdown(
                    id='state-filter',
                    options=[{'label': 'All', 'value': 'All'}],
                    value='All',
                    clearable=False
                ),
                html.Label("Product Type:"),
                dcc.Dropdown(
                    id='product-filter',
                    options=[{'label': 'All', 'value': 'All'}],
                    value='All',
                    clearable=False
                )
            ],
            style={'width': '25%', 'padding': '20px'}
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Total Policies", style={'textAlign': 'center'}),
                        html.H2(id='total-policies', style={'color': 'blue', 'textAlign': 'center'})
                    ],
                    className="card",
                    style={'width': '30%', 'margin': '10px', 'padding': '20px', 'border': '1px solid #ddd'}
                ),
                html.Div(
                    [
                        html.H3("Fraud Cases", style={'textAlign': 'center'}),
                        html.H2(id='fraud-cases', style={'color': 'red', 'textAlign': 'center'})
                    ],
                    className="card",
                    style={'width': '30%', 'margin': '10px', 'padding': '20px', 'border': '1px solid #ddd'}
                ),
                html.Div(
                    [
                        html.H3("Fraud Rate", style={'textAlign': 'center'}),
                        html.H2(id='fraud-rate', style={'color': 'orange', 'textAlign': 'center'})
                    ],
                    className="card",
                    style={'width': '30%', 'margin': '10px', 'padding': '20px', 'border': '1px solid #ddd'}
                )
            ],
            style={'display': 'flex'}
        )
    ],
    style={'display': 'flex'}
)

def parse_contents(contents, filename):
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            # Convert empty strings to NaN for consistency
            df = df.replace(r'^\s*$', pd.NA, regex=True)
            return df
        return None
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None

@app.callback(
    [Output('date-range', 'min_date_allowed'),
     Output('date-range', 'max_date_allowed'),
     Output('date-range', 'start_date'),
     Output('date-range', 'end_date'),
     Output('channel-filter', 'options'),
     Output('state-filter', 'options'),
     Output('product-filter', 'options')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_filters(contents, filename):
    if not contents:
        return (None, None, None, None, 
                [{'label': 'All', 'value': 'All'}], 
                [{'label': 'All', 'value': 'All'}],
                [{'label': 'All', 'value': 'All'}])
    
    df = parse_contents(contents, filename)
    if df is None:
        return (None, None, None, None, 
                [{'label': 'All', 'value': 'All'}], 
                [{'label': 'All', 'value': 'All'}],
                [{'label': 'All', 'value': 'All'}])
    
    min_date = max_date = start_date = end_date = None
    channel_options = [{'label': 'All', 'value': 'All'}]
    state_options = [{'label': 'All', 'value': 'All'}]
    product_options = [{'label': 'All', 'value': 'All'}]
    
    try:
        # Use POLICYRISKCOMMENCEMENTDATE for date range
        if 'POLICYRISKCOMMENCEMENTDATE' in df.columns:
            df['POLICYRISKCOMMENCEMENTDATE'] = pd.to_datetime(df['POLICYRISKCOMMENCEMENTDATE'], errors='coerce')
            df = df.dropna(subset=['POLICYRISKCOMMENCEMENTDATE'])
            if not df.empty:
                min_date = df['POLICYRISKCOMMENCEMENTDATE'].min()
                max_date = df['POLICYRISKCOMMENCEMENTDATE'].max()
                start_date = min_date
                end_date = max_date
        
        # Use CHANNEL for channel filter
        if 'CHANNEL' in df.columns:
            channels = df['CHANNEL'].dropna().unique()
            channel_options.extend([{'label': ch, 'value': ch} for ch in sorted(channels)])
        
        # Use CORRESPONDENCESTATE for state filter
        if 'CORRESPONDENCESTATE' in df.columns:
            states = df['CORRESPONDENCESTATE'].dropna().unique()
            state_options.extend([{'label': st, 'value': st} for st in sorted(states)])
        
        # Use Product Type for product filter
        if 'Product Type' in df.columns:
            products = df['Product Type'].dropna().unique()
            product_options.extend([{'label': p, 'value': p} for p in sorted(products)])
            
    except Exception as e:
        print(f"Error updating filters: {e}")
    
    return (min_date, max_date, start_date, end_date,
            channel_options, state_options, product_options)

@app.callback(
    [Output('total-policies', 'children'),
     Output('fraud-cases', 'children'),
     Output('fraud-rate', 'children')],
    [Input('upload-data', 'contents'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('channel-filter', 'value'),
     Input('state-filter', 'value'),
     Input('product-filter', 'value')],
    [State('upload-data', 'filename')]
)
def update_metrics(contents, start_date, end_date, channel, state, product, filename):
    if not contents:
        return "Upload data", "Upload data", "Upload data"
    
    df = parse_contents(contents, filename)
    if df is None:
        return "Invalid file", "Invalid file", "Invalid file"
    
    try:
        # Initialize filtered_df with all data
        filtered_df = df.copy()
        
        # Apply date filter if date column exists and dates are provided
        if 'POLICYRISKCOMMENCEMENTDATE' in filtered_df.columns:
            filtered_df['POLICYRISKCOMMENCEMENTDATE'] = pd.to_datetime(
                filtered_df['POLICYRISKCOMMENCEMENTDATE'], errors='coerce')
            filtered_df = filtered_df.dropna(subset=['POLICYRISKCOMMENCEMENTDATE'])
            
            if start_date and end_date:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                filtered_df = filtered_df[
                    (filtered_df['POLICYRISKCOMMENCEMENTDATE'] >= start_date) & 
                    (filtered_df['POLICYRISKCOMMENCEMENTDATE'] <= end_date)
                ]
        
        # Apply channel filter if column exists and not 'All'
        if 'CHANNEL' in filtered_df.columns and channel != 'All':
            filtered_df = filtered_df[filtered_df['CHANNEL'] == channel]
        
        # Apply state filter if column exists and not 'All'
        if 'CORRESPONDENCESTATE' in filtered_df.columns and state != 'All':
            filtered_df = filtered_df[filtered_df['CORRESPONDENCESTATE'] == state]
        
        # Apply product filter if column exists and not 'All'
        if 'Product Type' in filtered_df.columns and product != 'All':
            filtered_df = filtered_df[filtered_df['Product Type'] == product]
        
        # Calculate total policies using Dummy Policy No
        if 'Dummy Policy No' not in filtered_df.columns:
            return "No policy data", "N/A", "N/A"
        
        total_policies = filtered_df['Dummy Policy No'].nunique()
        
        # Calculate fraud cases
        if 'Fraud Category' not in filtered_df.columns:
            return f"{total_policies:,}", "No fraud data", "N/A"
        
        fraud_mask = ~filtered_df['Fraud Category'].isin(['No Fraud', 'NA', '', pd.NA, None])
        fraud_cases = filtered_df[fraud_mask].shape[0]
        
        fraud_rate = (fraud_cases / total_policies * 100) if total_policies > 0 else 0
        
        return (
            f"{total_policies:,}",
            f"{fraud_cases:,}",
            f"{fraud_rate:.2f}%"
        )
    
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return "Error", "Error", "Error"

if __name__ == '__main__':
    app.run(debug=True)