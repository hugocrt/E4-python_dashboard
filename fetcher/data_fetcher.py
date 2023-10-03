import requests
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

class DataFetcher:
    """
    This class allows fetching data from a specified URL, saving it to a CSV file,
    importing it into a Pandas DataFrame, and obtaining the current date from a web page.
    """

    def __init__(self, url):
        """
        Initialize a DataFetcher object with a specified URL.

        Args:
            url (str): The URL from which data will be fetched.
        """
        self.url = url

    def fetch_data(self):
        """
        Fetch data from the specified URL.

        Returns:
            tuple: A tuple containing the raw data and the 'content-disposition' header value.
        """
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            content = response.content
            content_disposition = response.headers.get("content-disposition")
            return content, content_disposition
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch data: {e}")

    def import_data(self):
        """
        Import data into a Pandas DataFrame from the specified URL.

        Returns:
            tuple: A tuple containing the Pandas DataFrame of data and the current date.
        """
        try:
            data, content_disposition = self.fetch_data()
            file_name = content_disposition.split("filename=")[-1].strip('"')
            self.save_data_to_file(data, file_name)
            df = pd.read_csv(file_name, delimiter=";")
            date_text = self.get_current_date()
            return df, date_text
        except Exception as e:
            print(f"An error occurred: {e}")

    def save_data_to_file(self, data, file_name):
        """
        Save raw data to a file.

        Args:
            data (bytes): The raw data to be saved.
            file_name (str): The name of the file where the data will be saved.
        """
        try:
            with open(file_name, 'wb') as file:
                file.write(data)
        except Exception as e:
            raise Exception(f"Failed to save data to file: {e}")

    def get_current_date(self):
        """
        Get the current date from a web page.

        Returns:
            str: The current date as text.
        """
        try:
            options = Options()
            options.headless = True
            browser = webdriver.Firefox()
            browser.get('https://data.economie.gouv.fr/explore/dataset/prix-des-carburants-en-france-flux-instantane-v2/information/')
            date_element = browser.find_element(by=By.XPATH,
                                                value="/html/body/div[1]/main/div/div[4]/div[2]/div[2]/div[1]/div/div[2]/div/div[3]/div[6]/div[2]")
            date_text = date_element.text
            browser.quit()
            return date_text
        except Exception as e:
            raise Exception(f"Failed to get current date: {e}")

if __name__ == "__main__":
    browser = webdriver.Firefox()
    browser.get('https://data.economie.gouv.fr/explore/dataset/prix-des-carburants-en-france-flux-instantane-v2/export/')
    url = browser.find_element(by=By.XPATH, value="/html/body/div[1]/main/div/div[4]/div[2]/div[2]/div[7]/div/div/div/div[1]/ul[1]/li[1]/div/a").get_attribute('href')
    browser.quit()
    fetcher = DataFetcher(url)
    result_tuple = fetcher.import_data()
    print(result_tuple)
