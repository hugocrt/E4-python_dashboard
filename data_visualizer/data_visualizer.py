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
                             external_stylesheets=[dbc.themes.LUX]
                             )
        self.dep = dataframe['Département'].unique()
        self.reg = dataframe['Région'].unique()
        self.setup_layout()
        self.register_callbacks()

    def setup_layout(self):
        self.app.layout = html.Div([
            dbc.Card([
                dbc.CardBody([
                    self.set_title(
                        'Prix et répartition des carburants par ville en '
                        'France métropolitaine'),

                    html.Div(self.set_date(self.last_update_date)),
                ])
            ], style={'background-color': '#f0f0f0', 'border-radius': '10px'},
                className='header-box'),

            self.create_whitespace(5),

            html.Div([
                dbc.Row([
                    dbc.Col(),
                    self.create_dropdown('Sélectionnez la région :',
                                         self.data_frame['Région'],
                                         'reg'),
                    self.create_dropdown('Sélectionnez le département :',
                                         self.data_frame['Département'],
                                         'dep'),
                    self.create_dropdown('Sélectionnez la ville :',
                                         self.data_frame['cp_ville'],
                                         'cit')
                ]),

                self.create_whitespace(10),

                dbc.Row([
                    dbc.Col(self.generate_area_card('France'), md=3,
                            style={'padding': '0'}),
                    dbc.Col(id='reg-card', md=3, style={'padding': '0'}),
                    dbc.Col(id='dep-card', md=3, style={'padding': '0'}),
                    dbc.Col(id='cit-card', md=3, style={'padding': '0'})
                ]),


                self.create_whitespace(10),

                dbc.Col([
                    self.create_dropdown('Sélectionnez le carburant :',
                                         self.fuel_columns, 'fuel'),
                    self.create_graph_card(True, 'histogram-plot')
                ]),

                self.create_whitespace(10),

                self.create_text_card(
                    'Répartition des stations en France par ville'
                    ' et prix des carburants', 'id-folium-map')

            ], className='content')
        ], className='container')

    def register_callbacks(self):
        @self.app.callback(
            [Output(f'{area}-card', 'children')
             for area in ['reg', 'dep', 'cit']],

            [Input(f'{area}-dropdown', 'value')
             for area in ['reg', 'dep', 'cit']]
        )
        def update_area_card(*selected_areas):
            return [self.generate_area_card(area) for area in selected_areas]

        @self.app.callback(
            Output('histogram-plot', 'figure'),
            [Input('fuel-dropdown', 'value')]
        )
        def update_histogram(fuel_selected):
            return self.generate_price_histogram(fuel_selected)

        @self.app.callback(
            Output('id-folium-map', 'children'),
            [Input('fuel-dropdown', 'value')]
        )
        def update_folium_map(fuel_selected):
            return self.generate_folium_map()

    def generate_folium_map(self):
        france_center = [46.232193, 2.209667]
        map1 = folium.Map(
            location=france_center,
            zoom_start=6,
            tiles='cartodb positron'
        )
        mc1 = MarkerCluster()
        self._add_cities_markers(self.data_frame, mc1)
        map1.add_child(mc1)
        folium_map_html = map1.get_root().render()
        return html.Iframe(srcDoc=folium_map_html,
                           style={'width': '100%', 'height': '600px'})

    def _get_city_popup(self, row):
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
        for col in self.fuel_columns:
            fuel_value = row[col]
            if pd.notna(fuel_value):
                popup_fuel += f"<b>{col}:</b> {fuel_value:.3f}€/L<br>"
            else:
                popup_fuel += (f"<b>{col}:</b> <span "
                               f"style='color:red;'>Non disponible</span>"
                               f"<br>")

        popup_stations_count = (f"<br><b>Nombre de stations:</b>"
                                f" {row['Nombre de stations']}")

        return folium.Popup(popup_title + popup_fuel + popup_stations_count,
                            max_width=300)

    def _add_cities_markers(self, dataf, mc):
        for _, row in dataf.iterrows():
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=self._get_city_popup(row)
            ).add_to(mc)

    def generate_price_histogram(self, selected_fuel='Gazole'):
        histogram_fig = px.histogram(
            self.data_frame,
            x=selected_fuel,
            title=f"Histogramme des prix en France du {selected_fuel}",
            labels={selected_fuel: f"Prix du {selected_fuel} en €"},
            nbins=30,
        )

        histogram_fig.update_traces(
            marker={'line': {'width': 1, 'color': 'Blue'}}
        )

        return histogram_fig

    def get_data_from_area(self, area):
        if area != 'France':
            if area[0].isdigit():
                area_query = 'cp_ville'
            elif area in self.reg:
                area_query = 'Région'
            else:
                area_query = 'Département'
            return self.data_frame.query(f'{area_query} == "{area}"')
        else:
            return self.data_frame

    def generate_average_barchart(self, area):
        data = self.get_data_from_area(area)
        national_data = self.get_data_from_area('France')

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

        # Sort area_percentage DataFrame based on national_percentage order
        area_percentage['Fuel_Type'] = pd.Categorical(
            area_percentage['Fuel_Type'],
            categories=national_percentage['Fuel_Type'],
            ordered=True)
        area_percentage = area_percentage.sort_values(by='Fuel_Type')

        merged_percentage = pd.merge(
            area_percentage, national_percentage, on='Fuel_Type'
        )

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=merged_percentage['Fuel_Type'],
            y=merged_percentage['area_per'],
            name='Area Data',
            text=merged_percentage['area_per'],
            textposition='auto',
            marker={'color': 'lightblue'}
        ))

        # Add trace for difference data
        for i, row in merged_percentage.iterrows():
            diff = round(row['area_per'] - row['nat_per'])

            if diff == 0:
                continue
            elif diff > 0:
                diff_text = f'+{diff}%'
                color = 'lightgreen'
            else:
                diff_text = f'{diff}%'
                color = 'lightcoral'

            fig.add_trace(go.Bar(
                x=[row['Fuel_Type']],
                y=[diff],
                text=diff_text,
                textposition='auto',
                marker={'color': color}
            ))

        fig.update_layout(
            xaxis_title=None,
            yaxis_title='Disponible dans (%) des villes',
            barmode='overlay',
            margin={
                'l': 0,
                'r': 0,
                't': 0,
                'b': 0
            },
            height=250,
            showlegend=False,

            xaxis={'title_font': {'size': 11}, 'tickangle': -45},
            yaxis={'title_font': {'size': 11}, 'range': [-100, 100]}
        )

        return fig

    def display_price(self, area):
        data = self.get_data_from_area(area)
        avg_area_price = data[self.fuel_columns].mean()
        national_data = self.get_data_from_area('France')
        avg_prices_national = national_data[self.fuel_columns].mean()
        price_difference_list = []

        for fuel in self.fuel_columns:
            price = avg_area_price[fuel]
            if pd.notna(price):
                price_text = (html.Span(
                    fuel,
                    style={'font-weight': 'bold', 'color': 'black'}),
                              html.Span(
                                  f' : {price:+.3f} €')
                )
                price_diff_text = None
                color = 'black'

                if area != 'France':
                    price_diff = (round(price, 3)
                                  - round(avg_prices_national[fuel], 3))

                    if price_diff == 0:
                        price_diff_text = f'({price_diff} €) (=)'
                        color = 'grey'
                    elif price_diff > 0:
                        price_diff_text = f'({price_diff:+.3f} €) ▲'
                        color = 'red'
                    else:
                        price_diff_text = f'({price_diff:+.3f} €) ▼'
                        color = 'green'
            else:
                price_text = (html.Span(
                    fuel,
                    style={'font-weight': 'bold', 'color': 'black'}),
                              html.Span(f' : Non disponible')
                )
                price_diff_text = None
                color = 'grey'

            price_difference_list.append(html.Li(
                [
                    html.Span(price_text),
                    html.Span(
                        price_diff_text,
                        style={'color': color}
                    ) if price_diff_text else None
                ]
            ))

        return html.Ul(price_difference_list)

    @staticmethod
    def set_title(title_text):
        return html.H1(title_text, style={
            'text-align': 'center', 'margin-bottom': '20px',
            'font-weight': 'bold', 'text-decoration': 'underline',
            'font-family': 'Roboto, sans-serif'})

    @staticmethod
    def set_date(update_date):
        return html.Div(f"Dernière mise à jour des données : {update_date}",
                        style={'text-align': 'right', 'font-size': '17px',
                               'color': 'orange',
                               'font-weight': 'bold'})

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
        ], md=3)

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
                dbc.CardHeader(h5_tag),
                dbc.CardBody(html.Div(id=body_id))
            ],
        )

    def generate_area_card(self, area):
        return dbc.Card(
            [
                dbc.CardHeader(
                    html.H5(area,
                            className='card-title text-center',
                            style={'font-size': '12px'}
                            ),
                    style={'display': 'flex',
                           'align-items': 'center',
                           'justify-content': 'center'}
                ),

                dbc.CardBody([
                    html.Div(self.display_price(area)),
                    html.Hr(),
                    dcc.Graph(
                        figure=self.generate_average_barchart(area),
                        config={'displayModeBar': False}
                    )
                ])
            ],
            style={'border-radius': '10px'}
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

    @staticmethod
    def create_whitespace(space):
        return html.Div(style={'margin-bottom': f'{space}px'})


if __name__ == '__main__':
    price_columns_list = ['Gazole', 'SP98', 'SP95',
                          'E85', 'E10', 'GPLc']
    date = 'date test'
    df = pd.read_csv('processed_data.csv')
    dashboard = DashboardHolder(df, price_columns_list, date)
    dashboard.app.run_server(debug=True)
