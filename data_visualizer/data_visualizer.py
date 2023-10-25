import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
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
                             external_stylesheets=[dbc.themes.LUX],

                             )
        self.dep = dataframe['Département'].unique()
        self.reg = dataframe['Région'].unique()
        self.setup_layout()
        self.register_callbacks()

    def setup_layout(self):
        self.app.layout = html.Div([

            self.set_title('Prix et répartition des carburants par ville en '
                           'France métropolitaine'),
            self.set_date(self.last_update_date),

            dbc.Row([
                self.create_dropdown('Sélectionnez la région :',
                                     self.data_frame['Région'],
                                     'reg'),
                self.create_dropdown('Sélectionnez le département :',
                                     self.data_frame['Département'],
                                     'dep'),
                self.create_dropdown('Sélectionnez la ville :',
                                     self.data_frame['cp_ville'],
                                     'city')
            ]),

            html.Div(style={'margin-bottom': '20px'}),

            dbc.Row([
                dbc.CardGroup(
                    [
                        self.create_area_card(False,
                                              header_name='France',
                                              body_id='fr-prices',
                                              generate_static_graph=
                                              self.generate_average_barchart()
                                              ),
                        self.create_area_card(True,
                                              header_name='reg-price-title',
                                              body_id='reg-price',
                                              graph_id='reg-barchart'
                                              ),
                        self.create_area_card(True,
                                              header_name='dep-price-title',
                                              body_id='dep-price',
                                              graph_id='dep-barchart'
                                              ),
                        self.create_area_card(True,
                                              header_name='city-price-title',
                                              body_id='city-price',
                                              graph_id='city-barchart'
                                              )
                    ],
                )
            ]),

            dbc.Col([
                self.create_dropdown('Sélectionnez le carburant :',
                                     self.fuel_columns, 'fuel'),
                self.create_graph_card(True, 'histogram-plot')
            ]),

            self.create_text_card(
                'Répartition des stations en France par ville'
                ' et prix des carburants', 'id-folium-map')

        ], className="container")

    def register_callbacks(self):
        @self.app.callback(
            Output('reg-price-title', 'children'),
            [Input('reg-dropdown', 'value')]
        )
        def update_blue_text(region_selected):
            return html.Div([
                html.Span(region_selected, style={'color': 'blue'})
            ])

        @self.app.callback(
            Output('dep-price-title', 'children'),
            [Input('dep-dropdown', 'value')]
        )
        def update_blue_text(departement_selected):
            return html.Div([
                html.Span(departement_selected, style={'color': 'blue'})
            ])

        @self.app.callback(
            Output('city-price-title', 'children'),
            [Input('city-dropdown', 'value')]
        )
        def update_blue_text(city_selected):
            return html.Div([
                html.Span(city_selected, style={'color': 'blue'})
            ])

        @self.app.callback(
            Output('fr-prices', 'children'),
            [Input('fuel-dropdown', 'value')]
        )
        def print_average_prices(fuel_selected):
            avg_prices = self.data_frame[
                self.fuel_columns].mean()
            avg_prices_list = [
                html.Li(f"{fuel} : {avg_price:.3f} €")
                for fuel, avg_price in avg_prices.items()]
            return html.Ul(avg_prices_list)

        @self.app.callback(
            Output('reg-price', 'children'),
            [Input('reg-dropdown', 'value')]
        )
        def update_price_display(area_selected):
            return self.display_price_difference(area_selected)

        @self.app.callback(
            Output('dep-price', 'children'),
            [Input('dep-dropdown', 'value')]
        )
        def update_price_display(area_selected):
            return self.display_price_difference(area_selected)

        @self.app.callback(
            Output('city-price', 'children'),
            [Input('city-dropdown', 'value')]
        )
        def update_price_display(area_selected):
            return self.display_price_difference(area_selected)

        @self.app.callback(
            Output('reg-barchart', 'figure'),
            [Input('reg-dropdown', 'value')]
        )
        def update_department(area_selected):
            return self.generate_average_barchart(area_selected)

        @self.app.callback(
            Output('dep-barchart', 'figure'),
            [Input('dep-dropdown', 'value')]
        )
        def update_department(area_selected):
            return self.generate_average_barchart(area_selected)

        @self.app.callback(
            Output('city-barchart', 'figure'),
            [Input('city-dropdown', 'value')]
        )
        def update_department(area_selected):
            return self.generate_average_barchart(area_selected)

        @self.app.callback(
            Output('histogram-plot', 'figure'),
            [Input('fuel-dropdown', 'value')]
        )
        def update_histogram(fuel_selected):
            return self.generate_histogram(fuel_selected)

        @self.app.callback(
            Output('id-folium-map', 'children'),  # Update the 'folium-map' Div
            [Input('fuel-dropdown', 'value')]
        )
        def update_folium_map(fuel_selected):
            return self.generate_folium_map()

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

    def get_data_from_area(self, area):
        if area is not None:
            area_query = None
            if area[0].isdigit():
                area_query = 'cp_ville'
            elif area in self.reg:
                area_query = 'Région'
            else:
                area_query = 'Département'
            return self.data_frame.query(f'{area_query} == "{area}"')
        else:
            return self.data_frame

    def generate_average_barchart(self, area=None):
        data = self.get_data_from_area(area)
        national_data = self.get_data_from_area(None)

        national_percentage = [
            (fuel,
             round(national_data[fuel].count() / national_data.shape[0] * 100))
            for fuel in self.fuel_columns
        ]

        national_percentage = pd.DataFrame(
            national_percentage,
            columns=['Fuel_Type', 'nat_per']
        )

        national_percentage = national_percentage.sort_values(
            by='nat_per',
            ascending=False
        )

        area_percentage = [
            (fuel, round(data[fuel].count() / data.shape[0] * 100)) for
            fuel in self.fuel_columns
        ]

        area_percentage = pd.DataFrame(
            area_percentage,
            columns=['Fuel_Type', 'area_per']
        )

        area_percentage = area_percentage.sort_values(
            by='area_per',
            ascending=False
        )

        merged_percentage = pd.merge(
            area_percentage, national_percentage, on='Fuel_Type'
        )

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=merged_percentage['Fuel_Type'],
            y=merged_percentage['area_per'],
            name='Area Data',
            text=merged_percentage['area_per'],
            textposition='outside',
            marker=dict(color='blue')
        ))

        # Add trace for difference data
        for i, row in merged_percentage.iterrows():
            diff = round(row['area_per'] - row['nat_per'])

            if diff == 0:
                continue
            elif diff > 0:
                diff_text = f'+{diff}%'
                color = 'green'
            else:
                diff_text = f'{diff}%'
                color = 'red'

            fig.add_trace(go.Bar(
                x=[row['Fuel_Type']],
                y=[diff],
                text=diff_text,
                textposition='outside',
                marker=dict(color=color)
            ))

        fig.update_layout(
            xaxis_title='Type de carburant',
            yaxis_title='Présent dans les villes à (%)',
            barmode='relative',
            margin=dict(
                l=0,
                r=0,
                t=0,
                b=0,
            ),
            height=250,
            showlegend=False
        )

        return fig

    def display_price_difference(self, area=None):
        data = self.get_data_from_area(area)
        avg_area_price = data[self.fuel_columns].mean()
        avg_prices_national = self.get_data_from_area(None)[
            self.fuel_columns].mean()

        price_difference_list = [
            html.Li(
                [
                    f"{fuel} : {avg_area_price[fuel]:.3f} € ",
                    html.Span(
                        f"("
                        f"{avg_area_price[fuel] - avg_prices_national[fuel]:+.3f} €)",
                        style={'color': 'red'
                        if avg_area_price[fuel] > avg_prices_national[fuel]
                        else 'green'}
                    )
                ]
            )
            for fuel in avg_area_price.keys()
        ]
        return html.Ul(price_difference_list)

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
    def create_dropdown(ptext, plist, id_dropdown):
        if not type(plist) == pd.Series:
            plist = pd.Series(plist)
        return dbc.Col([
            html.Label(ptext),
            dcc.Dropdown(
                id=f'{id_dropdown}-dropdown',
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
    def create_area_card(callback, header_name, body_id, graph_id=None,
                         generate_static_graph=None):

        class_name = 'card-title text-center'
        first_word = header_name.split('-')[0]

        if callback:
            h5_tag = html.H5(id=header_name, className=class_name)
            body_content = dcc.Graph(
                id=graph_id,
                config={'displayModeBar': False}
            )
        else:
            h5_tag = html.H5(header_name, className=class_name)
            body_content = dcc.Graph(
                figure=generate_static_graph,
                config={'displayModeBar': False}
            )

        return dbc.Card(
            [
                dbc.CardHeader(h5_tag,
                               style={'display': 'flex',
                                      'align-items': 'center',
                                      'justify-content': 'center'}),
                dbc.CardBody([
                    html.Div(id=body_id),
                    html.Hr(),
                    body_content
                ])
            ]
        )

    @staticmethod
    def create_graph_card(callback, graph_id=None,
                          generate_static_graph=None):
        if callback:
            body_content = dcc.Graph(id=graph_id)
        else:
            body_content = dcc.Graph(figure=generate_static_graph)
        return dbc.Card(
            dbc.CardBody(body_content)
        )


if __name__ == '__main__':
    price_columns_list = ['Gazole', 'SP98', 'SP95',
                          'E85', 'E10', 'GPLc']
    date = 'date test'
    df = pd.read_csv('processed_data.csv')
    dashboard = DashboardHolder(df, price_columns_list, date)
    dashboard.app.run_server(debug=True)
