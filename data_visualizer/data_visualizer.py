import dash
import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
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
        self.reg_color_mapping = self.generate_color_mapping(self.reg)
        self.setup_layout()
        self.setup_validation_layout()
        self.register_callbacks()

    def setup_layout(self):
        self.app.layout = html.Div([
            dcc.Location('url', refresh=False),
            self.setup_navbar(),

            html.Div(
                id='page-content',
                children=[],
                style={
                    'flex': '1',
                }
            ),

            self.setup_footer(),
        ], style={
            'margin': '10px',
            'display': 'flex',
            'flex-direction': 'column',
            'min-height': '100vh',
        })

    def setup_validation_layout(self):
        self.app.validation_layout = html.Div([
            html.Div([
                dcc.Location(id="url", refresh=False),
                self.setup_navbar(),
                self.create_whitespace(10),
                html.Div(id="page-content", children=[], )
            ],
                style={'margin': '0px 100px 0px'},
            ),
            self.setup_layout_home(),
            self.setup_layout_histogram(),
            self.setup_layout_map()
        ])

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

        @self.app.callback(
            Output('dep-dropdown', 'options'),
            [Input('reg-dropdown', 'value'),
             Input('switch-button', 'value')]
        )
        def update_dep_dropdown(reg, switch):
            if switch == 'Verrouiller':
                return [{'label': dep, 'value': dep} for dep in
                        self.from_reg_get_dep(reg)]
            else:
                return [{'label': dep, 'value': dep} for dep in
                        self.data_frame['Département'].unique()]

        @self.app.callback(
            Output('cit-dropdown', 'options'),
            [Input('dep-dropdown', 'value'),
             Input('switch-button', 'value')]
        )
        def update_dep_dropdown(dep, switch):
            if switch == 'Verrouiller':
                return [{'label': dep, 'value': dep} for dep in
                        self.from_dep_get_cities(dep)]
            else:
                return [{'label': dep, 'value': dep} for dep in
                        self.data_frame['cp_ville'].unique()]

        @self.app.callback(
            Output('dep-dropdown', 'value'),
            [Input('dep-dropdown', 'options')]
        )
        def set_default_dep_value(options):
            if options:
                return options[0]['value']
            else:
                return None

        @self.app.callback(
            Output('cit-dropdown', 'value'),
            [Input('cit-dropdown', 'options')]
        )
        def set_default_cit_value(options):
            if options:
                return options[0]['value']
            else:
                return None

        @self.app.callback(
            Output('page-content', 'children'),
            [Input('url', 'pathname')]
        )
        def render_page_content(pathname):
            if pathname == '/histogramme':
                return self.setup_layout_histogram()
            elif pathname == '/carte':
                return self.setup_layout_map()
            else:
                return self.setup_layout_home()

    def generate_folium_map(self):
        france_center = [46.232193, 2.209667]
        map1 = folium.Map(
            location=france_center,
            zoom_start=5,
            tiles='cartodb positron',
            max_zoom=18,
            min_zoom=5,
            min_lat=33,
            max_lat=55,
            min_lon=-20,
            max_lon=24,
            max_bounds=True
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

    @staticmethod
    def generate_color_mapping(list_to_map):
        color_mapping = {}
        color_scale = px.colors.qualitative.Light24_r
        for i in range(len(list_to_map)):
            color_mapping[list_to_map[i]] = color_scale[i]

        return color_mapping

    @staticmethod
    def generate_pie_chart(df, names_column, values_column, title,
                           color_mapping):
        fig = px.pie(
            df,
            names=names_column,
            values=values_column,
            title=title,
            color=names_column,
            color_discrete_map=color_mapping,
            hole=0.5
        ).update_traces(textinfo='percent + label',
                        textposition='outside').update_layout(showlegend=False)

        return fig

    @staticmethod
    def setup_navbar():
        return dbc.Nav([
            dbc.NavLink("Accueil", href="/", active="exact"),
            dbc.NavLink("Histogramme", href="/histogramme", active="exact"),
            dbc.NavLink("Cartographie", href="/carte", active="exact"),
        ],
            horizontal=True,
            pills=True,
        )

    def setup_layout_home(self):
        return [
            dbc.Card([
                dbc.CardBody([
                    self.set_title(
                        'Prix et répartition des carburants par ville en '
                        'France métropolitaine'),

                    html.Div(self.set_date(self.last_update_date)),
                ])
            ], style={'background-color': '#f0f0f0',
                      'border-radius': '10px'},
                className='header-box'),

            self.create_whitespace(5),

            html.Div([
                dbc.Row([
                    self.create_switch_button('switch-button'),
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
            ]),
        ]

    def setup_layout_histogram(self):
        return [
            dbc.Card([
                dbc.CardBody([
                    self.set_title(
                        'Distribution des stations essence en France'),

                    html.Div(self.set_date(self.last_update_date)),
                ])
            ], style={'background-color': '#f0f0f0',
                      'border-radius': '10px'},
                className='header-box'),

            self.create_whitespace(5),

            dbc.Col([
                self.create_dropdown('Sélectionnez le carburant :',
                                     self.fuel_columns, 'fuel'),
                self.create_graph_card(True, 'histogram-plot')
            ]),

            self.create_whitespace(10),

            dbc.Col([
                self.create_graph_card(
                    False,
                    generate_static_graph=self.generate_pie_chart(
                        self.data_frame,
                        'Région',
                        'Nombre de stations',
                        'Distribution des Stations par Région',
                        self.reg_color_mapping
                    ),
                ),
                self.create_graph_card(
                    False,
                    generate_static_graph=self.generate_pie_chart(
                        self.data_frame.groupby('Région')['cp_ville']
                        .nunique()
                        .reset_index()
                        .rename(
                            columns={'cp_ville': 'Number_of_Cities'}
                        ),
                        'Région',
                        'Number_of_Cities',
                        'Distribution du nombre de Villes comportant au '
                        'moins une Station par Région',
                        self.reg_color_mapping
                    )
                )
            ]),
        ]

    def setup_layout_map(self):
        return [
            dbc.Card([
                dbc.CardBody([
                    self.set_title(
                        'Répartition des stations en France par ville'
                        ' et prix des carburants'),

                    html.Div(self.set_date(self.last_update_date)),
                ])
            ], style={'background-color': '#f0f0f0',
                      'border-radius': '10px'},
                className='header-box'),

            self.create_whitespace(5),

            dbc.Col([
                self.create_dropdown('Sélectionnez le carburant :',
                                     self.fuel_columns, 'fuel'),
            ]),

            self.create_whitespace(10),

            self.create_text_card(
                'Répartition des stations en France par ville'
                ' et prix des carburants', 'id-folium-map'),
        ]

    def setup_footer(self):
        return html.Footer([
            html.Div([
                # Logo UNIV
                html.Img(
                    src=self.app.get_asset_url('logo_univ.png'),
                    style={
                        'border-radius': '5px',
                        'max-width': '10%',
                        'max-height': '100%',
                    }
                ),

                dbc.Col(
                    html.Div(
                        'Copyright © 2023 / 2024',
                        style={
                            'text-align': 'center',
                            'font-size': '12px',
                            'font-style': 'italic'

                        },
                    ),
                    md=3
                ),

                dbc.Col(
                    html.Div(
                        'CARANGEOT Hugo / SALI--ORLIANGE Lucas, encadrés par '
                        'Monsieur COURIVAUD D.',
                        style={
                            'text-align': 'center',
                            'font-size': '12px'
                            },
                    ),
                    md=3
                ),

                dbc.Col(
                    html.Div(
                        'DSIA-4101A : Python pour la Data Science',
                        style={
                            'text-align': 'center',
                            'font-size': '12px',
                            'text-decoration': 'underline'
                        },
                    ),
                    md=3
                ),

                # Logo ESIEE
                html.Img(
                    src=self.app.get_asset_url('logo_esiee.png'),
                    style={
                        'border-radius': '5px',
                        'max-width': '10%',
                        'max-height': '100%',
                    }
                ),
            ],
                style={
                    'display': 'flex',
                    'justify-content': 'space-between',
                    'color': '#1A1A1A',
                    'border': '1px solid #1A1A1A',
                    'height': '4.5rem',
                    'align-items': 'center',
                    'padding': '10px',
                    'border-radius': '5px',
                    'position': 'sticky',
                    'bottom': '0',
                    'z-index': '1',
                })
        ])

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

        if area[0].isdigit():
            y_title = 'Disponible ou non dans la ville'
        else:
            y_title = 'Disponible dans (x%) des villes'

        fig.update_layout(
            xaxis_title=None,
            yaxis_title=y_title,
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

    def display_text_info(self, area):
        area_data = self.get_data_from_area(area)
        avg_area_price = area_data[self.fuel_columns].mean()
        area_stations_count = area_data['Nombre de stations'].sum()

        national_data = self.get_data_from_area('France')
        avg_prices_national = national_data[self.fuel_columns].mean()
        national_cs_count = self.data_frame['cp_ville'].nunique()
        national_stations_count = national_data['Nombre de stations'].sum()

        text_info_list = []

        for fuel in self.fuel_columns:
            price = avg_area_price[fuel]
            if pd.notna(price):
                price_text = (html.Span(
                    fuel,
                    style={'font-weight': 'bold', 'color': 'black'}),
                              html.Span(
                                  f' : {price:.3f} €/L')
                )
                price_diff_text = None
                color = 'black'

                if area != 'France':
                    price_diff = (round(price, 3)
                                  - round(avg_prices_national[fuel], 3))
                    price_diff_text = f'({price_diff:+.3f})'

                    if price_diff == 0:
                        price_diff_text = '(-.---) ='
                        color = 'grey'
                    elif price_diff > 0:
                        price_diff_text += ' ▲'
                        color = 'red'
                    else:
                        price_diff_text += ' ▼'
                        color = 'green'

            else:
                price_text = (html.Span(
                    fuel,
                    style={'font-weight': 'bold', 'color': 'black'}),
                              html.Span(f' : Non disponible')
                )
                price_diff_text = None
                color = 'grey'

            text_info_list.append(html.Li(
                [
                    html.Span(price_text),
                    html.Span(
                        price_diff_text,
                        style={'color': color}
                    ) if price_diff_text else None
                ]
            ))

        if area in self.reg:
            area_cs_count = (self.data_frame.groupby('Région')['cp_ville']
                             .nunique())[area]
            color = 'grey'
        elif area in self.dep:
            area_cs_count = (self.data_frame.groupby('Département')['cp_ville']
                             .nunique())[area]
            color = 'grey'
        elif area[0].isdigit():
            area_cs_count = 1
            color = 'white'
        else:
            area_cs_count = self.data_frame['cp_ville'].nunique()
            color = 'grey'

        area_stations_rate = (
                    area_stations_count / national_stations_count * 100)
        area_cs_rate = (area_cs_count / national_cs_count * 100)

        text_info_list.append(
                html.Div(
                    [
                        html.Br(),
                        html.Span(f'Nombre de villes avec stations : ',
                                  style={'color': color}),
                        html.Br(),
                        html.Span(f'{area_cs_count} ⇔ ({area_cs_rate:.2f}%)',
                                  style={'color': color}),
                        html.Br(),
                        html.Span(f'Nombre de stations : ',
                                  style={'color': 'grey'}),
                        html.Br(),
                        html.Span(f'{area_stations_count} ⇔ ('
                                  f'{area_stations_rate:.2f}%)',
                                  style={'color': 'grey'})
                    ],
                    style={'font-size': '12px'})
        )

        return html.Ul(text_info_list)

    @staticmethod
    def set_title(title_text):
        return html.H1(title_text,
                       style={
                           'text-align': 'center',
                           'margin-bottom': '20px',
                           'font-weight': 'bold',
                           'text-decoration': 'underline',
                           'font-family': 'Roboto, sans-serif'
                       })

    @staticmethod
    def set_date(update_date):
        return html.Div(f"Dernière mise à jour des données : {update_date}",
                        style={'text-align': 'right', 'font-size': '20px',
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
        title_style = {
            'text-align': 'center',
            'text-decoration': 'underline',
            'font-size': '10px'
        }
        if area == 'France':
            text_title = 'Prix moyens sur le territoire français métropolitain'
            text_graph = ('Distribution des carburants sur le territoire '
                          'français métropolitain')
        else:
            text_title = 'Prix et différences moyennes avec la France'
            text_graph = ('Distribution des carburants et différences moyennes '
                          'avec la France')

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
                    html.Div(html.H5(text_title, style=title_style)),
                    html.Div(self.display_text_info(area)),

                    html.Hr(),

                    html.Div(html.H5(text_graph, style=title_style)),
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
            body_content = dcc.Graph(figure=generate_static_graph, )
        return dbc.Card(
            dbc.CardBody(body_content)
        )

    @staticmethod
    def create_whitespace(space):
        return html.Div(style={'margin-bottom': f'{space}px'})

    def from_reg_get_dep(self, reg):
        filtered_data = self.data_frame.query(f'Région == "{reg}"')
        departments = filtered_data['Département'].unique().tolist()
        return departments

    def from_dep_get_cities(self, dep):
        filtered_data = self.data_frame.query(f'Département == "{dep}"')
        cities = filtered_data['cp_ville'].unique().tolist()
        return cities

    @staticmethod
    def create_switch_button(button_switch):
        """
        Creates a switch button inside a card using Dash Bootstrap Components.

        Args:
            button_switch (str): The ID of the switch button.

        Returns:
            dbc.Card: The card component containing the switch button.
        """
        options = [
            {'label': 'Verrouiller', 'value': 'Verrouiller'},
            {'label': 'Déverrouiller', 'value': 'Déverrouiller'}
        ]

        return dbc.Col(
            dcc.RadioItems(
                id=button_switch,
                options=options,
                value=options[0]['value'],
                labelStyle={'display': 'flex'},
                style={'margin-top': '10px', 'margin-bottom': '10px'}
            ), md=3
        )


if __name__ == '__main__':
    price_columns_list = ['Gazole', 'SP98', 'SP95',
                          'E85', 'E10', 'GPLc']
    date = 'date test'
    df = pd.read_csv('processed_data.csv')
    dashboard = DashboardHolder(df, price_columns_list, date)
    dashboard.app.run_server(debug=True)
