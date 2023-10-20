import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc


class DashboardHolder:
    def __init__(self, dataframe, price_columns, date):
        self.data_frame = dataframe
        self.fuel_price_columns = price_columns
        self.last_update_date = date
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.setup_layout()
        self.register_callbacks()

    def generate_histogram(self):
        histogram_fig = px.histogram(
            self.data_frame,
            x=self.fuel_price_columns[0],
            title=f"Histogramme des prix en France du {self.fuel_price_columns[0].split('_')[0]}",
            labels={self.fuel_price_columns[0]: f"Prix du {self.fuel_price_columns[0].split('_')[0]} en €"},
            nbins=30,
        )
        histogram_fig.update_traces(
            marker=dict(line=dict(width=1, color='Blue')))
        return histogram_fig

    def generate_department_average_barchart(self, department):
        data = self.data_frame[self.data_frame['Département'] == department]
        percentage = [(fuel, data[fuel].count() / data.shape[0] * 100)
                      for fuel in self.fuel_price_columns]

        # Create a DataFrame for the bar chart
        df_percentage = pd.DataFrame(percentage,
                                     columns=['Fuel_Type', 'Percentage'])

        # Sort the DataFrame by Percentage in descending order
        df_percentage = df_percentage.sort_values(by='Percentage',
                                                  ascending=False)

        # Create the bar chart
        fig = px.bar(df_percentage, x='Fuel_Type', y='Percentage',
                     title=f'Présence du carburant en pourcentage dans les '
                           f'stations : '
                           f' {department}',
                     text='Percentage',
                     # Add this line to display the percentage on the bars
                     labels={
                         'Percentage': 'Percentage (%)'})  # Optional: Rename the y-axis label
        fig.update_traces(texttemplate='%{text:.2f}%',
                          textposition='outside')  # Optional: Format the text

        return fig

    def generate_percentage_barchart(self):
        percentage = [(fuel, self.data_frame[fuel].count() /
                       self.data_frame.shape[0] * 100) for fuel
                      in self.fuel_price_columns]

        # Create a DataFrame for the bar chart
        df_percentage = pd.DataFrame(percentage,
                                     columns=['Fuel_Type', 'Percentage'])

        # Sort the DataFrame by Percentage in descending order
        df_percentage = df_percentage.sort_values(by='Percentage',
                                                  ascending=False)

        # Create the bar chart
        fig = px.bar(df_percentage, x='Fuel_Type', y='Percentage',
                     title='Présence du carburant en pourcentage dans les '
                           f'stations en France métropolitaine',
                     text='Percentage',
                     # Add this line to display the percentage on the bars
                     labels={
                         'Percentage': 'Percentage (%)'})  # Optional: Rename the y-axis label
        fig.update_traces(texttemplate='%{text:.2f}%',
                          textposition='outside')  # Optional: Format the text

        return fig

    def setup_layout(self):
        self.app.layout = html.Div([
            html.H1("Dashboard des Prix des Carburants", style={'text-align': 'center', 'margin-bottom': '20px'}),
            dbc.Navbar(
                dbc.Container(
                    dbc.Row(
                        dbc.Col(
                            html.Div(f"Dernière mise à jour : "
                                     f"{self.last_update_date}", style={
                                'font-size': '14px', 'color': 'orange'}),
                            width={'size': 2, 'offset': 10}
                        )
                    )
                )
            ),

            dbc.Row([
                dbc.Col([
                    html.Label("Sélectionnez le carburant :"),
                    dcc.Dropdown(
                        id='carburant-dropdown',
                        options=[{'label': fuel.split('_')[0], 'value': fuel}
                                for fuel in self.fuel_price_columns],
                        value=self.fuel_price_columns[0],
                        clearable=False
                    ),
                ], md=4),
                dbc.Col([
                    html.Label("Sélectionnez le département :"),
                    dcc.Dropdown(
                        id='departement-dropdown',
                        options=[{'label': departement, 'value': departement}
                                for departement in
                                self.data_frame['Département'].unique()],
                        value=self.data_frame['Département'].unique()[0],
                        clearable=False
                    ),
                ], md=4),
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.CardGroup(
                        [
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5("Prix moyens en France", className="card-title"),
                                        html.Div(id='average-prices'),  # Added a div to display average prices
                                    ]
                                )
                            ),
                            dbc.Card(
                                html.Div(className="fa fa-list"),
                                className="bg-primary",
                                style={"maxWidth": 75},
                            ),
                        ],
                        className="mt-4 shadow",
                    ),
                    dbc.CardGroup(
                        [
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.Div(id='card2-title', className="card-title"),
                                        html.Div(id='price-difference', className="custom-card-text")  # Ajout de cet élément
                                    ]
                                )
                            ),
                            dbc.Card(
                                html.Div(className="fa fa-list"),
                                className="bg-primary",
                                style={"maxWidth": 75},
                            ),
                        ],
                        className="mt-4 shadow",
                    ),
                ], md=6),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(id='histogram-plot', figure=self.generate_histogram())
                        ),
                        className="mt-4 shadow",
                    ),
                ], md=6),
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(id='department-average-barchart',
                                      figure=self.generate_department_average_barchart(self.data_frame['Département'].unique()[0]))
                        ),
                        className="mt-4 shadow",
                    ),
                ], md=6),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(id='percentage-barchart',
                                      figure=self.generate_percentage_barchart())
                        ),
                        className="mt-4 shadow",
                    ),
                ], md=6),
            ]),

        ], className="container")

    def register_callbacks(self):
        @self.app.callback(
            Output('histogram-plot', 'figure'),
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

        @self.app.callback(
            Output('average-prices', 'children'),
            [Input('carburant-dropdown', 'value')]
        )
        def print_average_prices(fuel_selected):
            avg_prices = self.data_frame[
                self.fuel_price_columns].mean()  # Calculate average prices for all fuels
            avg_prices_list = [
                html.Li(f"{fuel.split('_')[0]} : {avg_price:.2f} €")
                for fuel, avg_price in avg_prices.items()]
            return html.Ul(avg_prices_list)

        @self.app.callback(
            Output('card2-title', 'children'),
            [Input('departement-dropdown', 'value')]
        )
        def update_card2_title(departement_selected):
            return (f"Prix moyen du {departement_selected} et différence par "
                    f"rapport au territoire métropolitain")

        @self.app.callback(
            Output('price-difference', 'children'),
            [Input('departement-dropdown', 'value')]
        )
        def display_price_difference(departement_selected):
            df_filtered = self.data_frame[
                self.data_frame['Département'] == departement_selected]
            avg_prices_departement = df_filtered[self.fuel_price_columns].mean()
            avg_prices_national = self.data_frame[self.fuel_price_columns].mean()

            price_difference_list = [
                html.Li(
                    [
                        f"{fuel.split('_')[0]} : {avg_prices_departement[fuel]:.2f} € ",
                        html.Span(
                            f"({avg_prices_departement[fuel] - avg_prices_national[fuel]:+.2f} €)",
                            style={'color': 'red' if avg_prices_departement[
                                                       fuel] >
                                                     avg_prices_national[
                                                         fuel] else 'green'}
                        )
                    ]
                )
                for fuel in avg_prices_departement.keys()
            ]
            return html.Ul(price_difference_list)

        @self.app.callback(
            Output('department-average-barchart', 'figure'),
            [Input('departement-dropdown', 'value')]
        )
        def update_department(departement_selected):
            return self.generate_department_average_barchart(departement_selected)


# if __name__ == '__main__':
#     price_columns_list = ['Gazole_prix', 'SP98_prix', 'SP95_prix',
#                           'E85_prix', 'E10_prix', 'GPLc_prix']
#     date = 'date test'
#     df = pd.read_csv('processed_data.csv')
#     dashboard = DashboardHolder(df, price_columns_list, date)
#     dashboard.app.run_server(debug=True)
