# Import some librairies
from tkinter import messagebox
from pathlib import Path
import pandas as pd


class DataFrameHolder:
    """
    A class to hold and process a DataFrame for E4 python projet at ESIEE PARIS.

    :param:
        current_dir (Path): The current directory path.
        df (pd.DataFrame): The DataFrame to be processed.
        price_columns (list): List of column names containing price information.
    """

    def __init__(self, file_name):
        """
        Initializes a DataFrameHolder object.

        :param:
            file_name (str): The name of the CSV file to be opened.
        """
        # Set the current file directory for opening and saving file
        self.current_dir = Path(__file__).resolve().parent
        # Set a dataframe for further processes
        self.df = self.load_csv_file(file_name)
        # Set the fuels
        self.price_columns = ['Gazole_prix', 'SP98_prix', 'SP95_prix', 'E85_prix', 'E10_prix', 'GPLc_prix']

    def load_csv_file(self, file_name):
        """
        Loads a CSV file from the 'fetcher' directory.

        :param:
            file_name (str): The name of the CSV file to be loaded.

        :return:
            pd.DataFrame or None: If successful, returns a DataFrame with the CSV data.
                                 If an error occurs, returns None and displays an error message.
        """
        # Retrieve the upper directory and go in the fetcher directory
        csv_path = self.current_dir.parent / 'fetcher' / file_name
        # Errors handling, we try to open the file, if we got an error print it in a box (with tk)
        try:
            return pd.read_csv(csv_path, dtype={'Code postal': 'object'}, delimiter=';')
        except FileNotFoundError:
            messagebox.showerror("Error", f"The file '{csv_path}' was not found.")
            return None
        except pd.errors.EmptyDataError:
            messagebox.showerror("Error", f"The file '{csv_path}' is empty.")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while opening the file: {e}")
            return None

    def process_data(self):
        """
        Processes the data by performing data cleaning and computing a new DataFrame.
        """
        # First we need to clean csv data
        self._data_cleaning()
        # Then we can apply our different processes
        self._compute_new_dataframe()

    def _data_cleaning(self):
        """
        Performs data cleaning operations on the DataFrame.
        """
        useful_columns = ['Région', 'Département', 'Code postal', 'Ville', 'geom'] + self.price_columns

        # We do not need the others columns for our application
        self.df = self.df[useful_columns]
        # We need unique key to perform grouping (ville is not sufficient, can have same names in different area)
        self.df['cp_ville'] = self.df['Code postal'] + ' ' + self.df['Ville']
        # Then we do not have use of these
        self.df = self.df.drop(columns=['Ville', 'Code postal'])
        # There are data without specify (Région, département, Ville) so we delete these
        self.df = self.df.dropna(subset=['Région'])
        # Split geom and floating them to have latitude and longitude for further application
        self.df['geom'] = self.df['geom'].apply(lambda x: [float(coord) for coord in x.split(', ') if coord])

    def _compute_new_dataframe(self):
        """
        Computes a new DataFrame by performing various operations.
        """
        # Mapping to have region and department linked to each city
        city_geo_mapping = self.df.groupby('cp_ville')[['Région', 'Département']].first().reset_index()

        # Performing the average prices for each city
        city_prices_means = self.df.groupby('cp_ville')[self.price_columns].mean().reset_index()

        # Performing the average coordinates for each city
        city_coords_means = pd.Series((self.df.groupby('cp_ville')['geom'])
                                      .apply(lambda x: self._mean_coords(x)), name='geom')

        # Count how many times a city appears
        city_app_count = self.df.groupby('cp_ville').size().reset_index(name='Apparition')

        # merge all results to have one dataframe
        self.df = (city_geo_mapping.merge(city_prices_means, on='cp_ville')
                                   .merge(city_coords_means, on='cp_ville')
                                   .merge(city_app_count, on='cp_ville'))

    @staticmethod
    def _mean_coords(coords_list):
        """
        Computes the mean of latitude and longitude from a list of coordinates.

        :param:
            coords_list (list): List of coordinates.

        :return:
            tuple: Mean latitude and mean longitude.
        """
        # Retrieves the latitudes and longitudes
        latitudes = [coord[0] for coord in coords_list if coord]
        longitudes = [coord[1] for coord in coords_list if coord]
        # return coordinates tuple
        return sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)

    def save_processed_dataframe(self):
        """
        Saves the processed DataFrame to a CSV file.
        """
        # Get the visualizer directory to save processed data
        target_dir = self.current_dir.parent / 'visualizer'
        # Look if exists, if not create it
        if not target_dir.is_dir():
            target_dir.mkdir()

        # Errors handling, we try to save the file, if we got an error print it in a box (with tk)
        try:
            file_path = target_dir / 'processed_data.csv'
            self.df.to_csv(file_path, index=False)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
