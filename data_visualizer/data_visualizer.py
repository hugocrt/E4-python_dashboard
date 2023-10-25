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
        map1 = folium.Map(
            location=france_center,
            zoom_start=6,
            tiles='cartodb positron'
        )
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

    def generate_average_barchart(self, area):
        # if area[0].isDigit():
        #     data = self.data_frame.query(f'cp_ville == "{area}"')
        # else
        data = self.data_frame.query(f'Département == "{area}"')
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
                           f'stations :<br>'
                           f' {area}',
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

    @staticmethod
    def create_dropdown(ptext, plist, pid):
        if not type(plist) == pd.Series:
            plist = pd.Series(plist)
        return dbc.Col([
            html.Label(ptext),
            dcc.Dropdown(
                id=f'{pid}-dropdown',
                options=[{'label': element, 'value': element}
                         for element in plist.unique()],
                value=plist.unique()[0],
                clearable=False
            ),
        ], md=4)

    @staticmethod
    def create_text_card(header_name, body_id):
        class_name = 'card-title text-center'
        first_word = header_name.split('-')[0]
        if first_word == 'id':
            h5_tag = html.H5(id=header_name, className=class_name)
        else:
            h5_tag = html.H5(header_name, className=class_name)

        return dbc.Card(
            [
                dbc.CardHeader(h5_tag,
                               style={'display': 'flex',
                                      'align-items': 'center',
                                      'justify-content': 'center'}),
                dbc.CardBody(html.Div(id=body_id))
            ],
        )

    @staticmethod
    def create_graph_card(callback, graph_id=None,
                          generate_static_graph=None):
        if callback:
            body_content = dcc.Graph(id=graph_id)
        else:
            body_content = dcc.Graph(figure=generate_static_graph)
        return dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    body_content
                ),
                className="mt-4 shadow",
            )
        )

    def setup_layout(self):
        self.app.layout = html.Div([
            self.set_title('Prix et répartition des carburants par ville en '
                           'France métropolitaine'),
            self.set_date(self.last_update_date),

            dbc.Row([
                self.create_dropdown('Sélectionnez la région :',
                                     self.data_frame['Région'],
                                     'région'),
                self.create_dropdown('Sélectionnez le département :',
                                     self.data_frame['Département'],
                                     'département'),
                self.create_dropdown('Sélectionnez la ville :',
                                     self.data_frame['cp_ville'],
                                     'ville')
            ]),

            dbc.Row([
                dbc.CardGroup(
                    [
                        self.create_text_card(header_name='France',
                                              body_id='average-prices'),
                        self.create_text_card(header_name='id-card1-title',
                                              body_id='reg-price'),
                        self.create_text_card(header_name='id-card2-title',
                                              body_id='dep-price'),
                        self.create_text_card(header_name='id-card3-title',
                                              body_id='city-price')
                    ],
                    className="mt-4 shadow",
                ),
            ]),

            dbc.CardGroup([
                self.create_graph_card(False,
                                       generate_static_graph=
                                       self.generate_percentage_barchart()),
                self.create_graph_card(True,
                                       'department-average-barchart'),
            ]),

            dbc.Col([
                self.create_dropdown('Sélectionnez le carburant :',
                                     self.fuel_columns,
                                     'carburant'),
                self.create_graph_card(True, 'histogram-plot')
            ], md=6),
            self.create_text_card(
                'Répartition des stations en France par ville'
                ' et prix des carburants', 'id-folium-map'),
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
            Output('id-card1-title', 'children'),
            [Input('région-dropdown', 'value')]
        )
        def update_blue_text(region_selected):
            return html.Div([
                html.Span(region_selected, style={'color': 'blue'})
            ])
        @self.app.callback(
            Output('id-card2-title', 'children'),
            [Input('département-dropdown', 'value')]
        )
        def update_blue_text(departement_selected):
            return html.Div([
                html.Span(departement_selected, style={'color': 'blue'})
            ])

        @self.app.callback(
            Output('id-card3-title', 'children'),
            [Input('ville-dropdown', 'value')]
        )
        def update_blue_text(city_selected):
            return html.Div([
                html.Span(city_selected, style={'color': 'blue'})
            ])

        @self.app.callback(
            Output('dep-price', 'children'),
            [Input('département-dropdown', 'value')]
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
            Output('city-price', 'children'),
            [Input('ville-dropdown', 'value')]
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
            Output('reg-price', 'children'),
            [Input('région-dropdown', 'value')]
        )
        def display_price_difference(city_selected):
            df_filtered = self.data_frame[
                self.data_frame['Région'] == city_selected]
            avg_prices_reg = df_filtered[self.fuel_columns].mean()
            avg_prices_national = self.data_frame[self.fuel_columns].mean()

            price_difference_list = [
                html.Li(
                    [
                        f"{fuel} : {avg_prices_reg[fuel]:.3f} € ",
                        html.Span(
                            f"("
                            f"{avg_prices_reg[fuel] - avg_prices_national[fuel]:+.3f} €)",
                            style={'color': 'red' if avg_prices_reg[
                                                         fuel] >
                                                     avg_prices_national[
                                                         fuel] else 'green'}
                        )
                    ]
                )
                for fuel in avg_prices_reg.keys()
            ]
            return html.Ul(price_difference_list)

        @self.app.callback(
            Output('department-average-barchart', 'figure'),
            [Input('département-dropdown', 'value')]
        )
        def update_department(departement_selected):
            return self.generate_average_barchart(departement_selected)

        @self.app.callback(
            Output('id-folium-map', 'children'),  # Update the 'folium-map' Div
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
