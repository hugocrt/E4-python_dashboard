from tkinter import messagebox
from pathlib import Path
import pandas as pd


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
        useful_columns = ['Région', 'Département', 'Code postal', 'Ville', 'Gazole_prix', 'SP95_prix',
                          'E85_prix', 'GPLc_prix', 'E10_prix', 'SP98_prix', 'geom']
        price_columns = ['Gazole_prix', 'SP95_prix', 'E85_prix', 'GPLc_prix', 'E10_prix', 'SP98_prix']

        self.df = self.df[useful_columns]
        self.df[price_columns] = self.df[price_columns].apply(pd.to_numeric, errors='coerce')
        self.df['Code postal'] = self.df['Code postal'].astype(str)
        self.df['Ville'] = self.df['Ville'].astype(str)
        self.df.insert(2, 'cp_ville', self.df[['Code postal', 'Ville']].apply(' '.join, axis=1))
        self.df.drop(columns=['Ville', 'Code postal'], inplace=True)
        # supprimer region nan

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
