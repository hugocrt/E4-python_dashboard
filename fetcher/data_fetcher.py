import os

import requests
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By


def show_error_message(message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", message)
    root.destroy()


def get_data_from_xpath(url, xpath, content="href"):
    """
        Scrapes data from a webpage using Selenium.

        Args:
            url (str): The URL of the webpage to scrape.
            xpath (str): The XPath expression to locate the element on the webpage.
            content (str, optional): The type of content to retrieve ("href" or "text"). Default is "href".

        Returns:
            str: The scraped data based on the specified content type (.csv or date)

        Raises:
            Exception: If there's an error during scraping.
    """
    options = webdriver.FirefoxOptions()
    options.headless = True

    try:
        with webdriver.Firefox(options=options) as driver:
            driver.get(url)
            # Wait to load the whole page
            driver.implicitly_wait(5)

            # Get the element based on the provided XPATH
            element = driver.find_element(By.XPATH, xpath)

            if content == "href":
                data_from_url = element.get_attribute("href")
            elif content == "text":
                data_from_url = element.text
            else:
                raise ValueError("Invalid content type")

        return data_from_url

    except Exception as e:
        error_message = f"Failed to get data from the webpage: {e}"
        show_error_message(error_message)
        raise Exception(error_message)


class DataFetcher:
    """
    This class allows fetching data from a specified URL, saving it to a CSV file,
    importing it into a Pandas DataFrame, and obtaining the current date from a web page with the last date of
    modification.
    """

    def __init__(self,
                 base_url="https://data.economie.gouv.fr/explore/dataset/"
                          "prix-des-carburants-en-france-flux-instantane-v2/",
                 file_name="prix-des-carburants-en-france-flux-instantane-v2.csv"):
        """
                Initialize a DataFetcher object with a specified URL.

                Args:
                    base_url (str): The root URL from which data & date will be fetched.
                """
        self.download_url = base_url + "export/"
        self.date_url = base_url + "information/"
        self.file_name = file_name
        self.data = None
        self.date = None

    def get_csv_url(self):
        return get_data_from_xpath(self.download_url, "/html/body/div[1]/main/div/div[4]/div[3]/div[2]/div[7]/"
                                                      "div/div/div/div[1]/ul[1]/li[1]/div/a", content="href")

    def get_date(self):
        self.date = get_data_from_xpath(self.date_url, xpath="/html/body/div[1]/main/div/div[4]/div[3]/div[2]/div[1]/"
                                                             "div/div[2]/div/div[3]/div[6]/div[2]", content="text")

    def save_file_as_csv(self):
        try:
            csv_url = self.get_csv_url()
            file_name = self.file_name

            response = requests.get(csv_url)
            response.raise_for_status()

            local_path = os.path.join(os.getcwd(), file_name)

            with open(local_path, 'wb') as file:
                file.write(response.content)

            print(f"Le fichier CSV '{file_name}' a été téléchargé avec succès.")
        except requests.exceptions.RequestException as e:
            show_error_message(f"Erreur lors de la demande HTTP : {e}")
        except IOError as e:
            show_error_message(f"Erreur lors de l'écriture du fichier local : {e}")


def main():
    # Créez une instance de la classe DataFetcher avec l'URL de base appropriée
    data_fetcher = DataFetcher(base_url="https://data.economie.gouv.fr/explore/dataset/"
                                        "prix-des-carburants-en-france-flux-instantane-v2/")

    try:
        # Obtenez l'URL du fichier CSV
        csv_url = data_fetcher.get_csv_url()

        # Téléchargez et sauvegardez le fichier CSV localement
        data_fetcher.save_file_as_csv()

        # Obtenez la date de la page web
        data_fetcher.get_date()

        # Affichez les données et la date obtenues
        print("Données CSV téléchargées :", csv_url)
        print("Date de dernière modification :", data_fetcher.date)
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")


if __name__ == "__main__":
    main()
