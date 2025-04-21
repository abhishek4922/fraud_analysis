import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Sample Indian data
data = {
    "State": ["Maharashtra", "Maharashtra", "Karnataka", "Karnataka", "Delhi", "Tamil Nadu"],
    "City": ["Mumbai", "Pune", "Bangalore", "Mysore", "New Delhi", "Chennai"],
    "Age": [17, 22, 30, 46, 36, 50],
    "Sales": [200, 150, 300, 100, 250, 180]
}
df = pd.DataFrame(data)

# Age Group Categorization
def categorize_age(age):
    if age < 18:
        return 'Below 18'
    elif 18 <= age <= 25:
        return '18–25'
    elif 25 < age <= 45:
        return '25–45'
    else:
        return '45+'

df['AgeGroup'] = df['Age'].apply(categorize_age)

# Bootstrap themes
light_theme = dbc.themes.BOOTSTRAP
dark_theme = dbc.themes.DARKLY

# Create Dash app (start with light theme)
app = dash.Dash(__name__, external_stylesheets=[light_theme])
app.title = "Indian Sales Dashboard"
server = app.server

# Layout with toggle
app.layout = html.Div([
    dcc.Store(id='theme-store', data='light'),

    dbc.Navbar(
        dbc.Container([
            html.H4("Indian Sales Dashboard with Filters", className='text-white'),
            dbc.Button("Switch to Dark Mode", id="theme-toggle", color="secondary", outline=True, className="ml-auto")
        ]),
        color="primary",
        dark=True,
        className="mb-4"
    ),

    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Label("State:"),
                dcc.Dropdown(
                    id='state-filter',
                    options=[{'label': s, 'value': s} for s in sorted(df['State'].unique())],
                    placeholder="Select or type a state",
                    searchable=True
                )
            ], width=4),

            dbc.Col([
                html.Label("City:"),
                dcc.Dropdown(
                    id='city-filter',
                    options=[{'label': c, 'value': c} for c in sorted(df['City'].unique())],
                    placeholder="Select or type a city",
                    searchable=True
                )
            ], width=4),

            dbc.Col([
                html.Label("Age Group:"),
                dcc.Dropdown(
                    id='age-group-filter',
                    options=[
                        {'label': 'Below 18', 'value': 'Below 18'},
                        {'label': '18–25', 'value': '18–25'},
                        {'label': '25–45', 'value': '25–45'},
                        {'label': '45+', 'value': '45+'},
                    ],
                    placeholder="Select age group"
                )
            ], width=4),
        ], className="mb-4"),

        dcc.Graph(id='sales-graph')
    ])
])

# Callback to update graph
@app.callback(
    Output('sales-graph', 'figure'),
    [Input('state-filter', 'value'),
     Input('city-filter', 'value'),
     Input('age-group-filter', 'value')]
)
def update_graph(state, city, age_group):
    filtered_df = df.copy()
    if state:
        filtered_df = filtered_df[filtered_df['State'] == state]
    if city:
        filtered_df = filtered_df[filtered_df['City'] == city]
    if age_group:
        filtered_df = filtered_df[filtered_df['AgeGroup'] == age_group]
    fig = px.bar(filtered_df, x="City", y="Sales", color="State", title="Filtered Sales (India)")
    return fig

# Callback to toggle theme
@app.callback(
    Output("theme-toggle", "children"),
    Output("theme-store", "data"),
    Input("theme-toggle", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True
)
def toggle_theme(n, current):
    if current == "light":
        app._external_stylesheets = [dark_theme]
        return "Switch to Light Mode", "dark"
    else:
        app._external_stylesheets = [light_theme]
        return "Switch to Dark Mode", "light"

# Run app
if __name__ == '__main__':
    app.run(debug=True)
