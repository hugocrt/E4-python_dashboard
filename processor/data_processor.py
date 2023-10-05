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
            return pd.read_csv(csv_path, dtype={'Code postal': 'object'}, delimiter=';')
        except FileNotFoundError:
            messagebox.showerror("Error", f"The file '{csv_path}' was not found.")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while opening the file: {e}")
            return None

    def process_data(self):
        useful_columns = ['Région', 'Département', 'Code postal', 'Ville', 'Gazole_prix', 'SP95_prix',
                          'E85_prix', 'GPLc_prix', 'E10_prix', 'SP98_prix', 'geom']
        price_columns = ['Gazole_prix', 'SP98_prix', 'SP95_prix', 'E85_prix', 'E10_prix', 'GPLc_prix']

        self.df = self.df[useful_columns]
        self.df[price_columns] = self.df[price_columns].apply(pd.to_numeric, errors='coerce')
        self.df['Ville'] = self.df['Ville'].astype(str)
        self.df.insert(2, 'cp_ville', self.df[['Code postal', 'Ville']].apply(' '.join, axis=1))
        self.df.drop(columns=['Ville', 'Code postal'], inplace=True)
        self.df.dropna(subset=['Région'], inplace=True)
        self.df[price_columns] = self.df[price_columns].apply(pd.to_numeric, errors='coerce')

        # Convertir les coordonnées en listes de flottants
        self.df['geom'] = self.df['geom'].apply(lambda x: [float(coord) for coord in x.split(', ') if coord])

        # Ajouter la colonne 'Région' pour chaque cp_ville
        region_mapping = self.df.groupby('cp_ville')['Région'].first().reset_index()

        # Ajouter la colonne 'Département' pour chaque cp_ville
        departement_mapping = self.df.groupby('cp_ville')['Département'].first().reset_index()

        # Calculer les moyennes des prix
        df_means = self.df.groupby('cp_ville')[price_columns].mean().reset_index()

        # Calculer les moyennes des coordonnées géographiques
        def mean_coords(coords_list):
            latitudes = [coord[0] for coord in coords_list if coord]
            longitudes = [coord[1] for coord in coords_list if coord]
            return sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)

        coords_means = self.df.groupby('cp_ville')['geom'].apply(lambda x: mean_coords(x)).apply(pd.Series)
        lat = pd.Series(coords_means[0], name='Latitude')
        long = pd.Series(coords_means[1], name='longitude')

        df_means = pd.merge(df_means, lat, on='cp_ville')
        df_means = pd.merge(df_means, long, on='cp_ville')

        # Compter le nombre d'apparitions
        df_counts = self.df.groupby('cp_ville').size().reset_index(name='apparition')

        # Fusionner les résultats
        self.df = pd.merge(df_means, df_counts, on='cp_ville')
        self.df = pd.merge(departement_mapping, self.df, on='cp_ville', how='left')
        self.df = pd.merge(region_mapping, self.df, on='cp_ville', how='left')

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
