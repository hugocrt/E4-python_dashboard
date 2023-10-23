import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import folium
from folium.plugins import MarkerCluster


class DashboardHolder:
    def __init__(self, dataframe, price_columns, lud):
        self.data_frame = dataframe
        self.fuel_columns = price_columns
        self.last_update_date = lud
        self.app = dash.Dash(__name__,
                             external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.setup_layout()
        self.register_callbacks()

    def generate_folium_map(self):

        def get_city_popup(row):
            """
            Generate the popup content for a city marker.

            Args:
                row (pd.Series): A row from the DataFrame.

            Returns:
                folium.Popup: A Popup object.
            """
            popup_title = f"<h4>{row['cp_ville']}</h4>"

            # Generate the fuel information for the popup
            popup_fuel = ''
            for col in price_columns_list:
                fuel_value = row[col]
                if pd.notna(fuel_value):
                    popup_fuel += f"<b>{col}:</b> {fuel_value:.3f}€/L<br>"
                else:
                    # popup_fuel += (html.Strong(col),
                    #               html.Span('Non disponible',
                    #                         style={'color': 'red'}),
                    #               html.Br())

                    popup_fuel += (f"<b>{col}:</b> <span "
                                   f"style='color:red;'>Non disponible</span><br>")

            popup_stations_count = (f"<br><b>Nombre de stations:</b>"
                                    f" {row['Nombre de stations']}")

            return folium.Popup(popup_title + popup_fuel + popup_stations_count,
                                max_width=300)

        def add_markers(df, mc):
            for _, row in df.iterrows():
                folium.Marker(
                    location=[row['Latitude'], row['Longitude']],
                    popup=get_city_popup(row)
                ).add_to(mc)

        france_center = [46.232193, 2.209667]
        map1 = folium.Map(location=france_center, zoom_start=6,
                          tiles='cartodb positron')
        mc1 = MarkerCluster()
        add_markers(self.data_frame, mc1)
        map1.add_child(mc1)
        folium_map_html = map1.get_root().render()
        return html.Iframe(srcDoc=folium_map_html,
                    style={'width': '100%', 'height': '600px'})

    def generate_histogram(self, selected_fuel='Gazole'):
        histogram_fig = px.histogram(
            self.data_frame,
            x=selected_fuel,
            title=f"Histogramme des prix en France du {selected_fuel}",
            labels={selected_fuel: f"Prix du {selected_fuel} en €"},
            nbins=30,
        )

        histogram_fig.update_traces(
            marker=dict(line=dict(width=1, color='Blue'))
        )

        return histogram_fig

    def generate_department_average_barchart(self, department):
        data = self.data_frame.query(f'Département == "{department}"')
        percentage = [(fuel, data[fuel].count() / data.shape[0] * 100)
                      for fuel in self.fuel_columns]

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
        fig.update_traces(texttemplate='%{text:.1f}%',
                          textposition='outside')  # Optional: Format the text

        return fig

    def generate_percentage_barchart(self):
        percentage = [(fuel, self.data_frame[fuel].count() /
                       self.data_frame.shape[0] * 100) for fuel
                      in self.fuel_columns]

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
        fig.update_traces(texttemplate='%{text:.1f}%',
                          textposition='outside')  # Optional: Format the text

        return fig

    @staticmethod
    def set_title(title_text):
        return html.H1(title_text, style={
                'text-align': 'center', 'margin-bottom': '20px',
                'font-weight': 'bold', 'text-decoration': 'underline'})

    @staticmethod
    def set_date(update_date):
        return html.Div(f"Dernière mise à jour des données : {update_date}",
                 style={'text-align': 'right', 'font-size': '20px',
                        'color': 'orange'})

    def setup_layout(self):
        self.app.layout = html.Div([
            self.set_title('Dashboard des Prix des Carburants'),
            self.set_date(self.last_update_date),
            dbc.Row([
                dbc.Col([
                    html.Label("Sélectionnez le carburant :"),
                    dcc.Dropdown(
                        id='carburant-dropdown',
                        options=[{'label': fuel, 'value': fuel}
                                 for fuel in self.fuel_columns],
                        value=self.fuel_columns[0],
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
                dbc.Col([
                    html.Label("Sélectionnez la Ville :"),
                    dcc.Dropdown(
                        id='city-dropdown',
                        options=[{'label': city, 'value': city}
                                 for city in
                                 self.data_frame['cp_ville'].unique()],
                        value=self.data_frame['cp_ville'].unique()[0],
                        clearable=False
                    ),
                ], md=4),
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.CardGroup(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.H5("Prix moyens en "
                                                       "France",
                                                           className="card-title text-center"),
                                                   style={'height': '150px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                                    dbc.CardBody(html.Div(id='average-prices'))
                                ],
                            ),
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.Div(id='card2-title',
                                                            className="card-title "
                                                                      "text-center"),
                                                   style={'height': '150px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                                    dbc.CardBody(html.Div(
                                        id='department-price-difference',
                                                          className="custom-card-text"))
                                ]
                            ),
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.Div(id='card3-title',
                                                            className="card-title "
                                                                      "text-center"),
                                                   style={'height': '150px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                                    dbc.CardBody(html.Div(
                                        id='city-price-difference',
                                        className="custom-card-text"))
                                ]
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
            dbc.Col([
                dbc.Card(
                    [
                        dbc.CardHeader(html.H5("Répartition des stations en "
                                               "France et Prix des carburants "
                                               "des stations par ville",
                                               className="card-title "
                                                         "text-center"),
                                       ),

                        dbc.CardBody(html.Div(id='folium-map')),
                    ],
                    className="mt-4 shadow",
                    id='folium-card'
                ),
            ], md=6),

        ], className="container")

    def register_callbacks(self):
        @self.app.callback(
            Output('histogram-plot', 'figure'),
            [Input('carburant-dropdown', 'value')]
        )
        def update_histogram(fuel_selected):
            return self.generate_histogram(fuel_selected)

        @self.app.callback(
            Output('average-prices', 'children'),
            [Input('carburant-dropdown', 'value')]
        )
        def print_average_prices(fuel_selected):
            avg_prices = self.data_frame[
                self.fuel_columns].mean()  # Calculate average prices for all fuels
            avg_prices_list = [
                html.Li(f"{fuel} : {avg_price:.3f} €")
                for fuel, avg_price in avg_prices.items()]
            return html.Ul(avg_prices_list)

        @self.app.callback(
            Output('card2-title', 'children'),
            [Input('departement-dropdown', 'value')]
        )
        def update_card2_title(departement_selected):
            return html.Div([
                "Prix moyen ",
                html.Span(departement_selected, style={'color': 'blue'}),
                " et différence par rapport au territoire métropolitain"
            ])

        @self.app.callback(
            Output('card3-title', 'children'),
            [Input('city-dropdown', 'value')]
        )
        def update_card2_title(city_selected):
            return html.Div([
                "Prix moyen ",
                html.Span(city_selected, style={'color': 'blue'}),
                " et différence par rapport au territoire métropolitain"
            ])

        @self.app.callback(
            Output('department-price-difference', 'children'),
            [Input('departement-dropdown', 'value')]
        )
        def display_price_difference(departement_selected):
            df_filtered = self.data_frame[
                self.data_frame['Département'] == departement_selected]
            avg_prices_departement = df_filtered[self.fuel_columns].mean()
            avg_prices_national = self.data_frame[self.fuel_columns].mean()

            price_difference_list = [
                html.Li(
                    [
                        f"{fuel} : {avg_prices_departement[fuel]:.3f} € ",
                        html.Span(
                            f"("
                            f"{avg_prices_departement[fuel] - avg_prices_national[fuel]:+.3f} €)",
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
            Output('city-price-difference', 'children'),
            [Input('city-dropdown', 'value')]
        )
        def display_price_difference(city_selected):
            df_filtered = self.data_frame[
                self.data_frame['cp_ville'] == city_selected]
            avg_prices_city = df_filtered[self.fuel_columns].mean()
            avg_prices_national = self.data_frame[self.fuel_columns].mean()

            price_difference_list = [
                html.Li(
                    [
                        f"{fuel} : {avg_prices_city[fuel]:.3f} € ",
                        html.Span(
                            f"("
                            f"{avg_prices_city[fuel] - avg_prices_national[fuel]:+.3f} €)",
                            style={'color': 'red' if avg_prices_city[
                                                         fuel] >
                                                     avg_prices_national[
                                                         fuel] else 'green'}
                        )
                    ]
                )
                for fuel in avg_prices_city.keys()
            ]
            return html.Ul(price_difference_list)

        @self.app.callback(
            Output('department-average-barchart', 'figure'),
            [Input('departement-dropdown', 'value')]
        )
        def update_department(departement_selected):
            return self.generate_department_average_barchart(departement_selected)

        @self.app.callback(
            Output('folium-map', 'children'),  # Update the 'folium-map' Div
            [Input('carburant-dropdown', 'value')]
        )
        def update_folium_map(fuel_selected):
            return self.generate_folium_map()


if __name__ == '__main__':
    price_columns_list = ['Gazole', 'SP98', 'SP95',
                          'E85', 'E10', 'GPLc']
    date = 'date test'
    df = pd.read_csv('processed_data.csv')
    dashboard = DashboardHolder(df, price_columns_list, date)
    dashboard.app.run_server(debug=True)
