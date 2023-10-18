import dash
from dash import dcc, html, Input, Output
import plotly.express as px


class DashboardHolder:
    def __init__(self, dataframe, price_columns):
        self.data_frame = dataframe
        self.fuel_price_columns = price_columns
        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.register_callbacks()

    def setup_layout(self):
        self.app.layout = html.Div([
            html.H1("Histogramme des Prix des Carburants"),

            html.Label("Sélectionnez le carburant :"),
            dcc.Dropdown(
                id='carburant-dropdown',
                options=[{'label': fuel.split('_')[0], 'value': fuel}
                         for fuel in self.fuel_price_columns],
                value=self.fuel_price_columns[0]
            ),

            dcc.Graph(id='histogram-graph')
        ])

    def register_callbacks(self):
        @self.app.callback(
            Output('histogram-graph', 'figure'),
            [Input('carburant-dropdown', 'value')]
        )
        def update_histogram(fuel_selected):
            fuel_name = fuel_selected.split('_')[0]
            histogram_fig = px.histogram(
                self.data_frame,
                x=fuel_selected,
                title=f"Histogramme des prix en France du {fuel_name}",
                labels={fuel_selected: f"Prix du {fuel_name} en €"},
                nbins=30,
            )
            histogram_fig.update_traces(
                marker=dict(line=dict(width=1, color='Blue')))
            return histogram_fig


# if __name__ == '__main__':
#     price_columns_list = ['Gazole_prix', 'SP98_prix', 'SP95_prix',
#                           'E85_prix', 'E10_prix', 'GPLc_prix']
#     df = pd.read_csv('processed_data.csv')
#     dashboard = DashboardHolder(df, price_columns_list)
#     dashboard.app.run_server(debug=True)
