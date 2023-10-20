import dash
import dash_leaflet as dl
from dash import html

import json

with open("processed_data.geojson", 'r') as geojson_file:
    geojson_data = json.load(geojson_file)

app = dash.Dash(__name__)

map_style = {'width': '100%', 'height': '500px'}
map_attribution = ('Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors,'
                   '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>')
colorscale = ['red', 'yellow', 'green', 'blue', 'purple']
color_prop = 'density'

app.layout = html.Div(
    [
        dl.Map(children=[
            dl.TileLayer(
                id='background',
                attribution=map_attribution),
            dl.GeoJSON(
                id='geojson',
                format='geojson',
                data=geojson_data,
                zoomToBoundsOnClick=True,
                options=dict(
                    style=dict(color='blue', opacity=0.5, weight=1, fillColor='blue', fillOpacity=0.2),
                    # tooltip=tooltips  Normalement tu mets un truc ici et ça s'affiche mais pas là stylé
                ),
                hoverStyle=dict(weight=2, color='red', fillColor='red', fillOpacity=0.5),
                cluster=True,
                superClusterOptions=dict(maxZoom=10, radius=150),
                hideout=dict(
                    colorProp=color_prop,
                    circleOptions=dict(fillOpacity=1, stroke=False, radius=100),
                    min=0,
                    max=100,
                    colorscale=colorscale
                )
            ),
        ],
            center=[46.203797228571432, 5.2366706857142855],
            zoom=5,
            style=map_style
        ),
    ])

if __name__ == '__main__':
    app.run_server(debug=True)
