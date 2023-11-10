"""
    Module that allows to display our information on the dashboard
"""

import dash
import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
from folium.plugins import MarkerCluster


class DashboardHolder:
    """
    Initialize the DashboardHolder class.

    This class serves as a container for creating and managing a Dash dashboard.
    It takes a DataFrame containing fuel price data, a list of price columns,
    and the last update date as input parameters. The constructor initializes
    the dashboard and sets up its layout, validation layout, and callbacks.

    Args:
        dataframe (pd.DataFrame): A DataFrame containing fuel price data.

        price_columns (list): A list of price columns to display.

        lud (str): The last update date of the data.
    """
    def __init__(self, dataframe, price_columns, lud):
        self.data_frame = dataframe
        self.fuel_columns = price_columns
        self.last_update_date = lud
        self.app = dash.Dash(__name__,
                             external_stylesheets=[dbc.themes.LUX],
                             )
        self.dep = dataframe['Département'].unique()
        self.reg = dataframe['Région'].unique()
        self.reg_color_mapping = self._generate_color_mapping(self.reg)
        self._setup_layout()
        self._setup_validation_layout()
        self._register_callbacks()

    def run(self):
        """
            run the dashboard
        """
        print('server running...')
        self.app.run_server()

    def _setup_layout(self):
        """
        Set up the layout for the Dash application by defining the structure
        of the web page. It creates the navigation bar, page content area,
        and footer for the dashboard.
        """
        self.app.layout = html.Div(
            [
                dcc.Location('url', refresh=False),
                self._setup_navbar(),

                html.Div(
                    id='page-content',
                    children=[],
                    className='page-style',
                ),

                self._setup_footer(),
            ],
            className='setup'
        )

    def _setup_validation_layout(self):
        """
        This method configures the validation layout for the Dash application.
        It includes a navigation bar, page content, and initializes the default
        layout for the home, histogram, map, and link pages. The validation
        layout is used to unsure a consistent and well-structured application
        layout. But also to avoid callbacks error.
        """
        self.app.validation_layout = html.Div([
            html.Div(
                [
                    dcc.Location(id="url", refresh=False),
                    self._setup_navbar(),
                    self._create_whitespace(10),
                    html.Div(id="page-content", children=[])
                ],
                className='navbar'
            ),
            self._setup_layout_home(),
            self._setup_layout_distribution(),
            self._setup_layout_map(),
            self._setup_layout_link()
        ])

    def _register_callbacks(self):
        """
        Register callbacks for the Dash application.

        Returns:
            None
        """
        @self.app.callback(
            [Output(f'{area}-card', 'children')
             for area in ['reg', 'dep', 'cit']],
            [Input(f'{area}-dropdown', 'value')
             for area in ['reg', 'dep', 'cit']]
        )
        def update_area_card(*selected_areas):
            """
            This callback function updates the area cards based on the selected
            geographic areas. It takes the selected areas as inputs and returns
            the corresponding area cards for display.

            Args:
                *selected_areas (str): Variable number of areas for
                generating the area cards.

            Returns:
                list: A list of area cards for display.
            """
            return [self._generate_area_card(area) for area in selected_areas]

        @self.app.callback(
            [Output(f'fuel-{i}-card', 'children')
             for i in ['1', '2', '3']],
            [Input(f'fuel-{i}-dropdown', 'value')
             for i in ['1', '2', '3']]
        )
        def update_fuel_card(*selected_fuels):
            """
            This callback function updates the fuel cards based on the selected
            fuel types. It takes the selected fuel types as inputs and returns
            the corresponding fuel cards for display.

            Args:
                *selected_fuels (str): Variable number of selected fuel types
                for generating the fuel cards.

            Returns:
                list: A list of fuel cards for display.
            """
            return [self._generate_fuel_card(fuel) for fuel in selected_fuels]

        @self.app.callback(
            Output('histogram-plot', 'figure'),
            [Input('fuel-dropdown', 'value')]
        )
        def update_histogram(fuel_selected):
            """
            This callback function updates the price histogram plot based on the
             selected fuel type. It takes the selected fuel type as an input
             and returns a new histogram figure with updated data.

            Args:
                fuel_selected (str): The selected fuel type for generating the
                price histogram.

            Returns:
                plotly.graph_objs.Figure: A Plotly figure representing the
                updated price histogram plot.
            """
            return self._generate_price_histogram(fuel_selected)

        @self.app.callback(
            Output('dep-dropdown', 'options'),
            [Input('reg-dropdown', 'value'),
             Input('switch-button', 'value')]
        )
        def update_dep_dropdown(reg, switch):
            if switch == 'Verrouiller':
                dep_list = self._from_reg_get_dep(reg)
            else:
                dep_list = self.data_frame['Département'].unique()

            return [{'label': dep, 'value': dep} for dep in dep_list]

        @self.app.callback(
            Output('cit-dropdown', 'options'),
            [Input('dep-dropdown', 'value'),
             Input('switch-button', 'value')]
        )
        def update_cit_dropdown(dep, switch):
            if switch == 'Verrouiller':
                cities_list = self._from_dep_get_cities(dep)
            else:
                cities_list = self.data_frame['cp_ville'].unique()

            return [{'label': cit, 'value': cit} for cit in cities_list]

        @self.app.callback(
            Output('dep-dropdown', 'value'),
            [Input('dep-dropdown', 'options')]
        )
        def set_default_dep_value(options):
            """
            This callback function sets the default value for the department
            dropdown based on the available options. If there are options
            available, it selects the first option as the default value.

            Args:
                options (list): The list of available options for the department
                 dropdown.

            Returns:
                str or None: The default value for the department dropdown, or
                None if there are no options.
            """
            if options:
                return options[0]['value']
            return None

        @self.app.callback(
            Output('cit-dropdown', 'value'),
            [Input('cit-dropdown', 'options')]
        )
        def set_default_cit_value(options):
            """
            This callback function sets the default value for the city dropdown
            based on the available options. If there are options available, it
            selects the first option as the default value.

            Args:
                options (list): The list of available options for the city
                dropdown.

            Returns:
                str or None: The default value for the city dropdown, or None if
                 there are no options.
            """
            if options:
                return options[0]['value']
            return None

        @self.app.callback(
            Output('page-content', 'children'),
            [Input('url', 'pathname')]
        )
        def render_page_content(pathname):
            """
            This callback function updates the content displayed on the web
            application based on the URL pathname. It maps different URL
            paths to specific layout functions, allowing users to navigate
            between different sections of the application.

            Args:
                pathname (str): The URL pathname, which determines the content
                to be displayed.

            Returns:
                dash.development.base_component.Component: The content to be
                displayed on the page.
            """
            if pathname == '/distribution':
                return self._setup_layout_distribution()
            if pathname == '/carte':
                return self._setup_layout_map()
            if pathname == '/comparaisons':
                return self._setup_layout_link()
            return self._setup_layout_home()

    def _generate_folium_map(self):
        """
        Generate a Folium map with a MarkerCluster for city markers.

        Returns:
            html.Iframe: An HTML iframe containing the rendered Folium map.
        """
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

        marker_cluster = MarkerCluster().add_to(map1)
        markers = self._get_city_markers()

        for marker in markers:
            marker.add_to(marker_cluster)

        folium_map_html = map1.get_root().render()
        return html.Iframe(srcDoc=folium_map_html,
                           className='folium-iframe-style')

    def _get_city_markers(self):
        """
        Get a list of Folium Markers for cities with popup information.

        Returns:
            list: List of Folium Markers.
        """
        locations = self.data_frame[['Latitude', 'Longitude']].values
        popup_contents = self.data_frame.apply(self._get_city_popup_content,
                                               axis=1).tolist()

        markers = [
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=300)
            )
            for (lat, lon), popup_content in zip(locations, popup_contents)
        ]
        return markers

    def _get_city_popup_content(self, row):
        """
        Generate popup content for a city marker.

        Args:
            row (pd.Series): A row from the DataFrame containing city information.

        Returns:
            str: Popup content in HTML format.
        """
        popup_title = f"<h4>{row['cp_ville']}</h4>"

        popup_fuel = [
            f"<b>{col}:</b> {row[col]:.3f}€/L<br>" if pd.notna(row[col]) else
            f"<b>{col}:</b> <span style='color:red;'>Non disponible</span><br>"
            for col in self.fuel_columns
        ]

        popup_stations_count = f"<br><b>Nombre de stations:</b> {row['Nombre de stations']}"

        return f"{popup_title}<br>{''.join(popup_fuel)}{popup_stations_count}"

    def _generate_price_histogram(self, selected_fuel='Gazole'):
        """
        Generate a price histogram chart showing the distribution of prices for
        a selected fuel type in France. The chart includes a specified number of
         bins to display the data.

        Args:
            selected_fuel (str): The fuel type for which the price histogram
            will be generated.

        Returns:
            plotly.graph_objs._figure.Figure: A Plotly figure representing the
            generated price histogram.
        """
        histogram_fig = px.histogram(
            self.data_frame,
            x=selected_fuel,
            title=f"Histogramme des prix en France du {selected_fuel}",
            labels={selected_fuel: f"Prix du {selected_fuel} en €"}
        )

        histogram_fig.update_traces(
            marker={'line': {'width': 1, 'color': 'Blue'}},
            xbins_size=0.05
        )

        return histogram_fig

    @staticmethod
    def _generate_color_mapping(list_to_map):
        """
            Generate a color mapping that associates a unique color with each
            item in a list. The colors are selected from a predefined color
            scale.

            Args:
                list_to_map (list): A list of items to be mapped to colors.

            Returns:
                dict: A dictionary mapping items in the list to unique colors.
            """
        color_mapping = {}
        color_scale = px.colors.qualitative.Light24_r
        for i, items in enumerate(list_to_map):
            color_mapping[items] = color_scale[i]
        return color_mapping

    @staticmethod
    def _generate_pie_chart(dataframe, names_column, values_column,
                            title, color_mapping):
        """
        Generate a pie chart based on DataFrame data showing the distribution of
         values in a specified column. It allows customization of the chart
         title, color mapping, and other visual aspects.

        Args:
            dataframe (pandas.DataFrame): The DataFrame containing the data for
            the pie chart.

            names_column (str): The column in the DataFrame representing the
            names of the pie chart slices.

            values_column (str): The column in the DataFrame representing the
            values of the pie chart slices.

            title (str): The title of the pie chart.

            color_mapping (dict): A dictionary mapping names to colors for
            slices.

        Returns:
            plotly.graph_objs._figure.Figure: A Plotly figure representing the
            generated pie chart.
        """
        fig = px.pie(
            dataframe,
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
    def _setup_navbar():
        """
        Set up the navigation bar for the web page with links to different
        sections, including links to different sections or pages. The
        navigation bar typically allows users to navigate to various parts of
        the web application.

        Returns:
            dash.development.base_component.Component: A Dash component
            representing the navigation bar.
        """
        return dbc.Nav([
            dbc.NavLink("Accueil", href="/", active="exact"),
            dbc.NavLink("Distribution", href="/distribution", active="exact"),
            dbc.NavLink("Données Géolocalisées", href="/carte", active="exact"),
            dbc.NavLink("Comparaisons rapides", href="/comparaisons",
                        active="exact"),
        ],
            horizontal=True,
            pills=True,
        )

    def _setup_layout_home(self):
        """
        Set up the home layout for the web page with fuel prices and
        distribution by city, including creating a header card with the title
        and date, switch buttons for changing the view, dropdowns for
        selecting region, department, and city, and cards for displaying fuel
        prices and distribution by city.

        Returns:
            list: A list of Dash components representing the home layout of the
            web page.
        """
        return [
            dbc.Card(
                [
                    dbc.CardBody([
                        self._set_title(
                            'Prix et répartition des carburants par ville en '
                            'France métropolitaine'),

                        html.Div(self._set_date(self.last_update_date)),
                    ])
                ],
                className='header-box'
            ),

            self._create_whitespace(5),

            html.Div([
                dbc.Row([
                    self._create_switch_button('switch-button'),
                    self._create_dropdown('Sélectionnez la région :',
                                          self.data_frame['Région'], 'reg'),
                    self._create_dropdown('Sélectionnez le département :',
                                          self.data_frame['Département'],
                                          'dep'),
                    self._create_dropdown('Sélectionnez la ville :',
                                          self.data_frame['cp_ville'], 'cit')
                ]),

                self._create_whitespace(10),

                dbc.Row([
                    html.Div(self._generate_area_card('France'),
                             className='area-card-home'),
                    html.Div(id='reg-card',
                             className='area-card-home'),
                    html.Div(id='dep-card',
                             className='area-card-home'),
                    html.Div(id='cit-card',
                             className='area-card-home')
                ]),
            ]),
        ]

    def _setup_layout_distribution(self):
        """
        Set up the layout for the web page with histograms and pie charts,
        including creating a header card with the title and date, histograms
        for fuel distribution, and pie charts showing the distribution of
        stations by region and cities per region.

        Returns:
            list: A list of Dash components representing the layout of the web
            page.
        """
        return [
            dbc.Card(
                [
                    dbc.CardBody([
                        self._set_title(
                            'Distribution des stations essence en France'),

                        html.Div(self._set_date(self.last_update_date)),
                    ])
                ],
                className='header-box'
            ),

            self._create_whitespace(5),

            # Histogram
            dbc.Col([
                self._create_dropdown('Sélectionnez le carburant :',
                                      self.fuel_columns, 'fuel'),
                self._create_graph_card(True, 'histogram-plot')
            ]),

            self._create_whitespace(10),

            dbc.Col([
                # Regional Pie Chart
                self._create_graph_card(
                    False,
                    generate_static_graph=self._generate_pie_chart(
                        self.data_frame,
                        'Région',
                        'Nombre de stations',
                        'Distribution des Stations par Région',
                        self.reg_color_mapping
                    ),
                ),

                self._create_whitespace(10),

                # Departmental Pie Chart
                self._create_graph_card(
                    False,
                    generate_static_graph=self._generate_pie_chart(
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

    def _setup_layout_map(self):
        """
        Set up the layout for the web page with a map displaying fuel station
        distribution and prices including creating a header card with the
        title and date, and a map displaying the distribution of fuel
        stations in France by city and fuel prices.

        Returns:
            list: A list of Dash components representing the layout of the web
            page.
        """
        return [
            dbc.Card(
                [
                    dbc.CardBody([
                        self._set_title(
                            'Répartition des stations en France par ville'
                            ' et prix des carburants'),

                        html.Div(self._set_date(self.last_update_date)),
                    ])
                ],
                className='header-box'
            ),

            self._create_whitespace(5),

            html.Div(self._generate_folium_map())
        ]

    def _setup_layout_link(self):
        """
        Set up the layout for the web page with data relationships and
        dropdowns. Including creating a header card with the title and date,
        dropdowns for selecting fuel types, and card placeholders for displaying
         data relationships.

        Returns:
            list: A list of Dash components representing the layout of the web
            page.
        """
        return [
            dbc.Card(
                [
                    dbc.CardBody([
                        self._set_title('Relation entre les données'),
                        html.Div(self._set_date(self.last_update_date)),
                    ])
                ],
                className='header-box'
            ),

            self._create_whitespace(5),

            html.Div([
                dbc.Row([
                    dbc.Col(self._create_dropdown('Sélectionnez le carburant :',
                                                  self.fuel_columns, 'fuel-1',
                                                  'Gazole')),
                    dbc.Col(self._create_dropdown('Sélectionnez le carburant :',
                                                  self.fuel_columns, 'fuel-2',
                                                  first_value='SP98')),
                    dbc.Col(self._create_dropdown('Sélectionnez le carburant :',
                                                  self.fuel_columns, 'fuel-3',
                                                  first_value='SP95')),
                ]),

                self._create_whitespace(5),

                dbc.Row([
                    dbc.Col(id='fuel-1-card', md=4, style={'padding': '10'}),
                    dbc.Col(id='fuel-2-card', md=4, style={'padding': '10'}),
                    dbc.Col(id='fuel-3-card', md=4, style={'padding': '10'}),
                ])
            ])
        ]

    def _setup_footer(self):
        """
        Create a footer for the web page with copyright and attribution
        information.

        Returns:
            dash.html.Footer: An HTML <footer> element with copyright and
            attribution information.
        """
        return html.Footer([
            html.Div([
                # Logo Université Gustave Eiffel
                html.Img(
                    src=self.app.get_asset_url('logo_univ.png'),
                    className='logo'
                ),

                # Copyright
                html.Div(
                    'Copyright © 2023 / 2024',
                    className='copyright'
                ),

                # Credits
                html.Div(
                    'CARANGEOT Hugo / SALI--ORLIANGE Lucas, encadrés par '
                    'Monsieur COURIVAUD D.',
                    className='credits'
                ),

                # Unit
                html.Div(
                    'DSIA-4101A : Python pour la Data Science',
                    className='unit'
                ),

                # Logo ESIEE Paris
                html.Img(
                    src=self.app.get_asset_url('logo_esiee.png'),
                    className='logo'
                ),
            ], className='footer')
        ])

    def _get_data_from_area(self, area):
        """
        Retrieves and returns a subset of the dataset, filtering it by a
        specific geographic area. The area can be defined by its name,
        which could be a region, department, or "France" for the entire country.

        Args:
            area (str): The name of the geographic area for which to retrieve
            data.

        Returns:
            pandas.DataFrame: A DataFrame containing the data filtered by the
            specified area.
        """
        if area != 'France':
            if area[0].isdigit():
                area_query = 'cp_ville'
            elif area in self.reg:
                area_query = 'Région'
            else:
                area_query = 'Département'
            return self.data_frame.query(f'{area_query} == "{area}"')

        return self.data_frame

    def _generate_average_barchart(self, area):
        """
        Generate a bar chart comparing the percentage of fuel availability
        in a specific area to the national average. It displays both the
        area's percentage and the difference (if any) from the national average.

        Args:
            area (str): The name of the geographic area for which to generate
            the bar chart.

        Returns:
            plotly.graph_objs._figure.Figure: A Plotly figure representing the
            bar chart.
        """
        data = self._get_data_from_area(area)
        national_data = self._get_data_from_area('France')

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

        for _, row in merged_percentage.iterrows():
            diff = round(row['area_per'] - row['nat_per'])

            if diff == 0:
                continue
            if diff > 0:
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

    def _display_fuel_info(self, fuel):
        """
        Generate information about fuel prices in regions and departments.
        Creates a list of HTML elements that provide information about fuel
        prices in the specified regions and departments. It includes the top
        5 and bottom 5 regions/departments with the highest and lowest fuel
        prices.

        Args:
            fuel (str): The type of fuel to display information for.

        Returns:
            dash.html.Ul: An HTML <ul> element containing the information about
            fuel prices.
        """
        list_area = ['Région', 'Département']

        text_fuel_list = []

        for area in list_area:
            avg_fuel_price = (self.data_frame
                              .groupby(area)[fuel]
                              .mean()
                              .reset_index())
            top_5 = (avg_fuel_price.nlargest(5, fuel)
                     .sort_values(by=fuel, ascending=False))
            min_5 = (avg_fuel_price.nsmallest(5, fuel)
                     .sort_values(by=fuel, ascending=True))

            text_fuel_list.extend([
                html.H5(
                    f'5 {area}s les plus chères' if area == 'Région'
                    else f'5 {area}s les plus chers',
                    className='card-body-title'
                ),

                html.Ol([
                    html.Li(
                        [
                            html.Span(f"{row[1][area]} : ",
                                      className='span-text-info'
                                      ),
                            f"{row[1][fuel]:.3f} €/L"
                        ]
                    )
                    for row in top_5.iterrows()
                ], className='font12'
                ),

                html.Hr(),

                html.H5(
                    f'5 {area}s les moins chères' if area == 'Région'
                    else f'5 {area}s les moins chers',
                    className='card-body-title'),

                html.Ol([
                    html.Li(
                        [
                            html.Span(f"{row[1][area]} : ",
                                      className='span-text-info'
                                      ),
                            f"{row[1][fuel]:.3f} €/L"
                        ]
                    )
                    for row in min_5.iterrows()
                ], className='font12'
                )
            ])

            if area == 'Région':
                text_fuel_list.append(
                    html.Hr()
                )

        return html.Ul(text_fuel_list)

    def _display_text_info(self, area):
        """
        Generate a list of HTML elements containing information about a
        specific geographic area. It provides information about a specified
        geographic area, including average fuel prices, price differences
        with the national average, city and station counts, and related data.

        Args:
            area (str): The name of the geographic area for which information
            is to be displayed.

        Returns:
            dash.html.Ul: An HTML <ul> element containing the information about
            the area.
        """
        area_data = self._get_data_from_area(area)
        avg_area_price = area_data[self.fuel_columns].mean()
        area_stations_count = area_data['Nombre de stations'].sum()

        national_data = self._get_data_from_area('France')
        avg_prices_national = national_data[self.fuel_columns].mean()
        national_cs_count = self.data_frame['cp_ville'].nunique()
        national_stations_count = national_data['Nombre de stations'].sum()

        text_info_list = []

        for fuel in self.fuel_columns:
            price = avg_area_price[fuel]
            if pd.notna(price):
                price_text = (
                    html.Span(fuel, className='span-text-info'),
                    html.Span(f' : {price:.3f} €/L')
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
                price_text = (
                    html.Span(fuel, className='span-text-info'),
                    html.Span(' : Non disponible')
                )

                price_diff_text = None
                color = 'grey'

            text_info_list.append(
                html.Li(
                    [
                        html.Span(price_text),
                        html.Span(price_diff_text, style={'color': color}) if
                        price_diff_text else None
                    ]
                )
            )

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
        area_cs_rate = area_cs_count / national_cs_count * 100

        text_info_list.append(
            html.Div(
                [
                    html.Br(),
                    html.Span('Nombre de villes avec stations : ',
                              style={'color': color}),

                    html.Br(),
                    html.Span(f'{area_cs_count} ⇔ ({area_cs_rate:.2f}%)',
                              style={'color': color}),

                    html.Br(),
                    html.Span('Nombre de stations : ', className='span-color'),

                    html.Br(),
                    html.Span(f'{area_stations_count} ⇔ ('
                              f'{area_stations_rate:.2f}%)',
                              className='span-color')
                ],
                className='font12')
        )

        return html.Ul(text_info_list)

    @staticmethod
    def _set_title(title_text):
        """
        Create an H1 element to display the main title.

        Args:
            title_text (str): The text to display as the main title.

        Returns:
            dash.html.H1: An HTML <h1> element with the specified title text.
        """
        return html.H1(title_text,
                       className='main-title',
                       )

    @staticmethod
    def _set_date(update_date):
        """
        Create a Div element to display the last data update date.

        Args:
            update_date (str): The date to display as the last data update date.

        Returns:
            dash.html.Div: An HTML <div> element with the specified update date.
        """
        return html.Div(f"Dernière mise à jour des données : {update_date}",
                        className='date'
                        )

    @staticmethod
    def _create_dropdown(ptext, plist, id_dropdown, first_value=None):
        """
        This function generates a Dash Dropdown component for selecting options
         from a list.

        Args:
            ptext (str): The label or text to display next to the dropdown.

            plist (pd.Series or iterable): The list of options to populate the
            dropdown.

            id_dropdown (str): The ID to assign to the dropdown.

            first_value (str or None, optional): The default selected value for the
            dropdown. If None, the first option is selected.

        Returns:
            dash.development.web.Dropdown: A Dash Dropdown component with the
            specified label, options, and ID.
        """
        if not isinstance(plist, pd.Series):
            plist = pd.Series(plist)
        if first_value is None:
            first_value = plist.unique()[0]
        column = 3
        if id_dropdown.split('-')[0] == 'fuel' and first_value is not None:
            column = 12

        return dbc.Col(
            [
                html.Label(ptext),
                dcc.Dropdown(
                    id=f'{id_dropdown}-dropdown',
                    options=[{'label': element, 'value': element}
                             for element in plist.unique()],
                    value=first_value,
                    clearable=False
                ),
            ], md=column
        )

    def _generate_fuel_card(self, fuel):
        """
        Generate a card component displaying information for a specific
        fuel, including a title, data.

        Args:
            fuel (str): The name of the fuel to display information
            for.

        Returns:
            dash_bootstrap_components.Card: A card component containing
            information.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    html.H5(fuel,
                            className='font12'
                            ),
                    className='card-header'
                ),

                dbc.CardBody([
                    self._display_fuel_info(fuel)
                ],
                    className='card-body-fuel'
                )
            ],
            className='card-style',
        )

    def _generate_area_card(self, area):
        """
        Generate a card component displaying information for a specific
        geographic area, including a title, data, and a Plotly graph.

        Args:
            area (str): The name of the geographic area to display information
            for.

        Returns:
            dash_bootstrap_components.Card: A card component containing
            information and a graph.
        """
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
                            className='font12'),
                    className='card-header'
                ),

                dbc.CardBody([
                    html.Div(html.H5(text_title,
                                     className='card-body-title')
                             ),

                    html.Div(self._display_text_info(area)),

                    html.Hr(),

                    html.Div(html.H5(text_graph,
                                     className='card-body-title')
                             ),

                    dcc.Graph(
                        figure=self._generate_average_barchart(area),
                        config={'displayModeBar': False}
                    )
                ])
            ],
            className='card-style',
        )

    @staticmethod
    def _create_graph_card(callback, graph_id=None,
                           generate_static_graph=None):
        """
        Create a card containing a Plotly graph component.

        Args:
            callback (bool): If True, the graph component will have an ID
            specified by 'graph_id'.

            graph_id (str, optional): The ID to assign to the graph component
            when 'callback' is True.

            generate_static_graph (plotly.graph_objs.Figure, optional): The
            static Plotly graph to display when 'callback' is False.

        Returns:
            dash_bootstrap_components.Card: A card containing the specified
            graph component.
        """
        if callback:
            body_content = dcc.Graph(id=graph_id)
        else:
            body_content = dcc.Graph(figure=generate_static_graph, )
        return dbc.Card(
            dbc.CardBody(body_content)
        )

    @staticmethod
    def _create_whitespace(space):
        """
        Create a whitespace element with a specified margin-bottom in pixels.

        Args:
            space (int): The amount of margin-bottom (in pixels) to add to
            the whitespace element.

        Returns:
            dash.html.Div: An HTML <div> element with the specified
            margin-bottom.
        """
        return html.Div(style={'margin-bottom': f'{space}px'})

    def _from_reg_get_dep(self, reg):
        """
        Retrieve a list of unique departments in a specified French region.

        Args:
            reg (str): French region to filter the data.

        Returns:
            list : A list of unique French departments in the specified
            department.
        """
        filtered_data = self.data_frame.query(f'Région == "{reg}"')
        departments = filtered_data['Département'].unique().tolist()
        return departments

    def _from_dep_get_cities(self, dep):
        """
        Retrieve a list of unique cities in a specified French department.

        Args:
            dep (str): French department to filter the data.

        Returns:
            cities : A list of unique French cities in the specified department.
        """
        filtered_data = self.data_frame.query(f'Département == "{dep}"')
        cities = filtered_data['cp_ville'].unique().tolist()
        return cities

    @staticmethod
    def _create_switch_button(button_switch):
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
                className='radio-items',
            ), md=3
        )
