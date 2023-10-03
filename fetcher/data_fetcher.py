import requests
import pandas as pd
from datetime import datetime

class DataFetcher:
    def __init__(self, url):
        self.url = url

    def fetch_data(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            content = response.content
            content_disposition = response.headers.get("content-disposition")
            return content, content_disposition
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch data: {e}")

    def import_data(self):
        try:
            data, content_disposition = self.fetch_data()
            file_name = content_disposition.split("filename=")[-1].strip('"')
            df = self.convert_csv(data, file_name)

            # Obtenez la date actuelle au format de l'OS
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Créez un tuple contenant le DataFrame et la date
            result_tuple = (df, current_date)

            print("File created correctly")
            return result_tuple
        except Exception as e:
            print(f"An error occurred: {e}")

    def convert_csv(self, data, file_name):
        try:
            with open(file_name, 'wb') as file:
                file.write(data)

            df = pd.read_csv(file_name, delimiter=";")

            return df
        except Exception as e:
            raise Exception(f"Failed to convert CSV: {e}")

if __name__ == "__main__":
    fetcher = DataFetcher("https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-instantane-v2/exports/csv?lang=fr&timezone=Europe%2FParis&use_labels=true&delimiter=%3B")
    result_tuple = fetcher.import_data()

    print(result_tuple)

