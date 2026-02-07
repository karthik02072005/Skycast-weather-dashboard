import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import requests
import pandas as pd

professional_css = """
body {
    background-color: #f4f7f6;
    font-family: 'Segoe UI', sans-serif;
    margin: 0;
}
.header {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    padding: 40px;
    text-align: center;
    border-radius: 0 0 20px 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.input-box {
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #ccc;
    width: 220px;
    margin-right: 10px;
    font-size: 16px;
    background-color: #ffffff;
    color: #000000;
}
.input-box::placeholder {
    color: #666666;
}
.btn {
    padding: 12px 25px;
    border-radius: 8px;
    border: none;
    background-color: #e74c3c;
    color: white;
    font-weight: bold;
    cursor: pointer;
    transition: 0.3s;
}
.btn:hover {
    background-color: #c0392b;
    transform: translateY(-2px);
}
.card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    text-align: center;
    flex: 1;
    min-width: 150px;
    border-top: 5px solid #3498db;
}
.card h3 {
    margin: 10px 0 0 0;
    color: #2c3e50;
}
.card p {
    color: #7f8c8d;
    font-size: 12px;
    margin: 0;
    text-transform: uppercase;
}
"""
app = dash.Dash(__name__)
app.index_string = f"""
<!DOCTYPE html>
<html>
<head>
    {{%metas%}}
    <title>SkyCast Pro</title>
    {{%css%}}
    <style>{professional_css}</style>
</head>
<body>
    {{%app_entry%}}
    <footer>
        {{%config%}}
        {{%scripts%}}
        {{%renderer%}}
    </footer>
</body>
</html>
"""

app.layout = html.Div([
    html.Div([
        html.H1("ForecastX", style={'margin': '0'}),
        html.P("Real-time Humidity, Rain, and Forecast Data"),
        html.Div([
            dcc.Input(
                id='city-input',
                type='text',
                placeholder='Enter City (Eg: London)',
                value='London',
                debounce=True,   # Update on Enter
                className='input-box'
            ),
            html.Button(
                'Update View',
                id='submit-val',
                n_clicks=0,
                className='btn'
            )
        ], style={'marginTop': '20px'})
    ], className='header'),
    html.Div(
        id='weather-stats',
        style={
            'display': 'flex',
            'justifyContent': 'center',
            'gap': '15px',
            'padding': '30px',
            'flexWrap': 'wrap'
        }
    ),
    html.Div([

        dcc.Graph(id='main-forecast-graph')
    ], style={
        'padding': '0 30px',
        'maxWidth': '1200px',
        'margin': '0 auto'
    })
])
def get_coords(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    try:
        res = requests.get(url).json()
        if 'results' in res:
            data = res['results'][0]
            return (
                data['latitude'],
                data['longitude'],
                data['name'],
                data['country']
            )
    except Exception as e:
        print("Geo Error:", e)
    return None, None, None, None
@app.callback(
    [
        Output('weather-stats', 'children'),
        Output('main-forecast-graph', 'figure')
    ],
    [
        Input('submit-val', 'n_clicks'),
        Input('city-input', 'value')
    ]
)
def update_dashboard(n_clicks, city):
    if not city:
        return [], go.Figure()
    print("Searching:", city)
    lat, lon, name, country = get_coords(city)
    if lat is None:
        error = [
            html.H3(
                f"City '{city}' not found",
                style={'color': '#e74c3c'}
            )
        ]
        return error, go.Figure()
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,"
        f"precipitation,wind_speed_10m"
        f"&hourly=temperature_2m,relative_humidity_2m,precipitation"
        f"&timezone=auto"
    )
    data = requests.get(url).json()
    curr = data['current']
    hourly = data['hourly']
    stats = [
        html.Div([
            html.P("Temperature"),
            html.H3(f"{curr['temperature_2m']} °C")
        ], className='card'),
        html.Div([
            html.P("Humidity"),
            html.H3(f"{curr['relative_humidity_2m']} %")
        ], className='card'),
        html.Div([
            html.P("Rain"),
            html.H3(f"{curr['precipitation']} mm")
        ], className='card'),
        html.Div([
            html.P("Wind Speed"),
            html.H3(f"{curr['wind_speed_10m']} km/h")
        ], className='card'),
        html.Div([
            html.P("Location"),
            html.H3(f"{name}, {country}")
        ], className='card')
    ]
    df = pd.DataFrame({
        "Time": pd.to_datetime(hourly['time'][:24]),
        "Temp": hourly['temperature_2m'][:24],
        "Rain": hourly['precipitation'][:24]
    })
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=df['Temp'],
        name="Temperature",
        fill='tozeroy'
    ))
    fig.add_trace(go.Bar(
        x=df['Time'],
        y=df['Rain'],
        name="Rain",
        opacity=0.5
    ))
    fig.update_layout(
        title=f"24 Hour Forecast - {name}",
        template="plotly_white",
        hovermode="x unified"
    )
    return stats, fig

if __name__ == "__main__":
    app.run(debug=True)