import os
import requests
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By


class DataFetcher:
    """
    This class allows fetching data from a specified URL, saving it to a CSV file,
    importing it into a Pandas DataFrame, and obtaining the current date from a web page with the last date of
    modification.
    """

    def __init__(self,
                 base_url="https://data.economie.gouv.fr/explore/dataset/prix-des-carburants-en-france-flux-instantane-v2/"):
        """
        Initialize a DataFetcher object with a specified URL.

        Args:
            base_url (str): The root URL from which data & date will be fetched.
        """
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window

        self.download_url = f"{base_url}export/"
        self.date_title_url = f"{base_url}information/"

        # XPaths for web scraping
        self.xpath_download = '/html/body/div[1]/main/div/div[4]/div[3]/div[2]/div[7]/div/div/div/div[1]/ul[1]/li[1]/div/a'
        self.xpath_date = '/html/body/div[1]/main/div/div[4]/div[3]/div[2]/div[1]/div/div[2]/div/div[3]/div[6]/div[2]'
        self.xpath_title = '/html/body/div[1]/main/div/div[4]/div[3]/div[2]/div[1]/div/div[2]/div/div[1]/div/div[2]/code'

        self.file_name = None
        self.csv_url = None
        self.date = None

    def get_url(self):
        """Get the URL of the CSV file."""
        return self.csv_url

    def get_date(self):
        """Get the date of the last modification."""
        return self.date

    def get_title(self):
        """Get the title of the file."""
        return self.file_name

    def show_message(self, title, message):
        """Show an information message box."""
        messagebox.showinfo(title, message)
        self.root.grab_set()  # Grab the main window to bring messagebox to the front

    def show_error_message(self, message):
        """Show an error message box."""
        messagebox.showerror("Error", message)
        self.root.grab_set()  # Grab the main window to bring messagebox to the front

    def get_data_from_xpath(self, content="href"):
        """
        Scrapes data from a webpage using Selenium.

        Args:
            content (str, optional): The type of content to retrieve ("href" or "text"). Default is "href".

        Returns:
            str: The scraped data based on the specified content type (.csv or (date, title))

        Raises:
            Exception: If there's an error during scraping.
        """
        options = webdriver.FirefoxOptions()
        options.headless = True

        try:
            with webdriver.Firefox(options=options) as driver:
                # To collect the CSV's url
                if content == "href":
                    self.show_message("Fetching .csv URL",
                                      "URL instantané pour une récupération inst... Mauvais script... [Appuyez sur ok "
                                      "si vous souhaitez lancer la récupération]")
                    driver.get(self.download_url)
                    driver.implicitly_wait(5)
                    element = driver.find_element(By.XPATH, self.xpath_download)
                    self.csv_url = element.get_attribute("href")
                # To collect the Date & Title of the URL
                elif content == "text":
                    self.show_message("Fetching Date and Title", "Votre date et titre sont en cours de prépara... "
                                                                 "Encore le mauvais script c'est pas possible... ["
                                                                 "Appuyez sur ok si vous souhaitez lancer la "
                                                                 "récupération]")
                    driver.get(self.date_title_url)
                    driver.implicitly_wait(5)
                    self.date = driver.find_element(By.XPATH, self.xpath_date).text
                    self.file_name = driver.find_element(By.XPATH, self.xpath_title).text
                # To collect both
                elif content == "all":
                    self.get_data_from_xpath("href")
                    self.get_data_from_xpath("text")
                else:
                    self.show_error_message("Invalid content type")
                    raise ValueError("Invalid content type")
        except Exception as e:
            error_message = f"Failed to get data from the webpage: {e}"
            self.show_error_message(error_message)
            raise Exception(error_message)

    def save_file_as_csv(self):
        """
        Save the CSV file from the URL to a local file.

        Raises:
            requests.exceptions.RequestException: If there's an HTTP request error.
            IOError: If there's an error while writing the local file.
        """
        try:
            self.show_message("CSV Download", "Souriez vous êtes téléchar... euh mauvais script ! Le téléchargement "
                                      "de votre CSV ne devrait pas prendre plus d'une minute ! [Appuyez sur ok si "
                                      "vous souhaitez lancer le téléchargement].")

            response = requests.get(self.get_url(), stream=True)
            response.raise_for_status()

            local_path = os.path.join(os.getcwd(), "fetcher", f"{self.get_title()}.csv")

            with open(local_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)

            self.show_message("CSV Download", "Votre .csv a correctement été téléchargé !")
        except requests.exceptions.RequestException as e:
            self.show_error_message(f"HTTP Request Error: {e}")
        except IOError as e:
            self.show_error_message(f"File Write Error: {e}")

    def fetch_data(self):
        """
        Fetch data by scraping web pages, download CSV, and show messages.

        Raises:
            Exception: If there's an error during any step of the process.
        """
        try:
            self.get_data_from_xpath("all")
            self.save_file_as_csv()

            self.show_message("CSV Download", f"CSV téléchargé à l'adresse : {self.get_url()}")
            self.show_message("Last Modification Date", f"Dernièr modification datant de : {self.get_date()}")
        except Exception as e:
            self.show_error_message(f"Error during processing: {e}")
