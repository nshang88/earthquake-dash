import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load your earthquake dataset
df = pd.read_csv('data/earth_data.csv')  # Replace with your actual file

# Convert Date column to datetime and extract year and month
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['year'] = df['Date'].dt.year
df['month'] = df['Date'].dt.month

# Categorize magnitudes
def get_mag_category(mag):
    if mag >= 8:
        return ">8"
    elif mag >= 7:
        return "7-8"
    elif mag >= 6:
        return "6-7"
    elif mag >= 5:
        return "5-6"
    else:
        return "<5"

color_map = {
    "5-6": "blue",
    "6-7": "orange",
    "7-8": "purple",
    ">8": "red",
    "<5": "gray"
}

# Add magnitude category column
df['mag_category'] = df['Magnitude'].apply(get_mag_category)

# Get dropdown options
all_years = sorted(df['year'].unique(), reverse=True)
all_months = sorted(df['month'].unique())
all_mag_cats = ["5-6", "6-7", "7-8", ">8"]

# App setup
app = dash.Dash(__name__)
app.title = "Global Earthquake Dashboard"
server = app.server

# Layout
app.layout = html.Div([
    html.H2("Global Earthquake Dashboard"),

    html.Div([
        html.Label("Select Year(s)"),
        dcc.Dropdown(
            options=[{"label": str(y), "value": y} for y in all_years],
            value=all_years,
            multi=True,
            id='year-selector'
        ),
        html.Label("Select Month(s)", style={"marginTop": "10px"}),
        dcc.Dropdown(
            options=[{"label": str(m), "value": m} for m in all_months],
            value=all_months,
            multi=True,
            id='month-selector'
        ),
        html.Label("Select Magnitude Category", style={"marginTop": "10px"}),
        dcc.Dropdown(
            options=[{"label": m, "value": m} for m in all_mag_cats],
            value=all_mag_cats,
            multi=True,
            id='mag-selector'
        )
    ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top"}),

    html.Div([
        dcc.Graph(id='earthquake-map'),
        dcc.Graph(id='yearly-count-bar-chart')
    ], style={"width": "68%", "display": "inline-block", "paddingLeft": "2%"})
])

# Callback
@app.callback(
    [Output('earthquake-map', 'figure'),
     Output('yearly-count-bar-chart', 'figure')],
    [Input('year-selector', 'value'),
     Input('month-selector', 'value'),
     Input('mag-selector', 'value')]
)
def update_dashboard(selected_years, selected_months, selected_mags):
    if not selected_years or not selected_months or not selected_mags:
        return go.Figure(), go.Figure()

    df_filtered = df[
        df['year'].isin(selected_years) &
        df['month'].isin(selected_months) &
        df['mag_category'].isin(selected_mags)
    ]

    # Map
    fig_map = go.Figure()
    for cat in sorted(df_filtered['mag_category'].unique()):
        df_cat = df_filtered[df_filtered['mag_category'] == cat]
        fig_map.add_trace(go.Scattergeo(
            lon=df_cat['Longitude'],
            lat=df_cat['Latitude'],
            mode='markers',
            marker=dict(size=4, color=color_map.get(cat, 'gray')),
            name=f'Mag {cat}',
            text=[
                f"Magnitude: {mag}<br>Date: {date.strftime('%Y-%m-%d')}<br>Lat: {lat:.2f}, Lon: {lon:.2f}"
                for mag, date, lat, lon in zip(df_cat['Magnitude'], df_cat['Date'], df_cat['Latitude'], df_cat['Longitude'])
            ],
            hoverinfo='text'
        ))

    fig_map.update_layout(
        geo_scope='world',
        title='Earthquake Locations Colored by Magnitude Category',
        legend_title_text='Magnitude Category',
        margin=dict(l=0, r=0, t=30, b=0)
    )

    # Yearly Bar Chart
    yearly_counts = df_filtered.groupby('year').size().reset_index(name='earthquake_count')
    yearly_counts = yearly_counts.sort_values('year')

    year_fig = px.bar(
        yearly_counts,
        x='year',
        y='earthquake_count',
        title='Earthquake Count by Year',
        labels={'earthquake_count': 'Earthquake Count'},
        color='earthquake_count',
        color_continuous_scale='Plasma'
    )

    return fig_map, year_fig

if __name__ == '__main__':
    app.run(debug=True)

