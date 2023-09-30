from tkinter import messagebox
from pathlib import Path
import pandas as pd


def open_csv_file(file_name):
    """
    Opens a CSV file located in the 'fetcher' directory.

    Args:
        file_name (str): The name of the CSV file to be opened.

    Returns:
        pandas.DataFrame or None: If successful, returns a DataFrame with the CSV data.
            If an error occurs, returns None and displays an error message.

    Examples:
        df = open_csv_file('data.csv')
    """
    # Get the absolute path of the current directory
    current_dir = Path(__file__).resolve().parent

    # Construct the path to the CSV file in the fetcher directory
    csv_path = current_dir.parent / 'fetcher' / file_name

    try:
        # Try to open the CSV file
        df = pd.read_csv(csv_path, sep=';')
        print("The file was opened successfully.")
        return df
    except FileNotFoundError:
        # Show an error window if the file was not found
        messagebox.showerror("Error", f"The file '{csv_path}' was not found.")
    except Exception as e:
        # Show an error window for all other exceptions
        messagebox.showerror("Error", f"An error occurred while opening the file: {e}")

    # Return None in case of an error
    return None


# traitement de la df
data = open_csv_file('64e02cff-9e53-4cb2-adfd-5fcc88b2dc09.csv')
data = data[['ville', 'prix_maj', 'prix_nom', 'prix_valeur',
             'reg_code', 'reg_name', 'dep_code',
             'dep_name', 'com_code', 'geom']].copy()
data = data.dropna()
# Convertir la colonne 'date_str' en format datetime
data['prix_maj'] = pd.to_datetime(data['prix_maj'], format='%Y-%m-%dT%H:%M:%S%z', utc=True)
# Extraire l'année
data['year'] = data['prix_maj'].dt.year

# Grouper par année et région, puis effectuer une opération sur les données (par exemple, moyenne des prix)
# Grouper par année et région
grouped_reg_data = data.groupby(['year', 'reg_name'])

# Grouper par année et par département
grouped_dep_data = data.groupby(['year', 'dep_name'])

# Récupérer les données pour l'année 2023
data_2023 = grouped_dep_data.get_group(('2023',))




