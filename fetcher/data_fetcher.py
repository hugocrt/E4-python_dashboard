import requests
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By


def get_coordinates_from_city_names(list_cities):
    """
    Get coordinates (latitude and longitude) for a list of city names using OpenStreetMap Nominatim.

    Args:
        list_cities (list): List of city names.

    Returns:
        list: List of tuples containing latitude and longitude coordinates.
    """
    coordinates_list = []
    base_url = "https://nominatim.openstreetmap.org/search"

    for city in list_cities:
        params = {
            "q": city,
            "format": "json",
            "limit": 1
        }

        try:
            response = requests.get(base_url, params=params)
            data = response.json()

            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                coordinates_list.append((lat, lon))
            else:
                print(f"Unable to find coordinates for {city}.")
        except Exception as e:
            print(f"Error while querying {city}: {str(e)}")

    return coordinates_list


def show_error_message(message):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showerror("Error", message)
    root.destroy()


class DataFetcher:
    """
    This class allows fetching data from a specified URL, saving it to a CSV file,
    importing it into a Pandas DataFrame, and obtaining the current date from a web page.
    """

    def __init__(self, target_url):
        """
        Initialize a DataFetcher object with a specified URL.

        Args:
            target_url (str): The URL from which data will be fetched.
        """
        self.target_url = target_url

    def fetch_data(self):
        """
        Fetch data from the specified URL.

        Returns:
            tuple: A tuple containing the raw data and the 'content-disposition' header value.
        """
        try:
            response = requests.get(self.target_url)
            response.raise_for_status()
            content = response.content
            content_disposition = response.headers.get("content-disposition")
            return content, content_disposition
        except requests.exceptions.RequestException as e:
            show_error_message(f"Failed to fetch data: {e}")

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
            show_error_message(f"An error occurred: {e}")

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
            show_error_message(f"Failed to save data to file: {e}")

    def get_current_date(self):
        """
        Get the current date from a web page.

        Returns:
            str: The current date as text.
        """
        options = webdriver.FirefoxOptions()
        options.headless = True
        try:
            driver = webdriver.Firefox(options=options)
            driver.get("https://data.economie.gouv.fr/explore/dataset/prix-des-carburants-en-france-flux-instantane-v2"
                       "/information/")
            # Need to wait to be sure that the web page is fully opened
            driver.implicitly_wait(5)
            # Get through XPATH the "content" in the tag at the XPATH
            date_element = driver.find_element(by=By.XPATH, value="/html/body/div[1]/main/div/div[4]/div[3]/div[2]/"
                                                                  "div[1]/div/div[2]/div/div[3]/div[6]/div[2]/span")
            date_text = date_element.text
            driver.quit()
            return date_text
        except Exception as e:
            show_error_message(f"Failed to get the current date: {e}")


if __name__ == "__main__":
    browser = webdriver.Firefox()
    browser.get('https://data.economie.gouv.fr/explore/dataset/prix-des-carburants-en-france-flux-instantane-v2/'
                'export/')
    # Need to wait to be sure that the web page
    browser.implicitly_wait(5)
    # Get through XPATH the "href" from the tag at the XPATH
    url_data_gouv = browser.find_element(By.XPATH, '/html/body/div[1]/main/div/div[4]/div[3]/div[2]/div[7]/div/'
                                                   'div/div/div[1]/ul[1]/li[1]/div/a').get_attribute('href')
    browser.quit()

    fetcher = DataFetcher(url_data_gouv)
    result_tuple = fetcher.import_data()
    print(result_tuple)
