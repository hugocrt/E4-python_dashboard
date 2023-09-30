import requests
import pandas as pd
from urllib.parse import urlparse


class DataFetcher:
    def __init__(self, url):
        """
        Initialize a DataFetcher object with a given URL.

        :param url: The URL to fetch data from.
        """
        self.url = url

    def fetch_data(self):
        """
        Fetch data from the specified URL.

        :return: Content from self.url
        """
        try:
            # Use HTTP requests to download data from the URL while handling HTTP errors
            response = requests.get(self.url)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch data: {e}")

    def convert_csv(self, fetched_data):
        """
        Convert a CSV into a DataFrame using pandas.

        :param fetched_data: Content from self.url
        :return: DataFrame with content from the CSV file
        """
        try:
            # Define file_name as the ID of the DataSet
            file_name = "Fuel_price_FR.csv"

            # Write the file_name.csv by opening the fetched_data content, then close it
            with open(file_name, 'wb') as file:
                file.write(fetched_data)

            # Create the DataFrame by separating with ';'
            df = pd.read_csv(file_name, delimiter=';')

            return df
        except Exception as e:
            raise Exception(f"Failed to convert CSV: {e}")


url = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-instantane-v2/exports/csv?lang=fr&timezone=Europe%2FParis&use_labels=true&delimiter=%3B"

# Create an instance of the DataFetcher class, specifying the URL of the file
fetcher = DataFetcher(url)

try:
    # Call the fetch_data method to download the data
    data = fetcher.fetch_data()

    # Then call the convert_csv method to save the data in CSV format and create a DataFrame
    df = fetcher.convert_csv(data)

    # Now you can work with the DataFrame 'df' as needed
    print("File created correctly")
except Exception as e:
    print(f"An error occurred: {e}")
