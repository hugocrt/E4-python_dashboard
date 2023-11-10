"""
    Module providing methods on our specific dataframe
"""
from tkinter import messagebox
from pathlib import Path
import pandas as pd


class DataFrameHolder:
    """
    A class to hold and process a DataFrame for the E4 Python project at ESIEE
    PARIS.

    Args:
        file_name (str): The name of the CSV file to be opened.
    """
    def __init__(self, file_name):
        """
        Initializes a DataFrameHolder object.

        Args:
            file_name (str): The name of the CSV file to be opened.
        """
        self.current_dir = Path(__file__).resolve().parent
        self._data_frame = self.load_csv_file(file_name)
        self._fuel_columns = ['Gazole_prix', 'SP98_prix', 'SP95_prix',
                              'E85_prix', 'E10_prix', 'GPLc_prix']

    @property
    def price_columns(self):
        """
        Get the fuel list.

        Returns:
            list of str: The list of fuels.
        """
        return self._fuel_columns

    @property
    def data_frame(self):
        """
        Get the DataFrame.

        Returns:
            pandas DataFrame: The DataFrame.
        """
        return self._data_frame

    def load_csv_file(self, file_name):
        """
        Loads a CSV file from the 'fetcher' directory.

        Args:
            file_name (str): The name of the CSV file to be loaded.

        Returns:
            pd.DataFrame or None: If successful, returns a DataFrame with the
            CSV data. If an error occurs, returns None and displays an error
            message.
        """
        # Navigate to the parent directory and access the "web_scraper"
        # directory.
        csv_path = self.current_dir.parent / 'web_scraper' / file_name

        # Errorshandling : we attempt to open the file, and if an error
        # occurs, display an error message through tkinter
        try:
            return pd.read_csv(csv_path, dtype={'Code postal': 'str'},
                               delimiter=';')
        except FileNotFoundError as exception:
            messagebox.showerror("Error", f"The file '{csv_path}' was not "
                                          f"found: {exception}")
            return None
        except pd.errors.EmptyDataError as exception:
            messagebox.showerror("Error", f"The file '{csv_path}' is empty: "
                                          f"{exception}")
            return None
        except Exception as exception:  # pylint: disable=broad-except
            messagebox.showerror("Error", f"An error occurred: {exception}")
            return None

    def process_data(self):
        """
        Processes the data by performing data cleaning and computing a new
        DataFrame.
        """
        print('wait for the data processing...')
        self._data_cleaning()
        self._compute_new_dataframe()

    def _data_cleaning(self):
        """
        Performs data cleaning operations on the DataFrame.
        """
        useful_columns = (['Région', 'Département', 'Code postal', 'Ville',
                           'geom'] + self.price_columns)

        self._data_frame = self._data_frame[useful_columns]
        self._data_frame['cp_ville'] = (self._data_frame['Code postal'] + ' '
                                        + self._data_frame['Ville'])
        self._data_frame = (self._data_frame.drop(
            columns=['Ville', 'Code postal']))

        self._data_frame = self._data_frame.rename(
            columns={fuel: fuel.split('_', maxsplit=1)[0] for fuel in
                     self._fuel_columns})

        # Delete data without specify (Région, département, Ville)
        self._data_frame = self._data_frame.dropna(subset=['Région'])
        self._fuel_columns = [col.split('_', maxsplit=1)[0] for col in self._fuel_columns]

        # Split geom and floating them to get latitude and longitude
        self._data_frame['geom'] = (
            self._data_frame['geom'].
            apply(
                lambda x: [float(coord) for coord in x.split(', ') if coord]))

    def _compute_new_dataframe(self):
        """
        Computes a new DataFrame by performing various operations.
        """
        # Mapping region and department linked to each city
        city_geo_mapping = (
            self._data_frame.groupby('cp_ville')[['Région', 'Département']]
            .first().reset_index())

        # Performing average prices per city
        city_prices_means = (
            self._data_frame.groupby('cp_ville')[self._fuel_columns].mean()
            .reset_index())

        # Performing the average coordinates per city
        city_coords_means = (self._data_frame.groupby('cp_ville')['geom']
                             .apply(self._mean_coords)
                             .reset_index(level=1, drop=True)
                             .reset_index())

        # Count occurrences per city
        city_app_count = (self._data_frame.groupby('cp_ville').size()
                          .reset_index(name='Nombre de stations'))

        # Merge all
        self._data_frame = (city_geo_mapping
                            .merge(city_prices_means, on='cp_ville')
                            .merge(city_coords_means, on='cp_ville')
                            .merge(city_app_count, on='cp_ville'))

    @staticmethod
    def _mean_coords(coords_list):
        """
        Computes the mean of latitude and longitude from a list of coordinates.

        Args:
            coords_list (list): List of coordinates.

        Returns:
            tuple: Mean latitude and mean longitude.
        """
        latitudes = [coord[0] for coord in coords_list if coord]
        longitudes = [coord[1] for coord in coords_list if coord]

        return pd.DataFrame({'Latitude': [sum(latitudes) / len(latitudes)],
                             'Longitude': [sum(longitudes) / len(longitudes)]})

    def save_dataframe(self, name='processed_data.csv'):
        """
        Saves the DataFrame to a CSV file.

        Args:
            name (str, optional): The name of the output CSV file.
        """
        # Get visualizer directory to save data
        target_dir = self.current_dir.parent / 'data_visualizer'

        if not target_dir.is_dir():
            target_dir.mkdir()

        # Error handling : we attempt to open the file, and if an error
        # occurs, display an error message through tkinter
        try:
            file_path = target_dir / name
            self._data_frame.to_csv(file_path, index=False)
        except Exception as exception:  # pylint: disable=broad-except
            messagebox.showerror("Error", f"An error occurred: {exception}")
