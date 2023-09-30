import requests


class DataFetcher:
    def __init__(self, url):
        self.url = url

    def fetch_data(self):
        response = requests.get(self.url)
        response.raise_for_status()
        return response.content
