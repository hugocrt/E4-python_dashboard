from tkinter import messagebox
from pathlib import Path
import pandas as pd
from fetcher.data_fetcher import get_coordinates_from_city_names


class DataFrameHolder:
    def __init__(self, file_name):
        """
        Initializes a DataFrameHolder object.

        :param file_name: (str) The name of the CSV file to be opened.
        """
        self.current_dir = Path(__file__).resolve().parent
        self.df = self.load_csv_file(file_name)

    def load_csv_file(self, file_name):
        """
        Loads a CSV file from the 'fetcher' directory.

        :param file_name: (str) The name of the CSV file to be loaded.

        :return: pandas.DataFrame or None: If successful, returns a DataFrame with the CSV data.
                 If an error occurs, returns None and displays an error message.
        """
        csv_path = self.current_dir.parent / 'fetcher' / file_name
        try:
            return pd.read_csv(csv_path, sep=';')
        except FileNotFoundError:
            messagebox.showerror("Error", f"The file '{csv_path}' was not found.")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while opening the file: {e}")
            return None

    def process_data(self):
        """
        Processes the loaded DataFrame.

        This method performs several data processing tasks, including removing unused columns,
        converting price columns to numeric values, counting city occurrences, adding coordinates,
        and calculating average prices.
        """
        self._remove_unused_columns()
        self._convert_price_columns()
        self._count_city_occurrences()
        self._add_coordinates()
        self._calculate_average_prices()

    def _remove_unused_columns(self):
        """
        Removes unused columns from the DataFrame.

        This method removes columns that are not needed for further processing.
        """
        useful_columns = ['Code postal', 'Ville', 'Gazole_prix', 'SP95_prix', 'E85_prix',
                          'GPLc_prix', 'E10_prix', 'SP98_prix', 'Département', 'Région']
        self.df = self.df[useful_columns]

    def _convert_price_columns(self):
        """
        Converts price columns to numeric values.

        This method converts columns representing prices to numeric values and NaN if not a numeric for further analysis
        """
        price_columns = ['Gazole_prix', 'SP95_prix', 'E85_prix', 'GPLc_prix', 'E10_prix', 'SP98_prix']
        self.df[price_columns] = self.df[price_columns].apply(pd.to_numeric, errors='coerce')

    def _count_city_occurrences(self):
        """
        Counts the occurrences of each city.

        This method counts the number of occurrences of each city and adds it as a new column.
        """
        self.df['Nombre d\'occurrences'] = self.df['Ville'].value_counts().loc[self.df['Ville']].values

    def _add_coordinates(self):
        """
        Adds coordinates to the DataFrame.

        This method adds a 'Coordinates' column to the DataFrame with coordinates for each city.
        """
        self.df['Coordinates'] = get_coordinates_from_city_names(self.df['Ville'])

    def _calculate_average_prices(self):
        """
        Calculates average prices.

        This method calculates average prices per type of fuel, department, region, and city.
        It also prints the total sum of occurrences.
        """
        price_columns = ['Gazole_prix', 'SP95_prix', 'E85_prix', 'GPLc_prix', 'E10_prix', 'SP98_prix']
        self.df = self.df.groupby(['Région', 'Département', 'Ville'])[price_columns].mean().reset_index()

    def save_processed_dataframe(self):
        """
        Saves the processed DataFrame to a CSV file.

        The file is saved in a directory named 'visualizer' as 'processed_data.csv'.
        """
        target_dir = self.current_dir.parent / 'visualizer'
        try:
            if not target_dir.is_dir():
                messagebox.showerror("Error", "Directory 'visualizer' not found.")
                return

            file_path = target_dir / 'processed_data.csv'
            self.df.to_csv(file_path, index=False)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
