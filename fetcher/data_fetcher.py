import requests
import pandas as pd
from urllib.parse import urlparse

class DataFetcher:
    def __init__(self, url):
        self.url = url

    def fetch_data(self):
        """
        :return: Content from self.url
        """
        # Use HTTP requests to download a file from a URL while handling HTTP errors
        response = requests.get(self.url)
        response.raise_for_status()
        return response.content

    def convert_csv(self, fetched_data):
        """
        Convert a CSV into a DataFrame using pandas
        :param fetched_data: Content from self.url
        :return: DataFrame with content from the CSV file
        """
        # Define file_name as the ID of the DataSet
        file_name = urlparse(self.url).path.split("/")[-1] + ".csv"

        # Write the file_name.csv by opening the fetched_data content, then close it
        with open(file_name, 'wb') as file:
            file.write(fetched_data)

        # Create the DataFrame by separating with ';'
        df = pd.read_csv(file_name, delimiter=';')

        return df

url = "https://www.data.gouv.fr/fr/datasets/r/64e02cff-9e53-4cb2-adfd-5fcc88b2dc09"

# Create an instance of the DataFetcher class, specifying the URL of the file
fetcher = DataFetcher(url)

# Call the fetch_data method to download the data
data = fetcher.fetch_data()

# Then call the convert_csv method to save the data in CSV format
df = fetcher.convert_csv(data)
